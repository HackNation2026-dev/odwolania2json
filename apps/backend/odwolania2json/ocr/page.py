"""Przekłada wynik dostawcy OCR na linie wymagane przez silnik ekstrakcji."""

from __future__ import annotations

from typing import TYPE_CHECKING

from odwolania2json.extract.ports import OcrLine, OcrWord

if TYPE_CHECKING:
    from PIL import Image

    from .rapid import OcrProvider


class PageOcrAdapter:
    """Zachowuje kolejność i współrzędne pikselowe zwrócone przez dostawcę."""

    def __init__(self, provider: OcrProvider) -> None:
        self._provider = provider

    def recognize(self, image: Image.Image) -> tuple[OcrLine, ...]:
        return tuple(
            OcrLine(
                text=line.text,
                bbox=line.bbox,
                words=tuple(
                    OcrWord(text=word.text, bbox=word.bbox, confidence=word.confidence)
                    for word in line.words
                ),
            )
            for line in self._provider.recognize(image).lines
        )
