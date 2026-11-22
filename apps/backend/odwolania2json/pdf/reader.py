"""Czytnik PDF na pdfium: słowa z obrysem, linie, obrót, diagnoza strony, render.

Układ współrzędnych: punkty PDF, początek w lewym górnym rogu strony wyświetlanej
po `/Rotate`, x w prawo, y w dół (architektura §4.1).

Diagnoza strony rozstrzyga, czy warstwie tekstu wolno ufać. Strona zdominowana
obrazem albo z niewidoczną warstwą tekstu jest skanem: jej warstwa PDF bywa błędna
(S5: poprawny obraz i niewidoczny tekst z innymi cyframi), więc dalej idzie OCR
i obraz, a nie tekst z PDF (E04, E13).
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from types import TracebackType
from typing import Literal, Self

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_raw
from PIL import Image

from odwolania2json.errors import ProcessingError

__all__ = [
    "DEFAULT_MAX_PAGES",
    "DEFAULT_MAX_PIXELS",
    "IMAGE_DOMINANT_COVERAGE",
    "INVISIBLE_TEXT_SHARE",
    "Bbox",
    "Line",
    "PageDiagnosis",
    "PageReading",
    "PdfDocument",
    "Word",
    "diagnose_page",
    "display_point",
    "group_lines",
]

type Bbox = tuple[float, float, float, float]
PageKind = Literal["text", "scan", "blank"]

# Progi z E04: obraz na co najmniej połowie strony albo co najmniej połowa znaków
# niewidoczna (tryb 3, biel, 1 pt, poza MediaBox) oznacza stronę skanową.
IMAGE_DOMINANT_COVERAGE = 0.5
INVISIBLE_TEXT_SHARE = 0.5
# Limity zasobów: dokument konkursowy ma najwyżej kilkanaście stron, a strona
# renderowana do OCR ok. 2000 px dłuższego boku (E03); zapas jest kilkukrotny.
DEFAULT_MAX_PAGES = 200
DEFAULT_MAX_PIXELS = 25_000_000
_INVISIBLE_RENDER_MODE = 3
_TINY_FONT_PT = 1.5
_WHITE_LEVEL = 250
_HEADER_WINDOW = 1024
_MAX_RENDER_SCALE = 300.0 / 72.0
_OBJECT_DEPTH = 3


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


@dataclass(frozen=True)
class _Geometry:
    """Obrót i rozmiary strony potrzebne do przeliczania obrysów."""

    rotation: int
    mediabox: Bbox
    width: float
    height: float

    def clipped(self, corners: Bbox) -> Bbox | None:
        """Obrys w układzie wyświetlanym przycięty do strony; `None`, gdy pusty."""
        ax, ay = display_point(self.rotation, self.mediabox, corners[0], corners[1])
        bx, by = display_point(self.rotation, self.mediabox, corners[2], corners[3])
        x0, x1 = max(0.0, min(ax, bx)), min(self.width, max(ax, bx))
        y0, y1 = max(0.0, min(ay, by)), min(self.height, max(ay, by))
        if x0 >= x1 or y0 >= y1:
            return None
        return x0, y0, x1, y1


class _WordBuilder:
    """Składa znaki w słowa i scala ich obrysy."""

    def __init__(self) -> None:
        self.words: list[Word] = []
        self._letters: list[str] = []
        self._boxes: list[Bbox] = []

    def add(self, char: str, box: Bbox) -> None:
        self._letters.append(char)
        self._boxes.append(box)

    def flush(self) -> None:
        if self._letters:
            merged = (
                min(box[0] for box in self._boxes),
                min(box[1] for box in self._boxes),
                max(box[2] for box in self._boxes),
                max(box[3] for box in self._boxes),
            )
            self.words.append(Word(text="".join(self._letters), bbox=merged))
        self._letters.clear()
        self._boxes.clear()


class PdfDocument:
    """Otwarty dokument PDF; używaj przez `with`, żeby zwolnić zasoby pdfium."""

    def __init__(self, data: bytes, *, max_pages: int = DEFAULT_MAX_PAGES) -> None:
        if not _is_pdf(data):
            raise ProcessingError("not_a_pdf", "plik nie ma nagłówka PDF")
        try:
            self._document = pdfium.PdfDocument(data)
            self._page_count = len(self._document)
        except pdfium.PdfiumError as error:
            # pdfium zgłasza „hasło” także dla części uszkodzonych plików, więc wymagamy
            # słownika /Encrypt (leży w nieskompresowanym trailerze albo strumieniu xref).
            if "password" in str(error).lower() and b"/Encrypt" in data:
                raise ProcessingError("pdf_encrypted", "PDF jest zaszyfrowany") from None
            raise ProcessingError("pdf_corrupted", "nie udało się otworzyć PDF-a") from None
        if self._page_count == 0:
            self._document.close()
            raise ProcessingError("empty_document", "PDF nie ma stron")
        if self._page_count > max_pages:
            self._document.close()
            raise ProcessingError(
                "page_limit", f"liczba stron {self._page_count} przekracza limit {max_pages}"
            )

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
            width, height = right - left, top - bottom
            if rotation % 180 == 90:
                width, height = height, width
            geometry = _Geometry(rotation, (left, bottom, right, top), width, height)
            words, invisible_share = self._words(page, geometry)
            image_area, objects = self._objects(page, geometry)
        except (pdfium.PdfiumError, IndexError):
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
            invisible_share=invisible_share,
            object_count=objects,
        )

    @staticmethod
    def _is_white(textpage: pdfium.PdfTextPage, index: int) -> bool:
        red, green, blue, alpha = (ctypes.c_uint() for _ in range(4))
        if not pdfium_raw.FPDFText_GetFillColor(textpage.raw, index, red, green, blue, alpha):
            return False
        return min(red.value, green.value, blue.value) >= _WHITE_LEVEL or alpha.value == 0

    @staticmethod
    def _is_unseeable(textpage: pdfium.PdfTextPage, index: int) -> bool:
        """Znak, którego człowiek nie zobaczy: tryb niewidoczny albo mikroskopijny krój.

        Rozmiar bierzemy z pola kroju na stronie, nie z operatora `Tf`: dokumenty
        często ustawiają krój 1 pt i skalują go macierzą tekstu do zwykłej wielkości.
        """
        left, bottom, right, top = textpage.get_charbox(index, loose=True)
        if max(float(right) - float(left), float(top) - float(bottom)) <= _TINY_FONT_PT:
            return True
        text_object = pdfium_raw.FPDFText_GetTextObject(textpage.raw, index)
        if not text_object:
            return False
        return int(pdfium_raw.FPDFTextObj_GetTextRenderMode(text_object)) == _INVISIBLE_RENDER_MODE

    def _words(self, page: pdfium.PdfPage, geometry: _Geometry) -> tuple[list[Word], float]:
        """Słowa widoczne oraz udział znaków niewidocznych w warstwie tekstu.

        Znak w trybie 3, mikroskopijny albo poza stroną nie trafia do tekstu: to
        nie jest treść, którą widzi człowiek (E13). Biały znak zostaje w tekście
        (bywa widoczny na ciemnym tle), ale liczy się do udziału niewidocznych.
        """
        textpage = page.get_textpage()
        count = int(textpage.count_chars())
        if count == 0:
            return [], 0.0
        text = str(textpage.get_text_range(0, count))
        builder = _WordBuilder()
        total = invisible = 0
        for index in range(count):
            # Tekst bywa krótszy niż liczba znaków (pary zastępcze): brak znaku kończy słowo.
            char = text[index] if index < len(text) else ""
            if not char or char.isspace() or char == "\x00":
                builder.flush()
                continue
            total += 1
            raw = textpage.get_charbox(index, loose=False)
            box = geometry.clipped((float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3])))
            if box is None or self._is_unseeable(textpage, index):
                # Znak bez pola na stronie albo niewidoczny: nie zgadujemy geometrii ani treści.
                invisible += 1
                builder.flush()
                continue
            if self._is_white(textpage, index):
                invisible += 1
            builder.add(char, box)
        builder.flush()
        return builder.words, invisible / total if total else 0.0

    @staticmethod
    def _objects(page: pdfium.PdfPage, geometry: _Geometry) -> tuple[float, int]:
        """(pole obrazów w układzie strony, liczba wszystkich obiektów)."""
        image_area = 0.0
        total = 0
        for item in page.get_objects(max_depth=_OBJECT_DEPTH):
            total += 1
            if int(item.type) != pdfium_raw.FPDF_PAGEOBJ_IMAGE:
                continue
            raw = item.get_bounds()
            box = geometry.clipped((float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3])))
            if box is not None:
                image_area += (box[2] - box[0]) * (box[3] - box[1])
        return image_area, total

    def render_page(
        self, index: int, max_side: int, *, max_pixels: int = DEFAULT_MAX_PIXELS
    ) -> Image.Image:
        """Obraz RGB strony (z `/Rotate`), dłuższy bok najwyżej `max_side` pikseli.

        Skala jest też ograniczona do 300 dpi, żeby mała strona nie była sztucznie
        powiększana. Limit pikseli chroni pamięć przed stroną o skrajnych wymiarach.
        """
        number = index + 1
        try:
            page = self._document[index]
            width, height = float(page.get_width()), float(page.get_height())
            scale = min(max_side / max(width, height, 1.0), _MAX_RENDER_SCALE)
            if width * scale * height * scale > max_pixels:
                raise ProcessingError(
                    "pixel_limit",
                    f"obraz strony przekracza limit {max_pixels} pikseli",
                    page=number,
                )
            rendered: Image.Image = page.render(scale=scale).to_pil()
        except (pdfium.PdfiumError, IndexError):
            raise ProcessingError(
                "pdf_corrupted", "błąd renderowania strony PDF", page=number
            ) from None
        return rendered.convert("RGB")
