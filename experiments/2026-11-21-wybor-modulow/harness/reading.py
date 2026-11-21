"""Warstwa odczytu: PdfReader (pypdfium2), OcrProvider (rapidocr | none), diagnoza stron.

Wspólny układ współrzędnych (architektura §4.1): punkty PDF, początek w lewym górnym rogu
strony wyświetlanej po `/Rotate`, x w prawo, y w dół. `to_pdf` to macierz 3×3 (wiersze)
przeliczająca współrzędne wyświetlane na układ użytkownika oryginalnego PDF-a.

Modele danych to zwykłe słowniki JSON-owe (nie klasy), żeby eksperymenty mogły je
zapisywać i porównywać bez adapterów.
"""

from __future__ import annotations

import io
import re
import time
from typing import Any, Protocol

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c

from common import HarnessError, sha256_bytes

SCHEMA_VERSION = 1
Reading = dict[str, Any]
Diagnosis = dict[str, Any]


# ---------- geometria ----------

def display_mapping(rotation: int, mediabox: tuple[float, float, float, float]):
    """Zwraca (funkcja user→display, rozmiar wyświetlany, macierz display→user 3×3 jako lista 9)."""
    l, b, r, t = mediabox
    w, h = r - l, t - b
    rot = rotation % 360

    def fwd(x: float, y: float) -> tuple[float, float]:
        u, v = x - l, y - b
        if rot == 0:
            return u, h - v
        if rot == 90:
            return v, u
        if rot == 180:
            return w - u, v
        if rot == 270:
            return h - v, w - u
        raise ValueError(rot)

    size = (w, h) if rot in (0, 180) else (h, w)
    # macierz odwrotna: display (X, Y) → user (x, y)
    if rot == 0:
        inv = [1, 0, l, 0, -1, b + h, 0, 0, 1]
    elif rot == 90:
        inv = [0, 1, l, 1, 0, b, 0, 0, 1]
    elif rot == 180:
        inv = [-1, 0, l + w, 0, 1, b, 0, 0, 1]
    else:
        inv = [0, -1, l + w, -1, 0, b + h, 0, 0, 1]
    return fwd, size, [float(v) for v in inv]


def _valid_bbox(bb: list[float]) -> bool:
    return len(bb) == 4 and bb[0] < bb[2] and bb[1] < bb[3]


def _round(bb: list[float]) -> list[float]:
    return [round(float(v), 2) for v in bb]


def group_lines(words: list[dict[str, Any]], page: int) -> list[dict[str, Any]]:
    """Grupuje słowa w linie geometrycznie i nadaje `line_id`/`order`. Słowa zostają w kolejności czytania."""
    lines: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for w in words:
        x0, y0, x1, y1 = w["bbox"]
        cy = (y0 + y1) / 2
        if cur is not None:
            cy0, cy1 = cur["bbox"][1], cur["bbox"][3]
            same = cy0 <= cy <= cy1 and x0 >= cur["bbox"][0] - 1
            if not same:
                cur = None
        if cur is None:
            cur = {"id": f"p{page}l{len(lines) + 1}", "words": [], "bbox": list(w["bbox"]), "_t": []}
            lines.append(cur)
        cur["words"].append(w["id"])
        cur["_t"].append(w["text"])
        cur["bbox"] = [min(cur["bbox"][0], x0), min(cur["bbox"][1], y0), max(cur["bbox"][2], x1), max(cur["bbox"][3], y1)]
        w["line_id"] = cur["id"]
        w["order"] = len(cur["words"]) - 1
    for ln in lines:
        ln["text"] = " ".join(ln.pop("_t"))
        ln["bbox"] = _round(ln["bbox"])
    return lines


# ---------- PdfReader ----------

class PdfReader(Protocol):
    name: str

    def open(self, data: bytes) -> Any: ...
    def page_count(self, doc: Any) -> int: ...
    def read_page(self, doc: Any, index: int) -> dict[str, Any]: ...
    def render_page(self, doc: Any, index: int, dpi: int) -> Any: ...
    def close(self, doc: Any) -> None: ...


