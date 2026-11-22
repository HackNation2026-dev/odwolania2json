"""E01b: geometria: narożniki po /Rotate, test obiegowy bbox (ślad tuszu), kolejność czytania na dwóch układach przelewów.

Polecenie: python E01/e01_geometry.py
"""
from __future__ import annotations

import io
import random
import re
import sys
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import lib  # noqa: E402

import data  # noqa: E402
from reading import PdfiumReader  # noqa: E402

SEED = 20261122


def rotated_bytes(src: Path, rot: int) -> bytes:
    d = pdfium.PdfDocument(str(src))
    for i in range(len(d)):
        d[i].set_rotation(rot)
    b = io.BytesIO()
    d.save(b)
    return b.getvalue()


def expect(bb, rot, W, H):
    x0, y0, x1, y1 = bb
    pts = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    f = {0: lambda x, y: (x, y), 90: lambda x, y: (H - y, x), 180: lambda x, y: (W - x, H - y), 270: lambda x, y: (y, W - x)}[rot]
    q = [f(*p) for p in pts]
    return [min(p[0] for p in q), min(p[1] for p in q), max(p[0] for p in q), max(p[1] for p in q)]


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u else 0.0


def ink_roundtrip(img: np.ndarray, bb, scale: float) -> tuple[float, float]:
    """(ułamek ciemnych pikseli w bbox, udział tuszu z paska wokół bbox leżący w bbox)."""
    h, w = img.shape
    x0, y0, x1, y1 = (int(round(v * scale)) for v in bb)
    pad = max(2, int(min(y1 - y0, x1 - x0) * 0.35))  # po krótszym boku: słowa pionowe po obrocie
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
    dark = img < 140
    inside = dark[max(0, y0):y1, max(0, x0):x1]
    region = dark[Y0:Y1, X0:X1]
    tot = region.sum()
    return (float(inside.mean()) if inside.size else 0.0, float(inside.sum() / tot) if tot else 0.0)


def rotate_test(n_docs: int = 12) -> dict:
    rd = PdfiumReader()
    items = sorted(data.load_items("cases-dev"), key=lambda i: i.key)
    sel = random.Random(SEED).sample(items, n_docs)
    out = {"docs": [i.key for i in sel], "rotations": {}}
    for rot in (0, 90, 180, 270):
        ious, words, ink_ok, ink_n, bad_dims, unmatched = [], 0, 0, 0, 0, 0
        for it in sel:
            d0 = rd.open(it.source.read_bytes())
            d1 = rd.open(rotated_bytes(it.source, rot))
            for pi in range(min(2, rd.page_count(d0))):
                p0, p1 = rd.read_page(d0, pi), rd.read_page(d1, pi)
                W, H = p0["width_pt"], p0["height_pt"]
                exp_dims = (W, H) if rot in (0, 180) else (H, W)
                if abs(p1["width_pt"] - exp_dims[0]) > 0.1 or abs(p1["height_pt"] - exp_dims[1]) > 0.1:
                    bad_dims += 1
                by_text: dict = {}
                for w1 in p1["words"]:
                    by_text.setdefault(w1["text"], []).append(w1)
                for w in p0["words"]:
                    cands = by_text.get(w["text"])
                    if not cands:
                        unmatched += 1  # słowo inaczej podzielone po obrocie (kolejność znaków pdfium): pomijamy, liczymy jawnie
                        continue
                    e = expect(w["bbox"], rot, W, H)
                    words += 1
                    ious.append(max(iou(e, c["bbox"]) for c in cands))
                scale = 2.0
                img = np.asarray(d1[pi].render(scale=scale).to_pil().convert("L"))
                for w in random.Random(SEED + pi).sample(p1["words"], min(60, len(p1["words"]))):
                    fr, share = ink_roundtrip(img, w["bbox"], scale)
                    ink_n += 1
                    ink_ok += (fr >= 0.03 and share >= 0.7)
            rd.close(d0); rd.close(d1)
        a = np.array(ious)
        out["rotations"][rot] = {"words_compared": words, "words_unmatched_by_text": unmatched, "iou_min": round(float(a.min()), 4), "iou_mean": round(float(a.mean()), 4),
                                 "share_iou_ge_0.95": round(float((a >= 0.95).mean()), 4), "page_dim_mismatch": bad_dims,
                                 "ink_roundtrip_tested": ink_n, "ink_roundtrip_ok": ink_ok, "ink_roundtrip_rate": round(ink_ok / ink_n, 4)}
    return out


LABELS = {"z": re.compile(r"obci[aą]|nadawc|p[lł]atnik|z rachunku|zleceniodawc", re.I),
          "na": re.compile(r"odbior|adresat|beneficjent|na rachunek|odbiorc", re.I)}


def label_class_before(text: str, digits: str) -> str | None:
    t = re.sub(r"[  ]", "", text)
    m = None
    for mm in re.finditer(re.escape(digits), t):
        m = mm
        break
    if not m:
        return None
    # indeks w tekście oryginalnym: odwzoruj pozycję przez zliczanie znaków niebędących spacjami
    cnt, pos = 0, 0
    for i, ch in enumerate(text):
        if ch not in "  ":
            if cnt == m.start():
                pos = i
                break
            cnt += 1
    before = text[:pos]
    best, bi = None, -1
    for cls, rx in LABELS.items():
        for mm in rx.finditer(before):
            if mm.start() > bi:
                best, bi = cls, mm.start()
    return best


def layout_of(path: Path) -> str:
    rd = PdfiumReader()
    d = rd.open(path.read_bytes())
    pg = rd.read_page(d, 0)
    rd.close(d)
    txt = pg["text"]
    if "...." in txt:
        return "lista-kropkowana"
    rights = [w for w in pg["words"] if w["text"].lower() == "rachunek" and w["bbox"][0] > pg["width_pt"] * 0.45]
    return "ramki-dwie-kolumny" if rights else "jedna-kolumna"


def reading_order_test() -> dict:
    sys.path.insert(0, str(HERE.parent / "vendor"))
    from e01_readers import READERS
    items = [i for i in data.load_items("cases-dev") if i.document_class == "przelew"]
    res: dict = {}
    for name, fn in READERS.items():
        by: dict = {}
        for it in items:
            lay = layout_of(it.source)
            ref = data.reference_for(it)["przelew_bankowy"]
            tx = fn(it.source)
            for field, cls in (("z_rachunku", "z"), ("na_rachunek", "na")):
                got = label_class_before(tx, re.sub(r"\D", "", ref[field]))
                b = by.setdefault(lay, {"n": 0, "ok": 0, "wrong": 0, "no_label": 0, "not_found": 0})
                b["n"] += 1
                if got is None:
                    b["not_found" if re.sub(r"\D", "", ref[field]) not in re.sub(r"\D", "", tx) else "no_label"] += 1
                elif got == cls:
                    b["ok"] += 1
                else:
                    b["wrong"] += 1
        res[name] = by
    return res


def main() -> int:
    out = {"experiment": "E01b", "seed": SEED, "versions": lib.versions(),
           "rotate": rotate_test(), "reading_order_accounts": reading_order_test()}
    lib.dump(HERE / "e01b-geometria.json", out)
    for r, v in out["rotate"]["rotations"].items():
        print(r, v)
    print(out["reading_order_accounts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
