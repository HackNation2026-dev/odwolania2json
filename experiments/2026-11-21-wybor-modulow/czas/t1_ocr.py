"""T1: OCR (rapidocr + onnxruntime CPU): s/stronę, szczytowy RSS, stron/min dla 1/2/4 workerów równolegle, punkt nasycenia.

Polecenie (jedno): ../../../.venv-exp/bin/python t1_ocr.py [--reps 5] [--quick]   → wyniki/T1.json (+ T1.units.jsonl, surowe jednostki)

Jednostka pomiaru = konfiguracja (dpi, workery W, wątki intra_op T) uruchomiona w NOWYCH procesach (zimny start każdego):
  worker: import + ładowanie modeli → render stron (poza pomiarem) → pierwsza strona OCR (zimna, osobno) → bariera (wszystkie
  workery startują razem) → N_WARM stron OCR po kolei (ciepłe, każda mierzona osobno) → raport (RSS: VmHWM, wątki).
  Przepustowość = (W × N_WARM) / (czas od bariery do końca ostatniego workera). Kolejność jednostek: bloki losowane (ziarno stałe).
Strony: pierwsze strony 3 skanów A4 z zestawu grupy A (odwołanie, pełnomocnictwo, przelew; profil „skan”; ta sama strona w każdej konfiguracji).
Render: „dpi znormalizowane do A4” (dłuższy bok = dpi × 11,69 cala), jak w E02; max_side_len = 2000 (wartość domyślna uprzęży/rapidocr),
dodatkowo wariant 300 dpi z limitem 4000 (1 worker) jako koszt braku limitu.
Cisza: twarda bramka przed skryptem; szybka między jednostkami; monitor obcych procesów w trakcie; jednostka nieczysta jest powtarzana (do 2×).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "odczyt"))
import tlib  # noqa: E402

N_WARM = 6
DPIS = (150, 200, 300)


def pick_pages() -> list[tuple[str, str, int]]:
    """Trzy strony A4 (odwołanie, pełnomocnictwo, przelew) z zestawu skanów: bierzemy pierwszą z każdej klasy wg kolejności manifestu."""
    sys.path.insert(0, str(HERE.parent / "odczyt" / "zestaw"))
    from api import load_zestaw
    items = load_zestaw(["skan"])
    out = []
    for cls in ("odwolanie", "pelnomocnictwo", "przelew"):
        it = sorted((i for i in items if i.document_class == cls), key=lambda i: i.entry["id"])[0]
        out.append((cls, str(it.pdf), 0))
    return out


def worker(idx: int, spec: dict, barrier, q) -> None:  # noqa: ANN001
    t_imp = time.perf_counter()
    import pypdfium2 as pdfium

    import ocr_lib
    o = ocr_lib.Ocr(threads=spec["threads"], max_side=spec["max_side"])
    t_load = time.perf_counter() - t_imp
    imgs = []
    for _cls, path, pg in spec["pages"]:
        d = pdfium.PdfDocument(path)
        imgs.append(ocr_lib.render_a4(d, pg, spec["dpi"]))
        d.close()
    t0 = time.perf_counter()
    o.run(imgs[(idx) % len(imgs)])
    cold = time.perf_counter() - t0
    barrier.wait()
    tb = time.perf_counter()
    cpu0 = time.process_time()
    lat = []
    for k in range(N_WARM):
        im = imgs[(idx + k) % len(imgs)]
        t = time.perf_counter()
        o.run(im)
        lat.append(time.perf_counter() - t)
    te = time.perf_counter()
    cpu_warm = time.process_time() - cpu0
    q.put({"cpu_warm_s": cpu_warm, "idx": idx, "t_load_s": t_load, "cold_first_page_s": cold, "warm_lat_s": lat, "t_barrier_wall": time.time(), "t_start_perf": tb, "t_end_perf": te,
           "rss_hwm_mb": tlib.rss_hwm_mb(), "threads_os_peak_end": tlib.thread_count(), "px": list(imgs[0].size)})


def run_unit(cfg: dict, pages: list) -> dict:
    spec = {"dpi": cfg["dpi"], "threads": cfg["threads"], "max_side": cfg["max_side"], "pages": pages}
    ctx = mp.get_context("spawn")
    W = cfg["workers"]
    barrier, q = ctx.Barrier(W), ctx.Queue()
    ps = [ctx.Process(target=worker, args=(i, spec, barrier, q)) for i in range(W)]
    t0 = time.perf_counter()
    for p in ps:
        p.start()
    res = [q.get(timeout=1800) for _ in ps]
    for p in ps:
        p.join()
    wall = time.perf_counter() - t0
    # czasy perf_counter z różnych procesów są porównywalne (CLOCK_MONOTONIC): okno = od najwcześniejszego startu do najpóźniejszego końca
    t_start = min(r["t_start_perf"] for r in res)
    t_end = max(r["t_end_perf"] for r in res)
    span = t_end - t_start
    lat = [x for r in res for x in r["warm_lat_s"]]
    return {"wall_s": round(wall, 2), "span_s": round(span, 3), "pages_per_min": round(W * N_WARM / span * 60, 2), "warm_lat_s": lat,
            "cold_first_page_s": [round(r["cold_first_page_s"], 3) for r in res], "t_load_s": [round(r["t_load_s"], 2) for r in res],
            "rss_hwm_mb_per_worker": [r["rss_hwm_mb"] for r in res], "rss_sum_mb": round(sum(r["rss_hwm_mb"] for r in res), 1), "cpu_s_per_page": round(sum(r["cpu_warm_s"] for r in res) / (W * N_WARM), 3), "px": res[0]["px"]}


def configs(quick: bool) -> list[dict]:
    """Zredukowana siatka (czas do 08:30): dpi 300 w1 × wątki 1/2/4/8, dpi 150 i 200 w1 t4, workery 2 i 4 (dpi 300), limit 4000."""
    cs = [dict(dpi=300, workers=1, threads=t, max_side=2000) for t in (1, 2, 4, 8)]
    cs += [dict(dpi=150, workers=1, threads=4, max_side=2000), dict(dpi=200, workers=1, threads=4, max_side=2000)]
    cs += [dict(dpi=300, workers=2, threads=2, max_side=2000), dict(dpi=300, workers=2, threads=4, max_side=2000), dict(dpi=300, workers=4, threads=1, max_side=2000),
           dict(dpi=300, workers=4, threads=2, max_side=2000)]
    cs.append(dict(dpi=300, workers=1, threads=4, max_side=4000))
    if quick:
        cs = [cs[0], cs[2], cs[6]]
    return cs


def key(c: dict) -> str:
    return f"dpi{c['dpi']}_w{c['workers']}_t{c['threads']}_cap{c['max_side']}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--aggregate-only", action="store_true", help="tylko agregacja z T1.units.jsonl (przerwany pomiar)")
    ap.add_argument("--out", default="T1.json")
    ap.add_argument("--quick", action="store_true", help="smoke test, nie pomiar")
    ap.add_argument("--max-wait", type=float, default=3600)
    ns = ap.parse_args()
    out = HERE / "wyniki" / ns.out
    units_path = out.with_suffix(".units.jsonl")
    pages = pick_pages()
    gate = tlib.wait_quiet(0 if ns.aggregate_only else ns.max_wait, strict=True, label="T1 start")
    plan = [] if ns.aggregate_only else tlib.block_shuffled(configs(ns.quick), ns.reps)
    done: list[dict] = []
    if units_path.exists() and not ns.quick:
        done = [json.loads(l) for l in units_path.read_text().splitlines()]
    have = {(u["rep"], u["key"]) for u in done if u["clean"]}
    waits = [gate]
    with units_path.open("a" if not ns.quick else "w") as fh:
        for rep, cfg in plan:
            k = key(cfg)
            if (rep, k) in have:
                continue
            for attempt in range(3):
                g = tlib.wait_quiet(ns.max_wait, strict=False, label=f"{k} rep{rep}")
                waits.append(g)
                with tlib.Monitor() as mon:
                    r = run_unit(cfg, pages)
                rec = {"rep": rep, "key": k, "cfg": cfg, "attempt": attempt, "gate": g, **mon.record(), "quiet_gate_ok": g["quiet"], **r}
                rec["clean"] = rec["clean"] and g["quiet"]
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                done.append(rec)
                print(k, rep, rec["pages_per_min"], "clean" if rec["clean"] else "NIECZYSTA", flush=True)
                if rec["clean"]:
                    break
    # agregacja
    agg = {}
    for k in sorted({u["key"] for u in done}):
        us = [u for u in done if u["key"] == k and u["clean"]]
        allu = [u for u in done if u["key"] == k]
        if not us:
            agg[k] = {"cfg": allu[0]["cfg"], "clean_units": 0, "note": "brak czystej jednostki: wynik niewiążący", "dirty_units": len(allu)}
            continue
        lat = [x for u in us for x in u["warm_lat_s"]]
        cold = [x for u in us for x in u["cold_first_page_s"]]
        load = [x for u in us for x in u["t_load_s"]]
        agg[k] = {"cfg": us[0]["cfg"], "clean_units": len(us), "dirty_units": len(allu) - len(us),
                  "warm_s_per_page": tlib.stats(lat), "cold_first_page_s": tlib.stats(cold), "init_import_model_s": tlib.stats(load),
                  "pages_per_min": tlib.stats([u["pages_per_min"] for u in us]),
                  "rss_peak_mb_per_worker": tlib.stats([x for u in us for x in u["rss_hwm_mb_per_worker"]]),
                  "rss_sum_mb": tlib.stats([u["rss_sum_mb"] for u in us]), "cpu_s_per_page": tlib.stats([u["cpu_s_per_page"] for u in us if "cpu_s_per_page" in u]), "px_first_page": us[0]["px"]}
    tlib.dump(out, {"experiment": "T1", "n_warm_per_worker": N_WARM, "pages": [{"class": c, "pdf": Path(p).name, "page": g} for c, p, g in pages],
                    "environment": tlib.environment(), "gates": waits, "summary": agg, "quick": ns.quick,
                    "total_wait_s": round(sum(w["waited_s"] for w in waits), 1)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
