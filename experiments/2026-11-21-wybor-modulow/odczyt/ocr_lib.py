"""OCR rapidocr+onnxruntime z jawną liczbą wątków i limitem boku (Global.max_side_len); wynik jak `reading.RapidOcr.ocr_image`."""
from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
from PIL import Image

import lib  # noqa: F401  (ścieżki)


class Ocr:
    def __init__(self, threads: int = 4, max_side: int = 2000, inter: int = 1) -> None:
        from rapidocr import RapidOCR
        logging.getLogger("RapidOCR").setLevel(logging.WARNING)
        self.threads, self.max_side = threads, max_side
        self.engine = RapidOCR(params={"EngineConfig.onnxruntime.intra_op_num_threads": threads,
                                       "EngineConfig.onnxruntime.inter_op_num_threads": inter,
                                       "Global.max_side_len": max_side, "Global.log_level": "warning"})

    def run(self, img: Image.Image) -> dict[str, Any]:
        res = self.engine(np.asarray(img.convert("RGB")), use_det=True, use_cls=True, use_rec=True, return_word_box=True)
        lines, words = [], []
        if res.txts:
            wr = res.word_results or [()] * len(res.txts)
            for li, (box, txt, sc) in enumerate(zip(res.boxes, res.txts, res.scores, strict=True), 1):
                xs, ys = [p[0] for p in box], [p[1] for p in box]
                lines.append({"id": f"l{li}", "text": txt, "confidence": float(sc), "bbox": [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]})
                for wi, (wt, ws, wb) in enumerate(wr[li - 1] if li - 1 < len(wr) else (), 1):
                    wx, wy = [p[0] for p in wb], [p[1] for p in wb]
                    words.append({"id": f"l{li}w{wi}", "line_id": f"l{li}", "text": wt, "confidence": float(ws),
                                  "bbox": [float(min(wx)), float(min(wy)), float(max(wx)), float(max(wy))]})
        return {"lines": lines, "words": words, "text": "\n".join(l["text"] for l in lines)}

    def timed(self, img: Image.Image) -> tuple[dict[str, Any], float]:
        t = time.perf_counter()
        r = self.run(img)
        return r, time.perf_counter() - t


def render_a4(doc, index: int, dpi: int) -> Image.Image:
    """Render strony przy „dpi znormalizowanym do A4”: dłuższy bok = dpi × 11,69 cala, niezależnie od MediaBox.

    Uprząż renderuje `scale = dpi/72` względem MediaBox; dla skanu szablonu (strona 1240 pt zamiast 595 pt) daje to ok. 2,08× więcej pikseli
    niż „nominalne” dpi. W eksperymentach dpi oznacza więc piksele na A4, żeby warianty były porównywalne (patrz BLOKERY.md).
    """
    w, h = doc[index].get_size()
    scale = dpi * 11.69 / max(w, h)
    return doc[index].render(scale=scale).to_pil().convert("RGB")
