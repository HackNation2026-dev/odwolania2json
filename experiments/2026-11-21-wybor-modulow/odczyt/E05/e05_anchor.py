"""E05: kotwiczenie cytatów do słów i bbox (warstwa tekstowa PDF, OCR skanów, obrót, obieg „wytnij bbox → OCR → porównaj z cytatem”).

Polecenie: python E05/e05_anchor.py            (wynik: E05/e05-wyniki.json; ok. 5–15 min zależnie od obciążenia maszyny)
Cytaty są syntetyczne (to NIE są odpowiedzi LLM): wartości referencyjne z dokumentów rozwojowych, ujęte jak cytuje człowiek/LLM
(dokładny przedział słów, inna wielkość liter, spacja nierozdzielająca, z kontekstem). Moduł testowany: `stages.WordAnchorResolver` uprzęży.
Zbiór: tylko sprawy rozwojowe (147 dokumentów); OCR: podzbiór 12 spraw × 3 dokumenty, ta sama próbka co E02.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from rapidfuzz.distance import Levenshtein

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "E01"))
sys.path.insert(0, str(HERE.parent / "E02"))
import lib  # noqa: E402
import ocr_lib  # noqa: E402
from api import load_zestaw  # noqa: E402
from e01_geometry import expect, iou, rotated_bytes  # noqa: E402
from e02_quality import ocr_doc, subset_cases  # noqa: E402

import data  # noqa: E402
import reading as R  # noqa: E402
from stages import WordAnchorResolver  # noqa: E402

SEED = 20261122
RESOLVER = WordAnchorResolver()
OCR_DPI = 150


def strip_p(t: str) -> str:
    return t.strip(".,;:()\"'")


def spans_for(words: list[dict], key: str, value) -> list[tuple[int, int]]:
    """Wszystkie (od, do) indeksy słów, w których występuje wartość (squash na znakach; kwota i data: słowo = forma)."""
    if key == "kwota":
        v = float(value)
        forms = {f"{v:.2f}".replace(".", ","), f"{v:.2f}"}
        return [(i, i) for i, w in enumerate(words) if strip_p(w["text"]) in forms]
    s = str(value)
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        y, m, d = s.split("-")
        forms = {f"{d}.{m}.{y}", f"{int(d)}.{m}.{y}"}
        return [(i, i) for i, w in enumerate(words) if strip_p(w["text"]) in forms]
    if key in lib.ID_FIELDS:
        needle = "".join(c for c in s if c.isdigit())
        sq = [("".join(c for c in w["text"] if c.isdigit())) for w in words]
    else:
        needle = lib.squash(s)
        sq = [lib.squash(w["text"]) for w in words]
    if len(needle) < 3:
        return []
    out = []
    n = len(words)
    for i in range(n):
        if not sq[i]:
            continue
        acc = ""
        for j in range(i, min(n, i + 14)):
            acc += sq[j]
            if needle in acc:
                if not (j > i and needle in acc[len(sq[i]):]):  # minimalny początek przedziału
                    out.append((i, j))
                break
            if len(acc) > len(needle) + 40:
                break
    return out


def quote_variants(span_words: list[dict], before: str, after: str) -> dict[str, str]:
    exact = " ".join(w["text"] for w in span_words)
    return {"exact": exact, "upper": exact.upper(), "nbsp": exact.replace(" ", " "), "context": f"{before} {exact} {after}".strip()}


def union(words: list[dict]) -> list[float]:
    return [min(w["bbox"][0] for w in words), min(w["bbox"][1] for w in words), max(w["bbox"][2] for w in words), max(w["bbox"][3] for w in words)]


def anchored_union(res: dict) -> list[float] | None:
    ev = res["evidence"]
    if not ev:
        return None
    bbs = [b for e in ev for b in e["bbox"]]
    return [min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs)]


def make_cases(reading_pages: list[dict], ref: dict) -> list[dict]:
    """Przypadki (pole, wartość, strona, indeksy słów, cytaty) dla wartości, które mają miejsce w słowach strony."""
    out = []
    for path, v in lib.leaves(ref):
        key = path.rsplit(".", 1)[-1]
        if v is None or isinstance(v, bool) or key in lib.SKIP_FIELDS:
            continue
        for p in reading_pages:
            ws = p["words"]
            sp = spans_for(ws, key, v)
            if sp:
                i, j = sp[0]
                before = ws[i - 1]["text"] if i else ""
                after = ws[j + 1]["text"] if j + 1 < len(ws) else ""
                out.append({"path": path, "key": key, "page": p["number"], "span": (i, j), "n_spans_on_page": len(sp), "words": ws[i:j + 1],
                            "quotes": quote_variants(ws[i:j + 1], before, after)})
                break
    return out


def evaluate(reading: dict, cases: list[dict], truth_fn, stats: dict, label: str) -> list[dict]:
    """Kotwiczy każdy cytat (z numerem strony i bez) i porównuje obrys z prawdą (`truth_fn(case) -> [bbox, ...]` możliwe prawdziwe obrysy)."""
    kept = []
    for c in cases:
        for qn, q in c["quotes"].items():
            for hint in (True, False):
                res = RESOLVER.resolve(reading, q, c["page"] if hint else None)
                k = f"{label}/{qn}/{'page' if hint else 'nopage'}"
                s = stats.setdefault(k, {"n": 0, "anchored": 0, "ambiguous": 0, "unanchored": 0, "correct": 0, "wrong": 0, "iou": []})
                s["n"] += 1
                s[res["status"]] += 1
                if res["status"] == "anchored":
                    bb = anchored_union(res)
                    best = max(iou(bb, t) for t in truth_fn(c))
                    s["iou"].append(best)
                    if best >= 0.5:
                        s["correct"] += 1
                    else:
                        s["wrong"] += 1
                    if qn == "exact" and hint:
                        kept.append({"case": c, "bbox": bb, "quote": q, "source": res["evidence"][0]["source"]})
    return kept


def fin(stats: dict) -> dict:
    out = {}
    for k, s in stats.items():
        n = s["n"]
        ious = s.pop("iou")
        s.update({"anchored_rate": round(s["anchored"] / n, 4), "ambiguous_rate": round(s["ambiguous"] / n, 4),
                  "unanchored_rate": round(s["unanchored"] / n, 4), "wrong_of_anchored": s["wrong"],
                  "iou_mean": round(float(np.mean(ious)), 4) if ious else None, "iou_min": round(float(min(ious)), 4) if ious else None})
        out[k] = s
    return out


def crop_ocr(ocr: ocr_lib.Ocr, img, bbox_px: list[float]) -> str:
    x0, y0, x1, y1 = bbox_px
    pad = 4
    w, h = img.size
    crop = img.crop((max(0, int(x0) - pad), max(0, int(y0) - pad), min(w, int(x1) + pad), min(h, int(y1) + pad)))
    if crop.size[0] < 4 or crop.size[1] < 4:
        return ""
    r = ocr.engine(np.asarray(crop.convert("RGB")), use_det=True, use_cls=False, use_rec=True)
    return " ".join(r.txts) if r.txts else ""


def roundtrip(ocr: ocr_lib.Ocr, docs: dict, anchored: list[dict], n: int, tag: str) -> dict:
    """Wytnij obrys z renderu, odczytaj OCR-em, porównaj z cytatem (CER po squash ≤ 0,2 = zgodne)."""
    rng = random.Random(SEED)
    sample = rng.sample(anchored, min(n, len(anchored)))
    ok, cers, bad = 0, [], []
    for a in sample:
        d, img, W, H = docs[a["doc"]][a["case"]["page"]]
        sx, sy = img.size[0] / W, img.size[1] / H
        x0, y0, x1, y1 = a["bbox"]
        txt = crop_ocr(ocr, img, [x0 * sx, y0 * sy, x1 * sx, y1 * sy])
        q, t = lib.squash(a["quote"]), lib.squash(txt)
        c = Levenshtein.distance(q, t) / max(1, len(q))
        cers.append(c)
        ok += c <= 0.2
        if c > 0.2 and len(bad) < 8:
            bad.append({"quote": a["quote"][:50], "ocr": txt[:60], "cer": round(c, 2)})
    return {"tag": tag, "tested": len(sample), "ok_cer_le_0.2": ok, "ok_rate": round(ok / max(1, len(sample)), 4),
            "cer_mean": round(float(np.mean(cers)), 4) if cers else None, "examples_bad": bad}


def main() -> int:
    t_start = time.time()
    rd = R.PdfiumReader()
    ocr = ocr_lib.Ocr(threads=3, max_side=2000)
    items = data.load_items("cases-dev")
    out: dict = {"experiment": "E05", "seed": SEED, "ocr_dpi_a4": OCR_DPI, "quote_kinds": ["exact", "upper", "nbsp", "context"]}

    # ---- A: warstwa tekstowa PDF (147 dokumentów) ----
    stats: dict = {}
    anchored_all: list[dict] = []
    docs_img: dict = {}
    n_cases = 0
    indep = {"checked": 0, "agree": 0, "disagree": []}
    for it in items:
        d = rd.open(it.source.read_bytes())
        pages = [rd.read_page(d, i) for i in range(rd.page_count(d))]
        reading = {"pages": pages}
        cases = make_cases(pages, data.reference_for(it))
        n_cases += len(cases)
        pdoc = pdfium.PdfDocument(str(it.source))

        def truth(c, pdoc=pdoc):
            return [union(c["words"])]
        kept = evaluate(reading, cases, truth, stats, "pdf")
        # niezależna weryfikacja: wyszukiwanie tekstu w pdfium (bez moich słów) dla cytatu exact, strony bez obrotu
        for a in kept[:6]:
            c = a["case"]
            tp = pdoc[c["page"] - 1].get_textpage()
            h = tp.search(a["quote"].replace(" ", " "), match_case=False).get_next()
            if h:
                rects = [tp.get_rect(k) for k in range(tp.count_rects(*h))]
                H = pages[c["page"] - 1]["height_pt"]
                bbs = [[l, H - t, r, H - b] for (l, b, r, t) in rects]
                u = [min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs)]
                indep["checked"] += 1
                v = iou(u, a["bbox"])
                if v >= 0.5:
                    indep["agree"] += 1
                elif len(indep["disagree"]) < 5:
                    indep["disagree"].append({"quote": a["quote"][:40], "iou": round(v, 3)})
        for a in kept:
            a["doc"] = it.key
        anchored_all.extend(kept)
        rd.close(d)
        pdoc.close()
    out["A_pdf_layer"] = {"documents": len(items), "cases": n_cases, "results": fin(stats), "independent_pdfium_search_check": indep}
    print("A done", round(time.time() - t_start), flush=True)

    # ---- B: OCR skanów (podzbiór 12 spraw) ----
    cases_sel = set(subset_cases())
    stats_o: dict = {}
    anchored_ocr: list[dict] = []
    docs_ocr: dict = {}
    n_cases_o = 0
    src = {i.key: i for i in items}
    scan_items = [i for i in load_zestaw(["skan"]) if i.case_id in cases_sel]
    for si in scan_items:
        s = src[f"{si.case_id}/{si.document_class}"] if f"{si.case_id}/{si.document_class}" in src else None
        if s is None:
            cand = [i for i in items if i.case_id == si.case_id and i.document_class == si.document_class]
            s = cand[0]
        d0 = rd.open(s.source.read_bytes())
        orig_pages = [rd.read_page(d0, i) for i in range(rd.page_count(d0))]
        ocr_pages = ocr_doc(ocr, si.pdf, OCR_DPI, f"e05-dpi{OCR_DPI}/{si.id.replace('/', '__')}")
        rpages = []
        for i, op in enumerate(ocr_pages):
            W, H = orig_pages[i]["width_pt"], orig_pages[i]["height_pt"]
            dpi_eff = op["px"][0] * 72.0 / W  # px skanu → pt strony oryginału (to samo przeliczenie, które robi harness)
            r = R.ocr_page_to_reading(i + 1, op, dpi_eff, W, H)
            rpages.append({"number": i + 1, "words": r["words"], "lines": r["lines"]})
        reading_ocr = {"pages": rpages}
        # cytaty wyprowadzone z tego, co OCR faktycznie odczytał (jak robiłby LLM czytający tekst OCR)
        cases = make_cases(rpages, si.reference())
        n_cases_o += len(cases)
        orig_ref_cases = {(c["path"], c["page"]): c for c in make_cases(orig_pages, si.reference())}

        def truth_o(c, orig_pages=orig_pages, si=si):
            key, v = c["key"], None
            spans = spans_for(orig_pages[c["page"] - 1]["words"], key, dict(lib.leaves(si.reference())).get(c["path"]))
            ws = orig_pages[c["page"] - 1]["words"]
            return [union(ws[i:j + 1]) for i, j in spans] or [[0, 0, 1, 1]]
        kept = evaluate(reading_ocr, cases, truth_o, stats_o, "ocr")
        for a in kept:
            a["doc"] = si.id
            docs_ocr.setdefault(si.id, {})
        # render skanu do obiegu
        sd = pdfium.PdfDocument(str(si.pdf))
        for k, pg in enumerate(rpages, 1):
            W, H = orig_pages[k - 1]["width_pt"], orig_pages[k - 1]["height_pt"]
            docs_ocr[si.id][k] = (sd, ocr_lib.render_a4(sd, k - 1, OCR_DPI), W, H)
        anchored_ocr.extend(kept)
        rd.close(d0)
    # pokrycie: ile wartości z referencji w ogóle nie dało cytatu (OCR nie odczytał)
    out["B_ocr_scans"] = {"documents": len(scan_items), "cases_with_value_in_ocr_words": n_cases_o, "results": fin(stats_o)}
    print("B done", round(time.time() - t_start), flush=True)

    # ---- C: obieg bbox → OCR → cytat ----
    docs_pdf: dict = {}
    for it in items[:0]:
        pass
    sample_docs = sorted({a["doc"] for a in anchored_all})
    rng = random.Random(SEED)
    pick = set(rng.sample(sample_docs, 15))
    sub = [a for a in anchored_all if a["doc"] in pick]
    for k in pick:
        d = pdfium.PdfDocument(str(src[k].source))
        docs_pdf[k] = {}
        for pi in range(len(d)):
            W, H = d[pi].get_size()
            docs_pdf[k][pi + 1] = (d, ocr_lib.render_a4(d, pi, 200), W, H)
    out["C_roundtrip_pdf"] = roundtrip(ocr, docs_pdf, sub, 200, "pdf-warstwa tekstowa → render 200 dpi → OCR obrysu")
    out["C_roundtrip_ocr_scans"] = roundtrip(ocr, docs_ocr, anchored_ocr, 200, "OCR skanu → render 150 dpi → OCR obrysu")
    print("C done", round(time.time() - t_start), flush=True)

    # ---- D: obrót /Rotate (narożniki po transformacji + zachowanie kotwiczenia) ----
    rot_stats = {}
    sel = sorted(random.Random(SEED + 1).sample([i for i in items], 12), key=lambda i: i.key)
    for rot in (90, 180, 270):
        tot = {"quotes": 0, "anchored": 0, "bbox_ok": 0, "iou": []}
        for it in sel:
            d0 = rd.open(it.source.read_bytes())
            d1 = rd.open(rotated_bytes(it.source, rot))
            p0 = [rd.read_page(d0, i) for i in range(rd.page_count(d0))]
            p1 = [rd.read_page(d1, i) for i in range(rd.page_count(d1))]
            for c in make_cases(p0, data.reference_for(it)):
                q = c["quotes"]["exact"]
                r0 = RESOLVER.resolve({"pages": p0}, q, c["page"])
                r1 = RESOLVER.resolve({"pages": p1}, q, c["page"])
                if r0["status"] != "anchored":
                    continue
                tot["quotes"] += 1
                if r1["status"] != "anchored":
                    continue
                tot["anchored"] += 1
                W, H = p0[c["page"] - 1]["width_pt"], p0[c["page"] - 1]["height_pt"]
                e = expect(anchored_union(r0), rot, W, H)
                v = iou(e, anchored_union(r1))
                tot["iou"].append(v)
                tot["bbox_ok"] += v >= 0.9
            rd.close(d0)
            rd.close(d1)
        a = tot.pop("iou")
        tot.update({"anchored_rate": round(tot["anchored"] / tot["quotes"], 4), "bbox_ok_rate": round(tot["bbox_ok"] / tot["quotes"], 4),
                    "iou_min": round(float(min(a)), 4), "iou_mean": round(float(np.mean(a)), 4)})
        rot_stats[str(rot)] = tot
    out["D_rotate"] = {"docs": [i.key for i in sel], "per_rotation": rot_stats,
                       "note": "obrót wymuszony przez set_rotation; prawda = narożniki obrysu z strony nieobróconej po transformacji CW"}
    out["wall_s"] = round(time.time() - t_start, 1)
    out["peak_rss_mb"] = lib.peak_rss_mb()
    out["versions"] = lib.versions()
    lib.dump(HERE / "e05-wyniki.json", out)
    print(json.dumps({k: out[k] for k in ("C_roundtrip_pdf", "C_roundtrip_ocr_scans", "D_rotate")}, ensure_ascii=False)[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
