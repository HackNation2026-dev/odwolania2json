"""Tekst OCR dokumentów rozwojowych (rasteryzacja 150 dpi „jak skan” + rapidocr, CPU).

To zestaw własny grupy B (wejście dla E08 i E06 na tekście z OCR), niezależny od zestawu grupy A.
Skan = render strony pdfium + `jak_skan` z narzędzi eksperymentu przypadków brzegowych (ziarno stałe).
Wynik: cache/texts_ocr150.json (klucz dokument → strony z tekstem). Jeden proces, `nice`.
Użycie: python build_ocr_cache.py [--limit N]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import lib
from data import _syntetyczne, render_pages
from reading import RapidOcr
from reading import ocr_page_to_reading

OUT = lib.CACHE / "texts_ocr150.json"


def main() -> None:
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    syn = _syntetyczne()
    ocr = RapidOcr()
    res: dict = json.loads(OUT.read_text()) if OUT.is_file() else {}
    items = [i for i in lib.dev_items() if i.document_class in ("odwolanie", "pelnomocnictwo", "przelew")]
    if limit:
        items = items[:limit]
    t0 = time.time()
    for n, it in enumerate(items):
        if it.key in res:
            continue
        syn.LOS.seed(20261122 + n)
        imgs = [syn.jak_skan(im, szum=4) for im in render_pages(it.source, 150)]
        pages = []
        for pi, im in enumerate(imgs, 1):
            r = ocr.ocr_image(im, 150)
            rd = ocr_page_to_reading(pi, r, 150, 595.0, 842.0)
            pages.append({"number": pi, "text": rd["text"], "source": "ocr"})
        res[it.key] = {"class": it.document_class, "split": it.split, "pages": pages, "ocr": "rapidocr==3.10.0", "dpi": 150}
        OUT.write_text(json.dumps(res, ensure_ascii=False))
        print(n + 1, len(items), it.key, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
