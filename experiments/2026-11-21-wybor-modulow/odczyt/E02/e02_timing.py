"""E02b: czas OCR (p50/p95, ≥5 powtórzeń, zimny i ciepły start), szczytowy RSS i dokładność na materiałach organizatora, dla 100/150/200/300 dpi.

Polecenie: python E02/e02_timing.py            (wynik: E02/e02b-czas.json; pomiar każdego dpi w osobnym podprocesie pod `flock /tmp/uzp-cpu.lock`)
Materiał: skan szablonu (7 stron, referencja: szablon-aplikacja/output) i 3 skany negatywne organizatora (strony ze skanem), zawsze oryginały (tylko odczyt).
Zimny start = nowy proces: import + wczytanie modeli + pierwsza strona; ciepły = kolejne strony po rozgrzewce (1 strona odrzucona).
RSS = ru_maxrss podprocesu (szczyt jednego procesu OCR). Wątki onnxruntime: jawnie intra_op = --threads, inter_op = 1.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import lib  # noqa: E402

import data  # noqa: E402

LOCK = "/tmp/uzp-cpu.lock"
REPS = 5
DPIS = (100, 150, 200, 300)
TEMPLATE_REF = data.MATERIALS / "szablon-aplikacja" / "output" / "case1" / "przyklad odwolanie.json"
NEG_SCANS = ["1648041143_1647951357decyzja-ministrasportu-pzn.pdf", "Decyzja-Ministra-Sportu-i-Turystyki1.pdf",
             "Minister-Sprawiedliwosci-pismo-RDSSP-z-11.03.2024-r..pdf"]


def pages() -> list[tuple[str, Path, int]]:
    out = [("szablon", data.TEMPLATE_DIR / "przyklad odwolanie.pdf", i) for i in range(7)]
    neg = {i.input_name: i.source for i in data.load_items("negatives")}
    import pypdfium2 as pdfium
    for n in NEG_SCANS:
        d = pdfium.PdfDocument(str(neg[n]))
        out += [(f"neg:{n[:12]}", neg[n], i) for i in range(len(d))]
    return out


def worker(dpi: int, threads: int, reps: int, max_side: int) -> dict:
    t_imp = time.perf_counter()
    import pypdfium2 as pdfium

    import ocr_lib
    o = ocr_lib.Ocr(threads=threads, max_side=max_side)
    t_load = time.perf_counter() - t_imp
    plist = pages()
    docs: dict = {}
    imgs = []
    for lab, path, i in plist:
        d = docs.setdefault(path, pdfium.PdfDocument(str(path)))
        imgs.append((lab, ocr_lib.render_a4(d, i, dpi)))
    # zimny start: pierwsza strona w nowym procesie (modele załadowane przy Ocr(), ale sesje ORT rozgrzewają się przy 1. wywołaniu)
    _, first = o.timed(imgs[0][1])
    warm, tmpl_text = [], {}
    per_page = {}
    for rep in range(reps):
        for k, (lab, im) in enumerate(imgs):
            r, t = o.timed(im)
            warm.append(t)
            per_page.setdefault(k, []).append(t)
            if rep == 0 and lab == "szablon":
                tmpl_text[k] = r["text"]
    ref = json.loads(TEMPLATE_REF.read_text(encoding="utf-8"))
    f = lib.findability(ref, "\n".join(tmpl_text[k] for k in sorted(tmpl_text)))
    return {"dpi_a4_normalized": dpi, "intra_op_threads": threads, "inter_op_threads": 1, "max_side_len": max_side, "pages": len(imgs), "repeats": reps,
            "px_first_page": list(imgs[0][1].size), "init_s_import_and_model_load": round(t_load, 2), "cold_first_page_s": round(first, 2),
            "warm_s": {"n": len(warm), "p50": lib.pctl(warm, .5), "p95": lib.pctl(warm, .95), "mean": round(sum(warm) / len(warm), 3), "max": round(max(warm), 3)},
            "per_page_median_s": {str(k): lib.pctl(v, .5) for k, v in per_page.items()},
            "template_findability": lib.totals(f["per_path"] and {p: b for p, b in f["per_path"].items()}), "template_missed": f["missed"],
            "peak_rss_mb": lib.peak_rss_mb(), "loadavg_end": os.getloadavg()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--reps", type=int, default=REPS)
    ap.add_argument("--max-side", type=int, default=2000)
    ap.add_argument("--dpi", type=int, action="append")
    ap.add_argument("--out", default="e02b-czas.json")
    ns = ap.parse_args()
    if ns.worker:
        print(json.dumps(worker(ns.worker, ns.threads, ns.reps, ns.max_side)))
        return 0
    runs = []
    for dpi in ns.dpi or DPIS:
        with open(LOCK, "w") as fh:
            t_wait = time.time()
            fcntl.flock(fh, fcntl.LOCK_EX)
            waited = round(time.time() - t_wait, 1)
            load0 = os.getloadavg()
            t0 = time.time()
            p = subprocess.run([sys.executable, str(Path(__file__)), "--worker", str(dpi), "--threads", str(ns.threads), "--reps", str(ns.reps),
                                "--max-side", str(ns.max_side)], capture_output=True, text=True, cwd=str(HERE))
            if p.returncode:
                runs.append({"dpi": dpi, "error": p.stderr[-500:]})
                continue
            r = json.loads(p.stdout.strip().splitlines()[-1])
            r.update({"lock_wait_s": waited, "loadavg_start": load0, "wall_s": round(time.time() - t0, 1), "flock": LOCK})
            runs.append(r)
            print(dpi, r["warm_s"], r["cold_first_page_s"], r["peak_rss_mb"], r["template_findability"], flush=True)
    lib.dump(HERE / ns.out, {"experiment": "E02b", "runs": runs, "versions": lib.versions(), "cpu_count": os.cpu_count(),
                              "note": "pomiar pod flock, ale maszyna współdzielona z innymi grupami (loadavg w wynikach): czasy to górne oszacowania"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
