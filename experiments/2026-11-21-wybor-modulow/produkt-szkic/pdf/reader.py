"""Czytnik PDF na pdfium: słowa z obrysem, linie, obrót, diagnoza strony, render.

Układ współrzędnych: punkty PDF, początek w lewym górnym rogu strony wyświetlanej
po `/Rotate`, x w prawo, y w dół (architektura §4.1).

Diagnoza strony rozstrzyga, czy warstwie tekstu wolno ufać. Strona zdominowana
obrazem albo z niewidoczną warstwą tekstu jest skanem: jej warstwa PDF bywa błędna
(S5: poprawny obraz i niewidoczny tekst z innymi cyframi), więc dalej idzie OCR
i obraz, a nie tekst z PDF (E04, E13).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import Literal, Self

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_raw
from PIL import Image

from odwolania2json.errors import ProcessingError

__all__ = [
    "IMAGE_DOMINANT_COVERAGE",
    "INVISIBLE_TEXT_SHARE",
    "Line",
    "PageDiagnosis",
    "PageReading",
    "PdfDocument",
    "Word",
    "diagnose_page",
    "display_point",
    "group_lines",
]

Bbox = tuple[float, float, float, float]
PageKind = Literal["text", "scan", "blank"]

# Progi z E04: obraz na co najmniej połowie strony albo co najmniej połowa obiektów
# tekstowych w trybie niewidocznym (render mode 3) oznacza stronę skanową.
IMAGE_DOMINANT_COVERAGE = 0.5
INVISIBLE_TEXT_SHARE = 0.5
_INVISIBLE_RENDER_MODE = 3
_HEADER_WINDOW = 1024
_MAX_RENDER_SCALE = 300.0 / 72.0


@dataclass(frozen=True)
class Word:
    """Słowo warstwy tekstowej z obrysem w układzie strony wyświetlanej."""

    text: str
    bbox: Bbox


@dataclass(frozen=True)
class Line:
    """Linia tekstu z identyfikatorem `p<strona>l<numer>`."""

    id: str
    text: str
    bbox: Bbox


@dataclass(frozen=True)
class PageReading:
    """Odczyt jednej strony: warstwa tekstu i sygnały do diagnozy."""

    number: int
    width_pt: float
    height_pt: float
    rotation: int
    words: tuple[Word, ...]
    lines: tuple[Line, ...]
    image_coverage: float
    invisible_share: float
    object_count: int

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)


@dataclass(frozen=True)
class PageDiagnosis:
    """Wynik diagnozy strony wraz z sygnałami, na których się opiera."""

    number: int
    kind: PageKind
    requires_ocr: bool
    word_count: int
    image_coverage: float
    invisible_share: float
    reasons: tuple[str, ...]


def diagnose_page(page: PageReading) -> PageDiagnosis:
    """Tekst, skan czy pusta strona; skan wymaga OCR i traci warstwę PDF."""
    word_count = len(page.words)
    reasons: list[str] = []
    if page.invisible_share >= INVISIBLE_TEXT_SHARE:
        reasons.append("invisible_text")
    if page.image_coverage >= IMAGE_DOMINANT_COVERAGE:
        reasons.append("image_dominant")
    if word_count == 0 and page.object_count > 0 and not reasons:
        # Brak słów przy niepustej stronie: tekst może być obrazem albo krzywymi.
        reasons.append("no_text_layer")
    kind: PageKind = "scan" if reasons else ("text" if word_count else "blank")
    return PageDiagnosis(
        number=page.number,
        kind=kind,
        requires_ocr=kind == "scan",
        word_count=word_count,
        image_coverage=page.image_coverage,
        invisible_share=page.invisible_share,
        reasons=tuple(reasons),
    )


def display_point(rotation: int, mediabox: Bbox, x: float, y: float) -> tuple[float, float]:
    """Punkt z układu użytkownika PDF w układzie strony wyświetlanej po `/Rotate`."""
    left, bottom, right, top = mediabox
    width, height = right - left, top - bottom
    u, v = x - left, y - bottom
    turn = rotation % 360
    if turn == 90:
        return v, u
    if turn == 180:
        return width - u, v
    if turn == 270:
        return height - v, width - u
    return u, height - v


def group_lines(words: list[Word], page_number: int) -> tuple[Line, ...]:
    """Grupuje słowa (w kolejności czytania) w linie według położenia w pionie.

    Słowo należy do bieżącej linii, gdy jego środek mieści się w jej wysokości
    i nie cofa się przed jej początek; inaczej zaczyna nową linię.
    """
    groups: list[tuple[list[str], list[float]]] = []
    for word in words:
        x0, y0, x1, y1 = word.bbox
        center = (y0 + y1) / 2
        if groups:
            texts, box = groups[-1]
            if box[1] <= center <= box[3] and x0 >= box[0] - 1:
                texts.append(word.text)
                box[0], box[1] = min(box[0], x0), min(box[1], y0)
                box[2], box[3] = max(box[2], x1), max(box[3], y1)
                continue
        groups.append(([word.text], [x0, y0, x1, y1]))
    return tuple(
        Line(
            id=f"p{page_number}l{index}",
            text=" ".join(texts),
            bbox=(box[0], box[1], box[2], box[3]),
        )
        for index, (texts, box) in enumerate(groups, 1)
    )


def _is_pdf(data: bytes) -> bool:
    return b"%PDF-" in data[:_HEADER_WINDOW]


class PdfDocument:
    """Otwarty dokument PDF; używaj przez `with`, żeby zwolnić zasoby pdfium."""

    def __init__(self, data: bytes) -> None:
        if not _is_pdf(data):
            raise ProcessingError("not_a_pdf", "plik nie ma nagłówka PDF")
        try:
            self._document = pdfium.PdfDocument(data)
            self._page_count = len(self._document)
        except pdfium.PdfiumError as error:
            if "password" in str(error).lower():
                raise ProcessingError("pdf_encrypted", "PDF jest zaszyfrowany") from None
            raise ProcessingError("pdf_corrupted", "nie udało się otworzyć PDF-a") from None
        if self._page_count == 0:
            self._document.close()
            raise ProcessingError("empty_document", "PDF nie ma stron")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._document.close()

    @property
    def page_count(self) -> int:
        return self._page_count

    def read_page(self, index: int) -> PageReading:
        """Warstwa tekstu i sygnały diagnozy strony o indeksie `index` (od zera)."""
        number = index + 1
        try:
            page = self._document[index]
            rotation = int(page.get_rotation())
            left, bottom, right, top = (float(value) for value in page.get_mediabox())
            mediabox = (left, bottom, right, top)
            width, height = right - left, top - bottom
            if rotation % 180 == 90:
                width, height = height, width
            words = self._words(page, rotation, mediabox, width, height)
            image_area, text_objects, invisible, objects = self._objects(
                page, rotation, mediabox, width, height
            )
        except pdfium.PdfiumError:
            raise ProcessingError("pdf_corrupted", "błąd odczytu strony PDF", page=number) from None
        area = max(width * height, 1.0)
        return PageReading(
            number=number,
            width_pt=width,
            height_pt=height,
            rotation=rotation,
            words=tuple(words),
            lines=group_lines(words, number),
            image_coverage=min(1.0, image_area / area),
            invisible_share=invisible / text_objects if text_objects else 0.0,
            object_count=objects,
        )

    @staticmethod
    def _clipped(
        rotation: int, mediabox: Bbox, width: float, height: float, corners: Bbox
    ) -> Bbox | None:
        """Obrys w układzie wyświetlanym przycięty do strony; `None`, gdy pusty."""
        ax, ay = display_point(rotation, mediabox, corners[0], corners[1])
        bx, by = display_point(rotation, mediabox, corners[2], corners[3])
        x0, x1 = max(0.0, min(ax, bx)), min(width, max(ax, bx))
        y0, y1 = max(0.0, min(ay, by)), min(height, max(ay, by))
        if x0 >= x1 or y0 >= y1:
            return None
        return x0, y0, x1, y1

    def _words(
        self, page: pdfium.PdfPage, rotation: int, mediabox: Bbox, width: float, height: float
    ) -> list[Word]:
        textpage = page.get_textpage()
        count = int(textpage.count_chars())
        if count == 0:
            return []
        text = str(textpage.get_text_range(0, count))
        words: list[Word] = []
        letters: list[str] = []
        boxes: list[Bbox] = []

        def flush() -> None:
            if letters:
                merged = (
                    min(box[0] for box in boxes),
                    min(box[1] for box in boxes),
                    max(box[2] for box in boxes),
                    max(box[3] for box in boxes),
                )
                words.append(Word(text="".join(letters), bbox=merged))
            letters.clear()
            boxes.clear()

        for index in range(count):
            # Tekst bywa krótszy niż liczba znaków (pary zastępcze): brak znaku kończy słowo.
            char = text[index] if index < len(text) else ""
            if not char or char.isspace() or char == "\x00":
                flush()
                continue
            raw = textpage.get_charbox(index, loose=False)
            corners = (float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]))
            box = self._clipped(rotation, mediabox, width, height, corners)
            if box is None:
                # Znak bez pola na stronie (np. poza MediaBox): nie zgadujemy geometrii.
                flush()
                continue
            letters.append(char)
            boxes.append(box)
        flush()
        return words

    def _objects(
        self, page: pdfium.PdfPage, rotation: int, mediabox: Bbox, width: float, height: float
    ) -> tuple[float, int, int, int]:
        """(pole obrazów, liczba obiektów tekstowych, w tym niewidocznych, wszystkich)."""
        image_area = 0.0
        text_objects = invisible = total = 0
        for item in page.get_objects(max_depth=3):
            total += 1
            kind = int(item.type)
            if kind == pdfium_raw.FPDF_PAGEOBJ_IMAGE:
                raw = item.get_bounds()
                corners = (float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]))
                box = self._clipped(rotation, mediabox, width, height, corners)
                if box is not None:
                    image_area += (box[2] - box[0]) * (box[3] - box[1])
            elif kind == pdfium_raw.FPDF_PAGEOBJ_TEXT:
                text_objects += 1
                mode = int(pdfium_raw.FPDFTextObj_GetTextRenderMode(item.raw))
                if mode == _INVISIBLE_RENDER_MODE:
                    invisible += 1
        return image_area, text_objects, invisible, total

    def render_page(self, index: int, max_side: int) -> Image.Image:
        """Obraz RGB strony (z `/Rotate`), dłuższy bok najwyżej `max_side` pikseli.

        Skala jest też ograniczona do 300 dpi, żeby mała strona nie była sztucznie
        powiększana, a liczba pikseli miała stałą górną granicę.
        """
        try:
            page = self._document[index]
            longest = max(float(page.get_width()), float(page.get_height()), 1.0)
            scale = min(max_side / longest, _MAX_RENDER_SCALE)
            rendered: Image.Image = page.render(scale=scale).to_pil()
        except pdfium.PdfiumError:
            raise ProcessingError(
                "pdf_corrupted", "błąd renderowania strony PDF", page=index + 1
            ) from None
        return rendered.convert("RGB")