class PdfiumReader:
    """Warstwa tekstowa PDF przez pypdfium2; słowa z bbox liczone ze znaków."""

    name = "pdfium"

    def info(self) -> dict[str, Any]:
        return {"name": "pypdfium2", "version": pdfium.version.PYPDFIUM_INFO.version if hasattr(pdfium, "version") else None}

    def open(self, data: bytes) -> pdfium.PdfDocument:
        try:
            return pdfium.PdfDocument(data)
        except pdfium.PdfiumError as e:
            msg = str(e).lower()
            if "password" in msg:
                raise HarnessError("pdf_encrypted", "PDF zaszyfrowany lub wymaga hasła", stage="read") from None
            raise HarnessError("pdf_corrupted", "nie udało się otworzyć PDF-a", stage="read") from None

    def page_count(self, doc: pdfium.PdfDocument) -> int:
        return len(doc)

    def render_page(self, doc: pdfium.PdfDocument, index: int, dpi: int) -> Any:
        """PIL.Image strony z uwzględnieniem /Rotate (zgodnie z układem wyświetlanym)."""
        try:
            return doc[index].render(scale=dpi / 72.0).to_pil().convert("RGB")
        except pdfium.PdfiumError:
            raise HarnessError("pdf_corrupted", "błąd renderowania strony", stage="read", page=index + 1) from None

    def read_page(self, doc: pdfium.PdfDocument, index: int) -> dict[str, Any]:
        number = index + 1
        try:
            page = doc[index]
            rotation = page.get_rotation()
            box = page.get_mediabox()
            fwd, (wd, hd), to_pdf = display_mapping(rotation, box)
            tp = page.get_textpage()
            n = tp.count_chars()
            words: list[dict[str, Any]] = []
            cur: list[tuple[str, tuple[float, float, float, float]]] = []

            def flush() -> None:
                if not cur:
                    return
                xs, ys = [], []
                for _, (l, b, r, t) in cur:
                    for px, py in ((l, b), (r, t)):
                        dx, dy = fwd(px, py)
                        xs.append(dx)
                        ys.append(dy)
                bb = [max(0.0, min(xs)), max(0.0, min(ys)), min(wd, max(xs)), min(hd, max(ys))]
                text = "".join(c for c, _ in cur)
                if _valid_bbox(bb):
                    words.append({"id": f"p{number}w{len(words) + 1}", "text": text, "line_id": "", "order": 0,
                                  "bbox": _round(bb), "confidence": None, "source": "pdf"})
                cur.clear()

            if n:
                text_all = tp.get_text_range(0, n)
                # get_text_range może zwracać mniej znaków niż count_chars (surogaty): dopasuj po indeksie znaku
                for i in range(n):
                    ch = text_all[i] if i < len(text_all) else ""
                    if ch == "" or ch.isspace() or ch in "\r\n\x00":
                        flush()
                        continue
                    box_c = tp.get_charbox(i, loose=False)
                    if box_c[2] <= box_c[0] or box_c[3] <= box_c[1]:
                        flush()  # znak bez geometrii: nie zgadujemy bbox
                        continue
                    cur.append((ch, box_c))
                flush()
            lines = group_lines(words, number)
            images = self._images(page, fwd, number)
            text = "\n".join(ln["text"] for ln in lines)
            return {"number": number, "width_pt": round(wd, 2), "height_pt": round(hd, 2), "text": text,
                    "source": "pdf" if words else "none", "words": words, "lines": lines, "images": images,
                    "to_pdf": to_pdf, "rotation": rotation}
        except HarnessError:
            raise
        except pdfium.PdfiumError:
            raise HarnessError("pdf_corrupted", "błąd odczytu strony PDF", stage="read", page=number) from None

    @staticmethod
    def _images(page: pdfium.PdfPage, fwd, number: int) -> list[dict[str, Any]]:
        out = []
        try:
            for k, obj in enumerate(page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE], max_depth=2)):
                l, b, r, t = obj.get_bounds()
                xs, ys = zip(fwd(l, b), fwd(r, t), strict=True)
                bb = [min(xs), min(ys), max(xs), max(ys)]
                if _valid_bbox(bb):
                    out.append({"id": f"p{number}i{k + 1}", "file": "", "bbox": _round(bb), "sha256": ""})
        except pdfium.PdfiumError:
            pass
        return out

    def close(self, doc: pdfium.PdfDocument) -> None:
        doc.close()


