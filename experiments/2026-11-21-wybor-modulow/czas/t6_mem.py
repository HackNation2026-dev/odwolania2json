"""T6: budżet pamięci: szczyt pamięci drzewa procesów dla najgorszego realnego dokumentu (11 stron, skan, 300 dpi) i dla 4 równoległych; zapas względem 16 GB.

Polecenie: ../../../.venv-exp/bin/python t6_mem.py [--reps 5]   → wyniki/T6.json (+ T6.units.jsonl)

Najgorszy realny dokument: odwołanie 11-stronicowe (maksimum w materiałach organizatora; dłuższe są tylko negatywy „obce”, do 35 stron, które i tak trafiają do
routera) jako skan z zestawu grupy A (profil „skan”, bez warstwy tekstu), render 300 dpi (skala 300/72 względem MediaBox), OCR rapidocr, `ocr_policy: always`.
Jednostka = świeży serwer w scope systemd (`MemoryMax=14G`, swap wyłączony) i dwa wsady: zimny, potem ciepły. Szczyt = cgroup memory.peak całej grupy procesów
(serwer + ewentualne dzieci) oraz VmHWM serwera. Konfiguracje: 1 dokument (współbieżność 1), 4 różne dokumenty 11-stronicowe równolegle (współbieżność 4) przy 300 dpi
oraz 4 równolegle przy 200 dpi (porównanie). Zapas = 16 GB − 4 GB (system i przeglądarka) − szczyt. Backend jest pojedynczym procesem wielowątkowym;
modele OCR są ładowane raz (jedna sesja onnxruntime współdzielona przez wątki).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "harness"))
sys.path.insert(0, str(HERE.parent / "odczyt" / "zestaw"))
import tlib  # noqa: E402
from srvunit import ServerUnit  # noqa: E402

BUDGET_MB = (16 - 4) * 1024
CONFIGS = [("dpi300_c1", 300, 1, 1), ("dpi300_c4", 300, 4, 4)]


def worst_docs(n: int) -> list[tuple[str, bytes, int]]:
    import data
    import pypdfium2 as pdfium
    from api import load_zestaw
    dev = [i for i in data.load_items("cases-dev") if i.document_class == "odwolanie"]
    sc = {(i.case_id, i.document_class): i for i in load_zestaw(["skan"])}
    out = []
    for i in sorted(dev, key=lambda i: i.key):
        z = sc[(i.case_id, "odwolanie")]
        d = pdfium.PdfDocument(str(z.pdf))
        pages = len(d)
        d.close()
        if pages == 11:
            out.append((i.key.replace("/", "__"), z.pdf.read_bytes(), pages))
        if len(out) == n:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--max-wait", type=float, default=3600)
    ns = ap.parse_args()
    docs = worst_docs(4)
    assert len(docs) == 4, "za mało 11-stronicowych skanów w zbiorze rozwojowym"
    gates = [tlib.wait_quiet(ns.max_wait, strict=True, label="T6 start")]
    units = []
    with (HERE / "wyniki" / "T6.units.jsonl").open("w") as fh:
        for rep, (name, dpi, w, ndocs) in tlib.block_shuffled(CONFIGS, ns.reps):
            files = [(n, b) for n, b, _ in docs[:ndocs]]
            for attempt in range(3):
                g = tlib.wait_quiet(ns.max_wait, strict=False, label=f"{name} rep{rep}")
                gates.append(g)
                cfg = {"name": f"t6-{name}", "router": "rules", "extractor": "rules", "ocr": "rapidocr", "ocr_dpi": dpi, "ocr_policy": "always",
                       "limits": {"max_workers": w, "document_timeout_s": 1800}}
                unit = f"t6-{name}-r{rep}-a{attempt}"
                with tlib.Monitor() as mon, ServerUnit(unit, cfg, Path(tempfile.gettempdir()) / unit) as srv:
                    idle = tlib.rss_hwm_mb(srv.pid)
                    cold = srv.run_batch(files)
                    warm = srv.run_batch(files)
                    pk = srv.peaks()
                rec = {"config": name, "dpi": dpi, "concurrency": w, "docs": ndocs, "pages_per_doc": 11, "rep": rep, "attempt": attempt, "gate": g, **mon.record(),
                       "rss_after_start_mb": idle, "peaks": pk, "cold_wall_s": cold["wall_s"], "warm_wall_s": warm["wall_s"],
                       "outcomes": [d["outcome"] for d in cold["docs"]], "ocr_pages_cold": sum((d["metrics"] or {}).get("ocr_pages", 0) for d in cold["docs"]),
                       "headroom_mb": round(BUDGET_MB - (pk["cgroup_memory_peak_mb"] or 0), 1)}
                rec["clean"] = rec["clean"] and g["quiet"]
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                units.append(rec)
                print(name, rep, rec["peaks"]["cgroup_memory_peak_mb"], rec["warm_wall_s"], "clean" if rec["clean"] else "NIECZYSTA", flush=True)
                if rec["clean"]:
                    break
    summ = {}
    for name, dpi, w, nd in CONFIGS:
        us = [u for u in units if u["config"] == name and u["clean"]]
        if not us:
            summ[name] = {"clean_units": 0, "note": "brak czystych jednostek: niewiążące"}
            continue
        summ[name] = {"dpi": dpi, "concurrency": w, "docs": nd, "clean_units": len(us), "cgroup_peak_mb": tlib.stats([u["peaks"]["cgroup_memory_peak_mb"] or 0 for u in us]),
                      "server_vmhwm_mb": tlib.stats([u["peaks"]["server_vmhwm_mb"] for u in us]), "rss_after_start_mb": tlib.stats([u["rss_after_start_mb"] for u in us]),
                      "cold_wall_s": tlib.stats([u["cold_wall_s"] for u in us]), "warm_wall_s": tlib.stats([u["warm_wall_s"] for u in us]),
                      "max_threads": max(u["peaks"]["sampled_max_threads"] for u in us), "headroom_mb_min": min(u["headroom_mb"] for u in us),
                      "outcomes": sorted({o for u in us for o in u["outcomes"]})}
    tlib.dump(HERE / "wyniki" / "T6.json", {"experiment": "T6", "budget_mb": BUDGET_MB, "docs": [d[0] for d in docs], "environment": tlib.environment(), "gates": gates,
              "total_wait_s": round(sum(g["waited_s"] for g in gates), 1), "summary": summ})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
