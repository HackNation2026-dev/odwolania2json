"""E01a: czytniki warstwy tekstowej PDF: odnajdywalność wartości referencyjnych, czas (p50/p95, ≥5 powtórzeń), RSS.

Jedno polecenie: python E01/e01_readers.py   (całość pod flock /tmp/uzp-cpu.lock dla czasów; czytniki liczone w osobnych procesach).
Tryb wewnętrzny: --reader NAZWA --reps N (proces potomny: zimny start = pierwszy odczyt po imporcie).
"""
from __future__ import annotations

import argparse
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "vendor"))  # pdfminer.six, pymupdf (izolowane, poza .venv-exp)
import lib  # noqa: E402

import data  # noqa: E402


def text_pdfium(path: Path) -> str:
    from reading import PdfiumReader
    r = PdfiumReader()
    d = r.open(path.read_bytes())
    try:
        return "\n".join(r.read_page(d, i)["text"] for i in range(r.page_count(d)))
    finally:
        r.close(d)


def text_pypdf(path: Path) -> str:
    import pypdf
    return "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(str(path)).pages)


def text_pdfminer(path: Path) -> str:
    from pdfminer.high_level import extract_text
    return extract_text(str(path))


def text_pymupdf(path: Path) -> str:
    import fitz
    with fitz.open(str(path)) as d:
        return "\n".join(p.get_text() for p in d)


READERS = {"pdfium": text_pdfium, "pypdf": text_pypdf, "pdfminer": text_pdfminer, "pymupdf": text_pymupdf}
LICENSE = {"pdfium": "BSD-3/Apache-2.0 (pypdfium2)", "pypdf": "BSD-3", "pdfminer": "MIT (pdfminer.six)", "pymupdf": "AGPL-3.0 lub komercyjna (PyMuPDF)"}


def docs(which: str):
    items = data.load_items("cases-dev")
    if which == "text":
        return [(i.key, i.source, i) for i in items]
    raise ValueError(which)


def child(reader: str, reps: int) -> dict:
    fn = READERS[reader]
    items = docs("text")
    t_imp = time.perf_counter()
    fn(items[0][1])  # rozgrzewka i import (zimny start liczony osobno)
    cold = time.perf_counter() - t_imp
    per_doc: dict[str, list[float]] = {}
    texts: dict[str, str] = {}
    for rep in range(reps):
        for key, p, _ in items:
            t0 = time.perf_counter()
            tx = fn(p)
            per_doc.setdefault(key, []).append(time.perf_counter() - t0)
            texts[key] = tx
    acc: dict[str, list[int]] = {}
    by_class: dict[str, dict[str, list[int]]] = {}
    missed = {}
    for key, p, it in items:
        f = lib.findability(data.reference_for(it), texts[key])
        lib.merge_find(acc, f)
        lib.merge_find(by_class.setdefault(it.document_class, {}), f)
        if f["missed"]:
            missed[key] = f["missed"]
    med = [lib.pctl(v, 0.5) for v in per_doc.values()]
    allt = [x for v in per_doc.values() for x in v]
    return {"reader": reader, "license": LICENSE[reader], "documents": len(items), "reps": reps,
            "cold_first_doc_s": round(cold, 4), "doc_time_s": {"p50": lib.pctl(allt, 0.5), "p95": lib.pctl(allt, 0.95), "max": round(max(allt), 4),
                                                              "median_of_doc_medians": lib.pctl(med, 0.5), "total_per_pass": round(sum(med), 3)},
            "peak_rss_mb": lib.peak_rss_mb(), "findability": lib.totals(acc),
            "findability_by_class": {k: lib.totals(v) for k, v in by_class.items()},
            "findability_by_path": {p: {"exact": b[0], "fuzzy_only": b[1], "total": b[2]} for p, b in sorted(acc.items())},
            "missed_examples": dict(list(missed.items())[:25]), "n_docs_with_miss": len(missed), "versions": lib.versions()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader")
    ap.add_argument("--reps", type=int, default=5)
    ns = ap.parse_args()
    if ns.reader:
        print(json.dumps(child(ns.reader, ns.reps)))
        return 0
    out = {"experiment": "E01a", "threads": "n/d (czytniki jednowątkowe)", "results": {}}
    with open("/tmp/uzp-cpu.lock", "a+") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        for r in READERS:
            cp = subprocess.run([sys.executable, __file__, "--reader", r, "--reps", str(ns.reps)], capture_output=True, text=True)
            if cp.returncode:
                out["results"][r] = {"error": cp.stderr[-600:]}
                continue
            out["results"][r] = json.loads(cp.stdout.strip().splitlines()[-1])
            x = out["results"][r]
            print(r, x["findability"], x["doc_time_s"], x["peak_rss_mb"], flush=True)
    out["timing_locked"] = True
    lib.dump(HERE / "e01a-czytniki.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