# ---------- OCR ----------

class OcrProvider(Protocol):
    name: str

    def info(self) -> dict[str, Any]: ...
    def ocr_image(self, image: Any, dpi: int) -> dict[str, Any]: ...


class NoOcr:
    """Dostawca wyłączony (architektura §5): jawnie niedostępny."""

    name = "none"

    def info(self) -> dict[str, Any]:
        return {"available": False, "name": "none", "version": None, "parameter_count": None,
                "license": None, "location": None, "models": []}

    def ocr_image(self, image: Any, dpi: int) -> dict[str, Any]:
        raise HarnessError("ocr_unavailable", "OCR wyłączony w konfiguracji", stage="ocr", retryable=False)


class RapidOcr:
    """rapidocr + onnxruntime (CPU). Silnik tworzony leniwie i raz na proces."""

    name = "rapidocr"

    def __init__(self) -> None:
        self._engine: Any = None
        self._load_error: str | None = None

    def _get(self) -> Any:
        if self._engine is None:
            try:
                import logging
                from rapidocr import RapidOCR
                logging.getLogger("RapidOCR").setLevel(logging.WARNING)
                self._engine = RapidOCR()
            except Exception as e:  # noqa: BLE001 — brak pakietu/wag: jawny kod, bez treści dokumentu
                self._load_error = type(e).__name__
                raise HarnessError("ocr_unavailable", f"rapidocr nie startuje: {type(e).__name__}", stage="ocr") from None
        return self._engine

    def info(self) -> dict[str, Any]:
        import importlib.metadata as md
        try:
            ver = md.version("rapidocr")
            ort = md.version("onnxruntime")
            import rapidocr
            from pathlib import Path
            mdir = Path(rapidocr.__file__).parent / "models"
            models = [{"name": p.stem, "role": "det" if "det" in p.stem else "rec" if "rec" in p.stem else "cls",
                       "version": None, "license": "Apache-2.0 (do potwierdzenia ADR-002)", "location": "local (pip)",
                       "parameter_count": None, "bytes": p.stat().st_size} for p in sorted(mdir.glob("*.onnx"))]
            return {"available": self._load_error is None, "name": "rapidocr", "version": ver, "onnxruntime": ort,
                    "parameter_count": None, "license": "Apache-2.0", "location": "local", "models": models}
        except Exception:  # noqa: BLE001
            return {"available": False, "name": "rapidocr", "version": None, "parameter_count": None,
                    "license": None, "location": None, "models": []}

    def ocr_image(self, image: Any, dpi: int) -> dict[str, Any]:
        import numpy as np
        engine = self._get()
        try:
            res = engine(np.asarray(image), return_word_box=True)
        except Exception as e:  # noqa: BLE001
            raise HarnessError("ocr_error", f"błąd OCR: {type(e).__name__}", stage="ocr") from None
        lines, words = [], []
        if res.txts:
            wr = res.word_results or [()] * len(res.txts)
            for li, (box, txt, score) in enumerate(zip(res.boxes, res.txts, res.scores, strict=True), 1):
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                lines.append({"id": f"l{li}", "text": txt, "bbox": [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))], "confidence": float(score)})
                for wi, (wt, ws, wb) in enumerate(wr[li - 1] if li - 1 < len(wr) else (), 1):
                    wx = [p[0] for p in wb]
                    wy = [p[1] for p in wb]
                    words.append({"id": f"l{li}w{wi}", "line_id": f"l{li}", "text": wt, "confidence": float(ws),
                                  "bbox": [float(min(wx)), float(min(wy)), float(max(wx)), float(max(wy))]})
        return {"lines": lines, "words": words, "rotation_degrees": 0, "dpi": dpi}


def make_ocr(name: str) -> OcrProvider:
    if name == "none":
        return NoOcr()
    if name == "rapidocr":
        return RapidOcr()
    raise HarnessError("invalid_configuration", f"nieznany dostawca OCR: {name}", stage="config")


