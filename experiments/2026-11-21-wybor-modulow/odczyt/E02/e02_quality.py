"""E02a: dokładność OCR na skanach z zestawu (podzbiór 12 spraw × 3 dokumenty) w zależności od dpi i limitu boku.

Polecenie: python E02/e02_quality.py [--config dpi200_cap2000 ...]  (wynik: E02/e02a-<config>.json; cache OCR w cache/ poza Git)
Miary: odnajdywalność wartości referencyjnych w tekście OCR (exact/fuzzy) per profil i klasa; CER wobec warstwy tekstu na czystej rasteryzacji.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import pypdfium2 as pdfium
from rapidfuzz.distance import Levenshtein

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import lib  # noqa: E402
import ocr_lib  # noqa: E402
from api import load_zestaw  # noqa: E402

import data  # noqa: E402

SEED = 20261122
CONFIGS = {f"dpi{d}_cap{c}": (d, c) for d, c in [(100, 2000), (150, 2000), (200, 2000), (300, 2000), (200, 4000), (300, 4000)]}
CACHE = HERE.parent / "cache" / "ocr"


def subset_cases(n: int = 12) -> list[str]:
    cases = sorted({i.case_id for i in load_zestaw(["skan"])})
    return sorted(random.Random(SEED).sample(cases, n))


def ocr_doc(o: ocr_lib.Ocr, pdf: Path, dpi: int, cache_key: str | None = None):
    d = pdfium.PdfDocument(str(pdf))
    pages = []
    for i in range(len(d)):
        cp = CACHE / cache_key / f"p{i + 1}.json" if cache_key else None
        if cp and cp.exists():
            pages.append(json.loads(cp.read_text()))
            continue
        img = ocr_lib.render_a4(d, i, dpi)
        r, t = o.timed(img)
        r["seconds"], r["px"] = round(t, 3), list(img.size)
        if cp:
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(json.dumps(r))
        pages.append(r)
    return pages


def cer(a: str, ref: str) -> float:
    A, R = lib.squash(a), lib.squash(ref)
    return Levenshtein.distance(A, R) / max(1, len(R))


def run(name: str, threads: int) -> dict:
    dpi, cap = CONFIGS[name]
    o = ocr_lib.Ocr(threads=threads, max_side=cap)
    cases = set(subset_cases())
    items = [i for i in load_zestaw(["skan"]) if i.case_id in cases]
    per_doc, acc, by_prof, by_cls, secs, npages = [], {}, {}, {}, [], 0
    t0 = time.time()
    for it in items:
        pages = ocr_doc(o, it.pdf, dpi, f"{name}/{it.id.replace('/', '__')}")
        text = "\n".join(p["text"] for p in pages)
        f = lib.findability(it.reference(), text)
        lib.merge_find(acc, f)
        lib.merge_find(by_prof.setdefault(it.profile, {}), f)
        lib.merge_find(by_cls.setdefault(it.document_class, {}), f)
        secs += [p["seconds"] for p in pages if "seconds" in p]
        npages += len(pages)
        per_doc.append({"id": it.id, "profile": it.profile, "pages": len(pages), "missed": f["missed"]})
    # CER na czystej rasteryzacji dokumentów z warstwą tekstu (pierwsza strona odwołań i przelewów podzbioru)
    cers = []
    for it in data.load_items("cases-dev"):
        if it.case_id in cases and it.document_class in ("odwolanie", "przelew"):
            d = pdfium.PdfDocument(str(it.source))
            ref = d[0].get_textpage().get_text_range()
            img = ocr_lib.render_a4(d, 0, dpi)
            r = o.run(img)
            cers.append({"key": it.key, "cer": round(cer(r["text"], ref), 4), "chars": len(lib.squash(ref))})
    return {"experiment": "E02a", "config": name, "dpi_a4_normalized": dpi, "max_side_len": cap, "intra_op_threads": threads, "inter_op_threads": 1,
            "seed": SEED, "cases": sorted(cases), "documents": len(items), "pages": npages,
            "findability": lib.totals(acc), "by_profile": {k: lib.totals(v) for k, v in by_prof.items()},
            "by_class": {k: lib.totals(v) for k, v in by_cls.items()},
            "by_path": {p: {"exact": b[0], "fuzzy_only": b[1], "total": b[2]} for p, b in sorted(acc.items())},
            "sec_per_page_quality_run": {"p50": lib.pctl(secs, .5), "p95": lib.pctl(secs, .95), "mean": round(sum(secs) / len(secs), 3), "note": "bez flock, inne procesy równolegle: tylko orientacyjnie"} if secs else None,
            "cer_clean_raster": {"n": len(cers), "mean": round(sum(c["cer"] for c in cers) / len(cers), 4), "median": lib.pctl([c["cer"] for c in cers], .5),
                                 "weighted": round(sum(c["cer"] * c["chars"] for c in cers) / sum(c["chars"] for c in cers), 4)},
            "per_document_missed": [d for d in per_doc if d["missed"]], "peak_rss_mb": lib.peak_rss_mb(),
            "wall_s": round(time.time() - t0, 1), "versions": lib.versions()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", action="append")
    ap.add_argument("--threads", type=int, default=3)
    ns = ap.parse_args()
    for name in ns.config or list(CONFIGS):
        r = run(name, ns.threads)
        lib.dump(HERE / f"e02a-{name}.json", r)
        print(name, r["findability"], r["cer_clean_raster"], r["wall_s"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
