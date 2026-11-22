"""E04a: diagnoza stron (tekst / skan / mieszana / niewidoczna warstwa): dokładność i koszt po obu stronach.

Polecenie: python E04/e04_diagnosis.py   (bez OCR; ok. 1 min)
Wariant v1 = `reading.diagnose_page` uprzęży; v2 = v1 + sygnał „niewidoczny tekst” (tryb renderowania 3) i pokrycie obrazem stron z tekstem.
Prawda strony: z konstrukcji wariantu (manifest) albo z ręcznej oceny materiałów organizatora (podane w wyniku).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as C

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import lib  # noqa: E402
from api import load_zestaw  # noqa: E402

import data  # noqa: E402
from reading import PdfiumReader, diagnose_page  # noqa: E402


def invisible_share(page: pdfium.PdfPage) -> tuple[int, float]:
    """(liczba obiektów tekstowych, udział w trybie renderowania 3 = niewidoczny)."""
    n = inv = 0
    for o in page.get_objects(filter=[C.FPDF_PAGEOBJ_TEXT], max_depth=3):
        n += 1
        if C.FPDFTextObj_GetTextRenderMode(o.raw) == 3:
            inv += 1
    return n, (inv / n if n else 0.0)


def diag_v2(page: dict, inv: tuple[int, float], base: dict) -> bool:
    """requires_ocr w v2: v1 lub (niewidoczny tekst ≥ 50% obiektów) lub (słowa, ale obraz ≥ 80% strony)."""
    if base["requires_ocr"]:
        return True
    return inv[1] >= 0.5


def pages_of(path: Path, truth, label: str, rd: PdfiumReader, out: list[dict]) -> None:
    d = rd.open(path.read_bytes())
    try:
        for i in range(rd.page_count(d)):
            pg = rd.read_page(d, i)
            base = diagnose_page(pg, ocr_available=True)
            inv = invisible_share(d[i])
            t = truth(i + 1) if callable(truth) else truth
            out.append({"set": label, "doc": str(path.name), "page": i + 1, "truth": t, "v1_requires_ocr": base["requires_ocr"],
                        "v1_text_source": base["text_source"], "v1_codes": base["codes"], "v2_requires_ocr": diag_v2(pg, inv, base),
                        "invisible_share": round(inv[1], 3), "words": len([w for w in pg["words"]]),
                        "image_cov": next(s["value"] for s in base["signals"] if s["code"] == "image_coverage")})
    finally:
        rd.close(d)


def main() -> int:
    rd = PdfiumReader()
    rows: list[dict] = []
    for it in data.load_items("cases-dev"):
        pages_of(it.source, "text", "oryginal-tekst", rd, rows)
    for it in load_zestaw():
        v = it.variant
        if v in ("skan", "obrot90", "obrot180", "obrot270", "skos3"):
            pages_of(it.pdf, "scan", v, rd, rows)
        elif v == "mieszany":
            pages_of(it.pdf, lambda p: "text" if p == 1 else "scan", v, rd, rows)
        elif v == "s2":
            pages_of(it.pdf, "mixed_image_data", v, rd, rows)
        elif v == "s5":
            pages_of(it.pdf, "scan_wrong_layer", v, rd, rows)
    # materiały organizatora: negatywy (tekst/skan wg pomiaru wcześniejszego), szablon (skan, 7 stron)
    neg_scans = {"1648041143_1647951357decyzja-ministrasportu-pzn.pdf", "Decyzja-Ministra-Sportu-i-Turystyki1.pdf",
                 "Minister-Sprawiedliwosci-pismo-RDSSP-z-11.03.2024-r..pdf"}
    for it in data.load_items("negatives"):
        pages_of(it.source, "scan" if it.input_name in neg_scans else "text", "negatywy-organizatora", rd, rows)
    pages_of(data.TEMPLATE_DIR / "przyklad odwolanie.pdf", "scan", "szablon-organizatora", rd, rows)
    pages_of(data.TEMPLATE_DIR / "negatywny przyklad.pdf", "text", "negatyw-szablonu", rd, rows)

    def summarize(ver: str) -> dict:
        res = {}
        by_set: dict[str, Counter] = {}
        for r in rows:
            req = r[f"{ver}_requires_ocr"]
            c = by_set.setdefault(r["set"], Counter())
            c["pages"] += 1
            c["ocr"] += req
            c["no_ocr"] += (not req)
        scanlike = [r for r in rows if r["truth"] != "text"]
        textlike = [r for r in rows if r["truth"] == "text"]
        missed = [r for r in scanlike if not r[f"{ver}_requires_ocr"]]
        wasted = [r for r in textlike if r[f"{ver}_requires_ocr"]]
        n = len(scanlike)
        res["scan_like_pages"] = n
        res["scan_like_sent_to_text_path(must_be_0)"] = len(missed)
        res["scan_like_missed_by_set"] = dict(Counter(r["set"] for r in missed))
        res["upper95_missed_rate_if_zero"] = round(3 / n, 4) if not missed else None
        res["text_pages"] = len(textlike)
        res["text_pages_sent_to_ocr(cost)"] = len(wasted)
        res["text_pages_wasted_by_set"] = dict(Counter(r["set"] for r in wasted))
        res["ocr_page_share_overall"] = round(sum(r[f"{ver}_requires_ocr"] for r in rows) / len(rows), 4)
        res["by_set"] = {k: dict(v) for k, v in by_set.items()}
        return res
    out = {"experiment": "E04a", "pages_total": len(rows), "truth_counts": dict(Counter(r["truth"] for r in rows)),
           "v1": summarize("v1"), "v2": summarize("v2"),
           "mixed_doc_saving": {"mieszany_pages": sum(1 for r in rows if r["set"] == "mieszany"),
                                "mieszany_text_pages_skipped_by_v1": sum(1 for r in rows if r["set"] == "mieszany" and r["truth"] == "text" and not r["v1_requires_ocr"])},
           "negatives_text_page_examples": [r for r in rows if r["set"] in ("negatywy-organizatora", "negatyw-szablonu") and r["v1_requires_ocr"]][:10],
           "versions": lib.versions()}
    lib.dump(HERE / "e04a-diagnoza.json", out)
    lib.dump(HERE / "e04a-strony.json", rows)
    import json
    print(json.dumps({k: out[k] for k in ("pages_total", "truth_counts", "v1", "v2")}, ensure_ascii=False, indent=1)[:3500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