def ocr_page_to_reading(page_no: int, ocr: dict[str, Any], dpi: int, width_pt: float, height_pt: float) -> dict[str, Any]:
    """Przelicza słowa OCR z pikseli na punkty strony; linie zostają takie, jak zwrócił OCR.

    Słowo bez poprawnego bbox po przycięciu do strony jest pomijane (nie zgadujemy geometrii).
    """
    k = 72.0 / dpi
    words: list[dict[str, Any]] = []
    lines: dict[str, dict[str, Any]] = {}
    for ln in ocr["lines"]:
        bb = [ln["bbox"][0] * k, ln["bbox"][1] * k, ln["bbox"][2] * k, ln["bbox"][3] * k]
        bb = [max(0.0, bb[0]), max(0.0, bb[1]), min(width_pt, bb[2]), min(height_pt, bb[3])]
        if _valid_bbox(bb):
            lines[ln["id"]] = {"id": f"p{page_no}o{ln['id']}", "text": ln["text"], "words": [], "bbox": _round(bb)}
    for w in ocr["words"]:
        ln = lines.get(w["line_id"])
        bb = [w["bbox"][0] * k, w["bbox"][1] * k, w["bbox"][2] * k, w["bbox"][3] * k]
        bb = [max(0.0, bb[0]), max(0.0, bb[1]), min(width_pt, bb[2]), min(height_pt, bb[3])]
        if ln is None or not _valid_bbox(bb) or not w["text"].strip():
            continue
        wid = f"p{page_no}o{w['id']}"
        ln["words"].append(wid)
        words.append({"id": wid, "text": w["text"], "line_id": ln["id"], "order": len(ln["words"]) - 1,
                      "bbox": _round(bb), "confidence": round(float(w["confidence"]), 4), "source": "ocr"})
    kept = [ln for ln in lines.values() if ln["words"]]
    return {"words": words, "lines": kept, "text": "\n".join(ln["text"] for ln in kept)}


# ---------- diagnoza ----------

MIN_WORDS_TEXT = 1  # strona z choć jednym słowem warstwy tekstowej nie jest pustą ani czystym skanem
SCAN_COVERAGE = 0.5


def diagnose_page(page: dict[str, Any], *, ocr_available: bool) -> dict[str, Any]:
    n_words = len([w for w in page["words"] if w["source"] == "pdf"])
    w, h = page["width_pt"], page["height_pt"]
    area = max(w * h, 1.0)
    img_cov = min(1.0, sum((i["bbox"][2] - i["bbox"][0]) * (i["bbox"][3] - i["bbox"][1]) for i in page["images"]) / area)
    codes: list[str] = []
    if n_words >= MIN_WORDS_TEXT and img_cov < 0.5:
        src, requires = "pdf", False
    elif n_words < MIN_WORDS_TEXT and img_cov >= SCAN_COVERAGE:
        src, requires = "none", True
        codes.append("scan")
    elif n_words >= MIN_WORDS_TEXT:
        src, requires = "mixed", True
        codes.append("scan" if img_cov >= 0.8 else "mixed_page")
    elif n_words == 0 and img_cov < 0.05:
        src, requires = "none", False  # pusta strona
    else:
        src, requires = "none", True
        codes.append("scan")
    if requires and not ocr_available:
        codes.append("ocr_unavailable")
    return {"number": page["number"], "text_source": src, "coverage": None, "rotation_degrees": page.get("rotation"),
            "confidence": None, "method": "diagnosis-v1", "requires_ocr": requires,
            "signals": [{"code": "pdf_word_count", "value": n_words, "description": "Słowa z warstwy tekstowej"},
                        {"code": "image_coverage", "value": round(img_cov, 3), "description": "Pokrycie strony obrazami"}],
            "codes": codes}


