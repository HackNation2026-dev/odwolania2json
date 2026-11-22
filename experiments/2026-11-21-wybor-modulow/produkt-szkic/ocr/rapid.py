"""OCR stron skanowych: protokół `OcrProvider` i adapter `rapidocr` (onnxruntime, CPU).

Ustalenia z E03: render o dłuższym boku ok. 2000 px, wykrywanie obrotu 90/180/270
przed rozpoznaniem, **bez** prostowania skosu i **bez** binaryzacji (oba szkodziły).
Silnik ładuje się leniwie i raz na proces; brak pakietu albo wag to jawny błąd
`ocr_unavailable`, a nie pusty tekst.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from PIL import Image

from odwolania2json.errors import ProcessingError

__all__ = [
    "OcrLine",
    "OcrProvider",
    "OcrResult",
    "RapidOcr",
    "UnavailableOcr",
]

_ROTATION_PROBE_SIDE = 1000


@dataclass(frozen=True)
class OcrLine:
    """Linia rozpoznana przez OCR z pewnością silnika."""

    text: str
    confidence: float


@dataclass(frozen=True)
class OcrResult:
    """Wynik OCR strony; `rotation` to obrót obrazu (stopnie), przy którym czytano."""

    lines: tuple[OcrLine, ...]
    rotation: int

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)


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
    """Fragment wyniku `rapidocr`, z którego korzysta adapter."""

    @property
    def boxes(self) -> Sequence[Sequence[Sequence[float]]] | None: ...

    @property
    def txts(self) -> Sequence[str] | None: ...

    @property
    def scores(self) -> Sequence[float] | None: ...


class _Engine(Protocol):
    def __call__(
        self, image: object, *, use_det: bool, use_cls: bool, use_rec: bool
    ) -> _EngineOutput: ...


EngineFactory = Callable[[dict[str, object]], _Engine]


def _load_rapidocr(params: dict[str, object]) -> _Engine:
    module = importlib.import_module("rapidocr")
    engine: _Engine = module.RapidOCR(params=params)
    return engine


class RapidOcr:
    """Adapter `rapidocr` z jawną liczbą wątków i limitem boku obrazu."""

    name = "rapidocr"

    def __init__(
        self,
        *,
        threads: int = 4,
        max_side: int = 2000,
        engine_factory: EngineFactory = _load_rapidocr,
    ) -> None:
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
            return engine(numpy.asarray(image), use_det=True, use_cls=recognize, use_rec=recognize)
        except Exception as error:
            raise ProcessingError("ocr_error", f"błąd OCR ({type(error).__name__})") from None

    @staticmethod
    def _lines(output: _EngineOutput) -> tuple[OcrLine, ...]:
        texts = output.txts or ()
        scores = output.scores or ()
        return tuple(
            OcrLine(text=str(text), confidence=float(score))
            for text, score in zip(texts, scores, strict=True)
            if str(text).strip()
        )

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
        OCR odczytuje więcej znaków z większą pewnością.
        """
        probe = image.copy()
        probe.thumbnail((_ROTATION_PROBE_SIDE, _ROTATION_PROBE_SIDE))
        boxes = self._run(probe, recognize=False).boxes
        if boxes is None or len(boxes) == 0:
            return 0
        vertical = 0
        for box in boxes:
            xs = [float(point[0]) for point in box]
            ys = [float(point[1]) for point in box]
            if max(ys) - min(ys) > max(xs) - min(xs):
                vertical += 1
        candidates = (90, 270) if vertical > len(boxes) / 2 else (0, 180)
        scores = [
            self._score(self._lines(self._run(self._rotated(probe, angle), recognize=True)))
            for angle in candidates
        ]
        return candidates[1] if scores[1] > scores[0] else candidates[0]

    @staticmethod
    def _rotated(image: Image.Image, angle: int) -> Image.Image:
        return image.rotate(angle, expand=True) if angle else image

    def recognize(self, image: Image.Image) -> OcrResult:
        rgb = image.convert("RGB")
        rotation = self.detect_rotation(rgb)
        output = self._run(self._rotated(rgb, rotation), recognize=True)
        return OcrResult(lines=self._lines(output), rotation=rotation)
