"""Porty silnika ekstrakcji: dostawca OCR strony i klient LLM zwracający JSON.

Silnik zależy od tych protokołów, a nie od konkretnych bibliotek: adapter OCR
(np. `rapidocr`) i klient HTTP LLM są wstrzykiwane, więc testy używają atrap,
a brak OCR nie blokuje dokumentów tekstowych.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from PIL import Image as PilImage

    from odwolania2json.llm.client import Image

__all__ = ["JsonLlm", "OcrLine", "OcrWord", "PageOcr", "PixelBox"]

# Obrys w pikselach obrazu przekazanego do OCR: (x0, y0, x1, y1), początek w lewym
# górnym rogu, x w prawo, y w dół. Na punkty strony przelicza go silnik (zna skalę renderu).
type PixelBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class OcrWord:
    """Słowo rozpoznane przez OCR; `confidence` w zakresie 0–1 albo `None`."""

    text: str
    bbox: PixelBox
    confidence: float | None = None


@dataclass(frozen=True)
class OcrLine:
    """Linia tekstu w kolejności czytania wraz ze słowami, z których powstała."""

    text: str
    bbox: PixelBox
    words: tuple[OcrWord, ...] = ()


@runtime_checkable
class PageOcr(Protocol):
    """Dostawca OCR jednej strony (architektura §4.2).

    Kontrakt:
    - `image` to obraz RGB całej strony po `/Rotate`, dłuższy bok ok. 2000 px (E03);
    - wynik to linie w kolejności czytania; obrysy linii i słów są w pikselach
      przekazanego obrazu, także gdy dostawca wewnętrznie obraca obraz (90/180/270);
    - pusta strona to pusta sekwencja, nie błąd;
    - awaria to `ProcessingError` z kodem `ocr_unavailable` (brak silnika lub wag)
      albo `ocr_error` (błąd rozpoznania); komunikat bez treści dokumentu.
    """

    def recognize(self, image: PilImage.Image) -> Sequence[OcrLine]: ...


class JsonLlm(Protocol):
    """Klient LLM zwracający obiekt JSON sprawdzony przez `validate`.

    Zgodny z `LlmClient.complete_json`: odpowiedź poza schematem (`validate`
    zgłasza `llm_invalid_response`) dostaje jedno ponowienie z krótszym limitem
    wyjścia, a drugie niepowodzenie kończy się `ProcessingError`.
    """

    def complete_json[T](
        self,
        system: str,
        user: str,
        images: list[Image] | None,
        validate: Callable[[dict[str, object]], T],
    ) -> T: ...