def diagnose_document(page_diags: list[dict[str, Any]]) -> Diagnosis:
    """Agreguje strony bez maskowania średnią: źródło dokumentu to wspólne źródło stron niepustych albo `mixed`."""
    non_blank = [d for d in page_diags if d["requires_ocr"] or d["text_source"] != "none"]
    kinds = {d["text_source"] for d in non_blank}
    if not non_blank:
        # same puste strony albo skany bez odczytu: rozróżnia to requires_ocr stron
        text_source = "none"
    elif len(kinds) == 1:
        text_source = kinds.pop()
    else:
        text_source = "mixed"
    # strona skanu bez OCR ma text_source=none, ale wymaga OCR: liczymy ją jako osobne źródło
    effective = {("scan" if d["requires_ocr"] and d["text_source"] == "none" else d["text_source"]) for d in non_blank}
    codes: list[str] = []
    for d in page_diags:
        codes += [c for c in d["codes"] if c not in codes]
    if len(effective) > 1 and "mixed_document" not in codes:
        codes.append("mixed_document")
        text_source = "mixed"
    return {"schema_version": SCHEMA_VERSION, "text_source": text_source, "coverage": None, "rotation_degrees": None,
            "confidence": None, "method": "diagnosis-v1", "requires_ocr": any(d["requires_ocr"] for d in page_diags),
            "signals": [], "codes": codes, "pages": page_diags}


# ---------- odczyt dokumentu ----------

def read_document(data: bytes, *, reader: PdfReader, ocr: OcrProvider, ocr_policy: str, ocr_dpi: int,
                  max_pages: int, deadline: float | None = None) -> tuple[Reading, Diagnosis, dict[str, Any]]:
    """PDF → Reading + Diagnosis + metryki (czasy, strony OCR). Wyjątki to HarnessError z kodem."""
    t0 = time.monotonic()
    doc = reader.open(data)
    metrics: dict[str, Any] = {"pdf_read_s": 0.0, "ocr_s": 0.0, "ocr_pages": 0, "pages": 0}
    try:
        n = reader.page_count(doc)
        if n == 0:
            raise HarnessError("empty_document", "PDF bez stron", stage="read")
        if n > max_pages:
            raise HarnessError("page_limit", f"liczba stron {n} przekracza limit {max_pages}", stage="read")
        metrics["pages"] = n
        pages, diags, ocr_errors = [], [], []
        ocr_ok = ocr.info()["available"] and ocr_policy != "never"
        for i in range(n):
            if deadline is not None and time.monotonic() > deadline:
                raise HarnessError("time_limit", "przekroczono limit czasu dokumentu", stage="read", page=i + 1)
            tp = time.monotonic()
            pg = reader.read_page(doc, i)
            metrics["pdf_read_s"] += time.monotonic() - tp
            diag = diagnose_page(pg, ocr_available=ocr_ok)
            need_ocr = ocr_policy == "always" or (ocr_policy == "if_needed" and diag["requires_ocr"])
            if need_ocr and ocr_policy != "never":
                to = time.monotonic()
                try:
                    img = reader.render_page(doc, i, ocr_dpi)
                    res = ocr.ocr_image(img, ocr_dpi)
                    extra = ocr_page_to_reading(pg["number"], res, ocr_dpi, pg["width_pt"], pg["height_pt"])
                    pg["words"] = pg["words"] + extra["words"]
                    pg["lines"] = pg["lines"] + extra["lines"]
                    pg["text"] = (pg["text"] + "\n" + extra["text"]).strip()
                    pg["source"] = "mixed" if any(w["source"] == "pdf" for w in pg["words"]) and extra["words"] else ("ocr" if extra["words"] else pg["source"])
                    diag["text_source"] = pg["source"] if extra["words"] else diag["text_source"]
                    diag["codes"] = [c for c in diag["codes"] if c != "ocr_unavailable"]
                    metrics["ocr_pages"] += 1
                except HarnessError as e:
                    if e.code not in ("ocr_unavailable", "ocr_error"):
                        raise
                    e.page = pg["number"]
                    ocr_errors.append(e)
                    if e.code not in diag["codes"]:
                        diag["codes"].append(e.code)
                finally:
                    metrics["ocr_s"] += time.monotonic() - to
            pages.append(pg)
            diags.append(diag)
        reading = {"schema_version": SCHEMA_VERSION, "document_sha256": sha256_bytes(data), "pages": pages}
        metrics["ocr_errors"] = [e.to_dict() for e in ocr_errors]
        metrics["unprocessed_pages"] = [e.page for e in ocr_errors]
        return reading, diagnose_document(diags), metrics
    finally:
        reader.close(doc)
        metrics["total_s"] = time.monotonic() - t0
