"""Preprocessing skanów: wykrycie obrotu (0/90/180/270), deskew, binaryzacja. Czysty numpy/opencv; koszt mierzony osobno."""
from __future__ import annotations

import time

import cv2
import numpy as np
from PIL import Image

import ocr_lib


def to_gray(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L"))


def binarize_otsu(img: Image.Image) -> Image.Image:
    g = to_gray(img)
    _, b = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(b).convert("RGB")


def estimate_skew(img: Image.Image, limit: float = 6.0) -> float:
    """Kąt (stopnie, znak jak `PIL.rotate`: dodatni = zawartość obrócona przeciwnie do ruchu wskazówek), z profilu rzutu poziomego."""
    g = to_gray(img)
    s = 900 / max(g.shape)
    g = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    _, b = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    h, w = b.shape
    c = (w / 2, h / 2)

    def score(a: float) -> float:
        m = cv2.getRotationMatrix2D(c, a, 1.0)
        r = cv2.warpAffine(b, m, (w, h), flags=cv2.INTER_NEAREST)
        p = r.sum(axis=1).astype(np.float64)
        return float(np.var(np.diff(p)))

    coarse = np.arange(-limit, limit + 1e-9, 0.5)
    best = max(coarse, key=score)
    fine = np.arange(best - 0.5, best + 0.5 + 1e-9, 0.1)
    return float(max(fine, key=score))


def deskew(img: Image.Image, angle: float) -> Image.Image:
    # estimate_skew zwraca kąt, o który trzeba obrócić (cv2: dodatni = przeciwnie do wskazówek), tak samo jak PIL.rotate
    return img.rotate(angle, resample=Image.BICUBIC, fillcolor=(255, 255, 255))


def detect_rotation(img: Image.Image, ocr: ocr_lib.Ocr) -> tuple[int, dict]:
    """Zwraca k ∈ {0,90,180,270}: `img.rotate(k, expand=True)` przywraca pionową orientację tekstu."""
    small = img.copy()
    small.thumbnail((1000, 1000))
    t0 = time.perf_counter()
    res = ocr.engine(np.asarray(small.convert("RGB")), use_det=True, use_cls=False, use_rec=False)
    boxes = res.boxes if res.boxes is not None else []
    vert = 0
    for b in boxes:
        xs, ys = [p[0] for p in b], [p[1] for p in b]
        vert += (max(ys) - min(ys)) > (max(xs) - min(xs))
    horizontal = vert <= len(boxes) / 2
    cands = (0, 180) if horizontal else (90, 270)
    scores = {}
    for k in cands:
        r = ocr.run(small.rotate(k, expand=True))
        scores[k] = sum(l["confidence"] * len("".join(ch for ch in l["text"] if ch.isalnum())) for l in r["lines"])
    best = max(scores, key=scores.get)
    return best, {"boxes": len(boxes), "vertical_boxes": int(vert), "scores": {str(k): round(v, 2) for k, v in scores.items()},
                  "seconds": round(time.perf_counter() - t0, 3)}
