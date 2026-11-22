"""T3: backend HTTP end-to-end BEZ LLM, 60 dokumentów, współbieżność 1/2/4: czas całkowity, dokumenty/min, szczyt pamięci grupy procesów, narzut serwera.

Polecenie: ../../../.venv-exp/bin/python t3_http.py [--reps 5] [--only text|scan]   → wyniki/T3.json (+ T3.units.jsonl)

Konfiguracja serwera: `router: rules`, `extractor: rules` (zerowy koszt etapu LLM: to, co robiłby mock o zerowym opóźnieniu; żadne wywołanie sieciowe
nie następuje), PDFium + (dla skanów) rapidocr 200 dpi `if_needed`, `limits.max_workers` = współbieżność. Serwer to ten sam `harness/server.py` co w grupach A-D.
Zbiory (po 60, 20 odwołań + 20 pełnomocnictw + 20 przelewów, pierwsze wg klucza; wyłącznie sprawy rozwojowe):
  text — oryginalne PDF-y z warstwą tekstu; scan — te same sprawy jako skany z zestawu grupy A (profil „skan”, bez warstwy tekstu).
Jednostka = świeży serwer w scope systemd (`MemoryMax=14G`, swap wyłączony): zimny wsad (start procesu, ładowanie modelu OCR) i zaraz potem ciepły wsad
(te same 60 plików ponownie). Szczyt pamięci = cgroup memory.peak całej grupy procesów po obu wsadach. Narzut serwera = czas ścienny wsadu minus
(Σ czasów etapów dokumentów / współbieżność): to, co nie jest odczytem, OCR, routerem ani ekstraktorem (kolejka, upload, zapis artefaktów, JSON, blokada PDFium).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "harness"))
sys.path.insert(0, str(HERE.parent / "odczyt" / "zestaw"))
import tlib  # noqa: E402
from srvunit import ServerUnit  # noqa: E402

CONCURRENCY = (1, 2, 4)
SCRATCH = Path(tempfile.gettempdir())


def doc_sets() -> dict[str, list[tuple[str, bytes]]]:
    import data
    from api import load_zestaw
    dev = [i for i in data.load_items("cases-dev")]
    pick = {}
    for cls in ("odwolanie", "pelnomocnictwo", "przelew"):
        pick[cls] = sorted((i for i in dev if i.document_class == cls), key=lambda i: i.key)[:20]
    text = [(i.key.replace("/", "__"), i.source.read_bytes()) for cls in pick for i in pick[cls]]
    sc = {(i.case_id, i.document_class): i for i in load_zestaw(["skan"])}
    scan = []
    for cls in pick:
        for i in pick[cls]:
            z = sc[(i.case_id, cls)]
            scan.append((i.key.replace("/", "__"), z.pdf.read_bytes()))
    return {"text": text, "scan": scan}


def stage_sums(docs: list[dict]) -> dict:
    ks = ("pdf_read_s", "ocr_s", "route_s", "extract_s", "wall_s", "ocr_pages", "pages")
    return {k: round(sum((d["metrics"] or {}).get(k, 0) for d in docs), 3) for k in ks}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--only")
    ap.add_argument("--max-wait", type=float, default=3600)
    ap.add_argument("--out", default="T3")
    ns = ap.parse_args()
    sets = doc_sets()
    if ns.only:
        sets = {ns.only: sets[ns.only]}
    cfgs = [(k, c) for k in sets for c in CONCURRENCY]
    gate0 = tlib.wait_quiet(ns.max_wait, strict=True, label="T3 start")
    units, gates = [], [gate0]
    up = HERE / "wyniki" / f"{ns.out}.units.jsonl"
    with up.open("w") as fh:
        for rep, (kind, w) in tlib.block_shuffled(cfgs, ns.reps):
            for attempt in range(3):
                g = tlib.wait_quiet(ns.max_wait, strict=False, label=f"{kind} c{w} rep{rep}")
                gates.append(g)
                cfg = {"name": f"t3-{kind}-c{w}", "router": "rules", "extractor": "rules", "ocr": "rapidocr" if kind == "scan" else "none",
                       "ocr_dpi": 200, "ocr_policy": "if_needed", "limits": {"max_workers": w, "document_timeout_s": 900}}
                unit = f"t3-{kind}-c{w}-r{rep}-a{attempt}"
                work = SCRATCH / unit
                with tlib.Monitor() as mon:
                    with ServerUnit(unit, cfg, work) as srv:
                        cold = srv.run_batch(sets[kind])
                        warm = srv.run_batch(sets[kind])
                        pk = srv.peaks()
                rec = {"kind": kind, "concurrency": w, "rep": rep, "attempt": attempt, "gate": g, **mon.record(), "peaks": pk,
                       "cold": {k: v for k, v in cold.items() if k != "docs"} | {"stages": stage_sums(cold["docs"]), "outcomes": _count(cold["docs"], "outcome")},
                       "warm": {k: v for k, v in warm.items() if k != "docs"} | {"stages": stage_sums(warm["docs"]), "outcomes": _count(warm["docs"], "outcome")},
                       "warm_doc_wall_s": [d["metrics"]["wall_s"] for d in warm["docs"] if d["metrics"]]}
                rec["clean"] = rec["clean"] and g["quiet"]
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                units.append(rec)
                print(kind, w, rep, rec["warm"]["wall_s"], rec["peaks"]["cgroup_memory_peak_mb"], "clean" if rec["clean"] else "NIECZYSTA", flush=True)
                if rec["clean"]:
                    break
    summ = {}
    for kind, w in cfgs:
        us = [u for u in units if u["kind"] == kind and u["concurrency"] == w and u["clean"]]
        if not us:
            summ[f"{kind}_c{w}"] = {"clean_units": 0, "note": "brak czystych jednostek: niewiążące"}
            continue
        s = {"clean_units": len(us), "dirty_units": sum(1 for u in units if u["kind"] == kind and u["concurrency"] == w and not u["clean"])}
        for ph in ("cold", "warm"):
            walls = [u[ph]["wall_s"] for u in us]
            ov = []
            for u in us:
                st = u[ph]["stages"]
                busy = st["pdf_read_s"] + st["ocr_s"] + st["route_s"] + st["extract_s"]
                ov.append(u[ph]["wall_s"] - st["wall_s"] / w)
            s[ph] = {"wall_s": tlib.stats(walls), "docs_per_min": tlib.stats([u[ph]["docs_per_min"] for u in us]),
                     "server_cpu_s": tlib.stats([u[ph]["server_cpu_s"] for u in us]), "cpu_utilization": tlib.stats([u[ph]["cpu_utilization"] for u in us]),
                     "overhead_s_wall_minus_sum_doc_wall_over_c": tlib.stats(ov), "stage_sums_mean": {k: round(sum(u[ph]["stages"][k] for u in us) / len(us), 2) for k in us[0][ph]["stages"]},
                     "outcomes": us[0][ph]["outcomes"]}
        s["cgroup_peak_mb"] = tlib.stats([u["peaks"]["cgroup_memory_peak_mb"] or 0 for u in us])
        s["server_vmhwm_mb"] = tlib.stats([u["peaks"]["server_vmhwm_mb"] for u in us])
        s["max_threads"] = max(u["peaks"]["sampled_max_threads"] for u in us)
        s["server_start_s"] = tlib.stats([u["peaks"]["start_s"] for u in us])
        s["warm_doc_wall_s_per_doc"] = tlib.stats([x for u in us for x in u["warm_doc_wall_s"]])
        summ[f"{kind}_c{w}"] = s
    tlib.dump(HERE / "wyniki" / f"{ns.out}.json", {"experiment": "T3", "docs_per_set": {k: len(v) for k, v in sets.items()}, "environment": tlib.environment(),
              "gates": gates, "total_wait_s": round(sum(g["waited_s"] for g in gates), 1), "summary": summ,
              "ocr_threads_note": "serwer tworzy RapidOCR() bez jawnej liczby wątków (domyślnie onnxruntime: -1, o liczbie decyduje ORT); zobacz max_threads"})
    return 0


def _count(docs: list[dict], key: str) -> dict:
    out: dict = {}
    for d in docs:
        out[str(d.get(key))] = out.get(str(d.get(key)), 0) + 1
    return out


if __name__ == "__main__":
    raise SystemExit(main())
