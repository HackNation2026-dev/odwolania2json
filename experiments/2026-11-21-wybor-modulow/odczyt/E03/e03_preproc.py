"""E03: czy preprocessing (wykrycie obrotu, deskew, binaryzacja) poprawia OCR i ile kosztuje.

Polecenie: python E03/e03_preproc.py [--threads 3]   (wynik E03/e03-wyniki.json)
Dane: odwołania 12 spraw (co 4.): wariant `skan` (profil z hasha), `obrot90/180/270`, `skos3`; pierwsza strona każdego.
Miara: odnajdywalność wartości referencyjnych, które występują w warstwie tekstu strony 1 oryginału (mianownik stały dla wszystkich metod).
Reguła decyzji ustalona przed pomiarem: krok jest przyjęty, gdy dolna granica 95% przedziału bootstrapu po sprawach różnicy odnajdywalności
(metoda − brak preprocessingu) na zbiorze, dla którego jest przeznaczony, jest > 0 i dodatkowy czas ≤ 1× czas OCR strony.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import lib  # noqa: E402
import ocr_lib  # noqa: E402
import preproc  # noqa: E402
from api import load_zestaw  # noqa: E402

import data  # noqa: E402

SEED = 20261122
DPI = 150
PAGES = 1
METHODS = ["none", "rot", "deskew", "rot+deskew", "rot+deskew+otsu", "otsu"]
SETS = ["skan", "obrot90", "obrot180", "obrot270", "skos3"]
TRUE_ROT = {"skan": 0, "skos3": 0, "obrot90": 90, "obrot180": 180, "obrot270": 270}


def boot_ci(per_case: list[float], n: int = 2000) -> tuple[float, float, float]:
    rng = random.Random(SEED)
    m = sum(per_case) / len(per_case)
    bs = sorted(sum(rng.choice(per_case) for _ in per_case) / len(per_case) for _ in range(n))
    return round(m, 4), round(bs[int(.025 * n)], 4), round(bs[int(.975 * n) - 1], 4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=3)
    ns = ap.parse_args()
    ocr = ocr_lib.Ocr(threads=ns.threads, max_side=2000)
    items = [i for i in load_zestaw(SETS) if i.document_class == "odwolanie"]
    src = {i.case_id: i for i in data.load_items("cases-dev") if i.document_class == "odwolanie"}
    out: dict = {"experiment": "E03", "dpi_a4": DPI, "pages_per_doc": PAGES, "threads": ns.threads, "seed": SEED, "methods": METHODS, "rows": [],
                 "rot_detect": {}, "skew_detect": {}}
    for it in items:
        s = src[it.case_id]
        ref_text = "\n".join(pdfium.PdfDocument(str(s.source))[i].get_textpage().get_text_range() for i in range(PAGES))
        ref = it.reference()
        # wartości występujące w warstwie tekstu strony 1 oryginału
        base = lib.findability(ref, ref_text)
        present = {p for p, b in base["per_path"].items() if b[0] + b[1] > 0}
        d = pdfium.PdfDocument(str(it.pdf))
        row = {"id": it.id, "set": it.variant, "case": it.case_id, "methods": {}}
        imgs = [ocr_lib.render_a4(d, i, DPI) for i in range(min(PAGES, len(d)))]
        # kroki wstępne mierzone raz na stronę
        rots, skews, t_rot, t_skew = [], [], 0.0, 0.0
        for im in imgs:
            k, info = preproc.detect_rotation(im, ocr)
            t_rot += info["seconds"]
            rots.append(k)
            imr = im.rotate(k, expand=True) if k else im
            t0 = time.perf_counter()
            skews.append(preproc.estimate_skew(imr))
            t_skew += time.perf_counter() - t0
        out["rot_detect"].setdefault(it.variant, []).extend([(k, TRUE_ROT[it.variant]) for k in rots])
        out["skew_detect"].setdefault(it.variant, []).extend(skews)
        for m in METHODS:
            texts, t_ocr, t_pre = [], 0.0, 0.0
            for im, k, a in zip(imgs, rots, skews, strict=True):
                x = im
                t0 = time.perf_counter()
                if "rot" in m.split("+")[0:1] or m.startswith("rot"):
                    x = x.rotate(k, expand=True) if k else x
                if "deskew" in m:
                    x = preproc.deskew(x, a)
                if "otsu" in m:
                    x = preproc.binarize_otsu(x)
                t_pre += time.perf_counter() - t0
                r, t = ocr.timed(x)
                t_ocr += t
                texts.append(r["text"])
            f = lib.findability(ref, "\n".join(texts))
            hit = sum((b[0] + b[1] > 0) for p, b in f["per_path"].items() if p in present)
            tot = len(present)
            # liczymy po liściach (nie po ścieżkach): odnajdywalność względem wartości obecnych w warstwie tekstu
            e = sum(b[0] + b[1] for p, b in f["per_path"].items() if p in present)
            n = sum(base["per_path"][p][2] for p in present)
            row["methods"][m] = {"found": e, "of": n, "rate": round(e / n, 4) if n else None, "ocr_s": round(t_ocr, 2), "pre_s": round(t_pre, 3)}
        row["rot_detect_s"], row["skew_detect_s"] = round(t_rot, 2), round(t_skew, 3)
        out["rows"].append(row)
        print(it.id, {m: v["rate"] for m, v in row["methods"].items()}, flush=True)
    # agregaty
    summ: dict = {}
    for st in SETS:
        rs = [r for r in out["rows"] if r["set"] == st]
        summ[st] = {}
        base_rates = [r["methods"]["none"]["rate"] for r in rs]
        for m in METHODS:
            rates = [r["methods"][m]["rate"] for r in rs]
            diffs = [a - b for a, b in zip(rates, base_rates, strict=True)]
            summ[st][m] = {"mean_rate": boot_ci(rates), "delta_vs_none": boot_ci(diffs) if m != "none" else None,
                           "ocr_s_per_page": round(sum(r["methods"][m]["ocr_s"] for r in rs) / (len(rs) * PAGES), 3),
                           "pre_s_per_page": round(sum(r["methods"][m]["pre_s"] for r in rs) / (len(rs) * PAGES), 4)}
    out["summary"] = summ
    rd = {}
    for st, pairs in out["rot_detect"].items():
        rd[st] = {"pages": len(pairs), "correct": sum(a == b for a, b in pairs),
                  "wrong": [(a, b) for a, b in pairs if a != b][:10]}
    out["rot_detect_summary"] = rd
    out["rot_detect_s_per_page"] = round(sum(r["rot_detect_s"] for r in out["rows"]) / (len(out["rows"]) * PAGES), 3)
    out["skew_detect_s_per_page"] = round(sum(r["skew_detect_s"] for r in out["rows"]) / (len(out["rows"]) * PAGES), 4)
    out["skew_summary"] = {st: {"mean": round(sum(v) / len(v), 2), "min": round(min(v), 2), "max": round(max(v), 2)} for st, v in out["skew_detect"].items()}
    out["versions"] = lib.versions()
    out["peak_rss_mb"] = lib.peak_rss_mb()
    lib.dump(HERE / "e03-wyniki.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
