"""OCR stron skanowych: protokół `OcrProvider` i adapter `rapidocr` (onnxruntime, CPU).

Ustalenia z eksperymentów:

- E02: konfiguracja limitu jest w pikselach dłuższego boku obrazu (`max_side`), nie w dpi;
  200 i 300 dpi dają ten sam wynik przy limicie 2000 px.
- E03: wykrywanie obrotu 90/180/270 daje +0,30…+0,46 odnajdywalności na stronach obróconych;
  prostowanie skosu i binaryzacja szkodziły, więc ich tu **nie ma**.
- E-T1: największy skok czasu daje przejście z 1 na 4 wątki onnxruntime; liczba wątków jest jawna.

Silnik ładuje się leniwie i raz na proces. Brak pakietu albo wag to jawny błąd
`ocr_unavailable`, a nie pusty tekst; błąd w trakcie rozpoznawania to `ocr_error`.
Współrzędne wyniku są w pikselach obrazu wejściowego (oś Y w dół); do punktów strony
przelicza je :meth:`OcrResult.to_page_points`.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from PIL import Image

from odwolania2json.errors import ProcessingError

__all__ = [
    "Bbox",
    "EngineFactory",
    "OcrLine",
    "OcrProvider",
    "OcrResult",
    "OcrWord",
    "RapidOcr",
    "UnavailableOcr",
]

Bbox = tuple[float, float, float, float]

_ROTATION_PROBE_SIDE = 1000
_MIN_MAX_SIDE = 64
# Klasyfikator linii w silniku czyta część tekstu obróconego o 180° prawie równie dobrze,
# więc drugi kandydat musi być wyraźnie lepszy; przy szumie zostaje pierwszy (bez obrotu).
_ROTATION_MARGIN = 1.1


@dataclass(frozen=True)
class OcrWord:
    """Słowo rozpoznane przez OCR; `bbox` to (x0, y0, x1, y1)."""

    text: str
    confidence: float
    bbox: Bbox


@dataclass(frozen=True)
class OcrLine:
    """Linia rozpoznana przez OCR; `words` bywa puste, gdy silnik nie podał słów."""

    text: str
    confidence: float
    bbox: Bbox
    words: tuple[OcrWord, ...] = ()


def _clip(bbox: Bbox, width: float, height: float) -> Bbox | None:
    """Przycina prostokąt do obszaru; `None`, gdy nie zostaje nic o dodatnim polu."""
    x0, y0 = max(0.0, bbox[0]), max(0.0, bbox[1])
    x1, y1 = min(width, bbox[2]), min(height, bbox[3])
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, y0, x1, y1)


def _scale(bbox: Bbox, kx: float, ky: float) -> Bbox:
    return (bbox[0] * kx, bbox[1] * ky, bbox[2] * kx, bbox[3] * ky)


@dataclass(frozen=True)
class OcrResult:
    """Wynik OCR strony.

    `rotation` to kąt (przeciwnie do ruchu wskazówek, jak `PIL.Image.rotate`), o który
    obrócono obraz przed odczytem; `bbox` wracają do układu obrazu wejściowego, którego
    rozmiar w pikselach to `width_px` × `height_px`.
    """

    lines: tuple[OcrLine, ...]
    rotation: int
    width_px: int
    height_px: int

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    @property
    def words(self) -> tuple[OcrWord, ...]:
        return tuple(word for line in self.lines for word in line.words)

    def to_page_points(self, width_pt: float, height_pt: float) -> OcrResult:
        """Przelicza piksele obrazu na punkty strony i przycina do jej obrysu.

        Skala jest osobna w poziomie i w pionie. Słowo albo linia, które po przycięciu nie
        mają dodatniego pola, są pomijane: geometrii nie zgadujemy.
        """
        if width_pt <= 0 or height_pt <= 0:
            raise ValueError("rozmiar strony w punktach musi być dodatni")
        kx = width_pt / self.width_px
        ky = height_pt / self.height_px
        lines: list[OcrLine] = []
        for line in self.lines:
            line_box = _clip(_scale(line.bbox, kx, ky), width_pt, height_pt)
            if line_box is None:
                continue
            words = []
            for word in line.words:
                word_box = _clip(_scale(word.bbox, kx, ky), width_pt, height_pt)
                if word_box is not None:
                    words.append(OcrWord(word.text, word.confidence, word_box))
            lines.append(OcrLine(line.text, line.confidence, line_box, tuple(words)))
        return OcrResult(tuple(lines), self.rotation, self.width_px, self.height_px)


class OcrProvider(Protocol):
    """Wymienny dostawca OCR (architektura §4.2)."""

    name: str

    def recognize(self, image: Image.Image) -> OcrResult: ...


class UnavailableOcr:
    """Dostawca wyłączony w konfiguracji: każda próba to jawny błąd."""

    name = "none"

    def recognize(self, image: Image.Image) -> OcrResult:
        raise ProcessingError("ocr_unavailable", "OCR jest wyłączony w konfiguracji")


class _EngineOutput(Protocol):
    """Fragment wyniku `rapidocr`: pola bywają `None` albo tablicami numpy."""

    @property
    def boxes(self) -> Sequence[Sequence[Sequence[float]]] | None: ...

    @property
    def txts(self) -> Sequence[str] | None: ...

    @property
    def scores(self) -> Sequence[float] | None: ...

    @property
    def word_results(
        self,
    ) -> Sequence[Sequence[tuple[str, float, Sequence[Sequence[float]]]]] | None: ...


class _Engine(Protocol):
    """Fragment interfejsu `rapidocr.RapidOCR`, z którego korzysta adapter."""

    def __call__(
        self,
        image: object,
        *,
        use_det: bool,
        use_cls: bool,
        use_rec: bool,
        return_word_box: bool,
    ) -> _EngineOutput: ...


EngineFactory = Callable[[dict[str, object]], _Engine]


def _load_rapidocr(params: dict[str, object]) -> _Engine:
    module = importlib.import_module("rapidocr")
    engine: _Engine = module.RapidOCR(params=params)
    return engine


def _enclosing(points: Sequence[Sequence[float]]) -> Bbox:
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _unrotate(bbox: Bbox, angle: int, width: int, height: int) -> Bbox:
    """Przenosi prostokąt z obrazu obróconego o `angle` stopni wstecz do obrazu wejściowego.

    `width` i `height` to rozmiar obrazu wejściowego (przed obrotem).
    """
    x0, y0, x1, y1 = bbox
    if angle == 90:
        return (width - y1, x0, width - y0, x1)
    if angle == 180:
        return (width - x1, height - y1, width - x0, height - y0)
    if angle == 270:
        return (y0, height - x1, y1, height - x0)
    return bbox


class RapidOcr:
    """Adapter `rapidocr` z jawną liczbą wątków i limitem dłuższego boku w pikselach."""

    name = "rapidocr"

    def __init__(
        self,
        *,
        threads: int = 4,
        max_side: int = 2000,
        engine_factory: EngineFactory = _load_rapidocr,
    ) -> None:
        if threads < 1:
            raise ValueError("threads musi być co najmniej 1")
        if max_side < _MIN_MAX_SIDE:
            raise ValueError(f"max_side musi być co najmniej {_MIN_MAX_SIDE} px")
        self._params: dict[str, object] = {
            # Liczba wątków jawnie: domyślna wartość onnxruntime zajmuje wszystkie rdzenie.
            "EngineConfig.onnxruntime.intra_op_num_threads": threads,
            "EngineConfig.onnxruntime.inter_op_num_threads": 1,
            "Global.max_side_len": max_side,
            "Global.log_level": "warning",
        }
        self._engine_factory = engine_factory
        self._engine: _Engine | None = None

    def _get_engine(self) -> _Engine:
        if self._engine is None:
            try:
                self._engine = self._engine_factory(self._params)
            except Exception as error:
                # Brak pakietu, wag albo biblioteki: nazwa klasy wystarcza do diagnozy.
                raise ProcessingError(
                    "ocr_unavailable", f"OCR nie startuje ({type(error).__name__})"
                ) from None
        return self._engine

    def _run(self, image: Image.Image, *, recognize: bool) -> _EngineOutput:
        numpy = importlib.import_module("numpy")
        engine = self._get_engine()
        try:
            return engine(
                numpy.asarray(image),
                use_det=True,
                use_cls=recognize,
                use_rec=recognize,
                return_word_box=recognize,
            )
        except Exception as error:
            raise ProcessingError("ocr_error", f"błąd OCR ({type(error).__name__})") from None

    @staticmethod
    def _lines(output: _EngineOutput) -> tuple[OcrLine, ...]:
        # Silnik zwraca tablice numpy albo krotki; `or` na tablicy zgłasza wyjątek.
        texts: Sequence[str] = () if output.txts is None else output.txts
        scores: Sequence[float] = () if output.scores is None else output.scores
        boxes: Sequence[Sequence[Sequence[float]]] = () if output.boxes is None else output.boxes
        word_results = () if output.word_results is None else output.word_results
        lines: list[OcrLine] = []
        for index, (box, text, score) in enumerate(zip(boxes, texts, scores, strict=True)):
            if not str(text).strip():
                continue
            raw_words = word_results[index] if index < len(word_results) else ()
            words = tuple(
                OcrWord(str(word_text), float(word_score), _enclosing(word_box))
                for word_text, word_score, word_box in raw_words
                if str(word_text).strip()
            )
            lines.append(OcrLine(str(text), float(score), _enclosing(box), words))
        return tuple(lines)

    @staticmethod
    def _score(lines: tuple[OcrLine, ...]) -> float:
        """Im więcej pewnie odczytanych liter i cyfr, tym lepsza orientacja."""
        return sum(
            line.confidence * sum(1 for char in line.text if char.isalnum()) for line in lines
        )

    def detect_rotation(self, image: Image.Image) -> int:
        """Kąt (0/90/180/270), o który trzeba obrócić obraz, żeby tekst stał prosto.

        Najpierw sama detekcja pól tekstu na pomniejszeniu: pola wyższe niż szersze
        oznaczają tekst pionowy. Z dwóch pozostałych orientacji wygrywa ta, w której
        OCR odczytuje więcej znaków z większą pewnością (z marginesem na korzyść pierwszej).
        """
        probe = image.copy()
        probe.thumbnail((_ROTATION_PROBE_SIDE, _ROTATION_PROBE_SIDE))
        boxes = self._run(probe, recognize=False).boxes
        if boxes is None or len(boxes) == 0:
            return 0
        vertical = 0
        for box in boxes:
            x0, y0, x1, y1 = _enclosing(box)
            if y1 - y0 > x1 - x0:
                vertical += 1
        candidates = (90, 270) if vertical > len(boxes) / 2 else (0, 180)
        scores = [
            self._score(self._lines(self._run(self._rotated(probe, angle), recognize=True)))
            for angle in candidates
        ]
        return candidates[1] if scores[1] > scores[0] * _ROTATION_MARGIN else candidates[0]

    @staticmethod
    def _rotated(image: Image.Image, angle: int) -> Image.Image:
        return image.rotate(angle, expand=True) if angle else image

    def recognize(self, image: Image.Image) -> OcrResult:
        """Odczytuje stronę; wynik w pikselach obrazu `image` (przed obrotem korygującym)."""
        rgb = image.convert("RGB")
        width, height = rgb.size
        rotation = self.detect_rotation(rgb)
        output = self._run(self._rotated(rgb, rotation), recognize=True)
        lines = tuple(
            OcrLine(
                line.text,
                line.confidence,
                _unrotate(line.bbox, rotation, width, height),
                tuple(
                    OcrWord(
                        word.text, word.confidence, _unrotate(word.bbox, rotation, width, height)
                    )
                    for word in line.words
                ),
            )
            for line in self._lines(output)
        )
        return OcrResult(lines=lines, rotation=rotation, width_px=width, height_px=height)
