"""Podobieństwo tekstów dla pól z progiem zgodności oraz lista tych pól.

Organizator podał próg 80% dla pięciu pól tekstowych, ale nie podał algorytmu
podobieństwa (pytanie U-Q01). Dlatego warianty są wymienne, a domyślny `ratio`
to najprostsza miara edycyjna rapidfuzz. Raport ewaluatora liczy F1 dla każdego
wariantu, żeby pokazać rozrzut wyniku zależny od tej niewiadomej.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, get_args

from rapidfuzz import fuzz

__all__ = [
    "DEFAULT_SIMILARITY_METHOD",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "SIMILARITY_FIELD_PATHS",
    "SIMILARITY_METHODS",
    "SimilarityMethod",
    "similarity",
]

SimilarityMethod = Literal["ratio", "token_sort_ratio", "partial_ratio"]

SIMILARITY_METHODS: tuple[SimilarityMethod, ...] = get_args(SimilarityMethod)
DEFAULT_SIMILARITY_METHOD: SimilarityMethod = "ratio"
DEFAULT_SIMILARITY_THRESHOLD = 0.8

# Jedyne miejsce z listą pól z progiem. Ścieżki to klucze referencyjnych JSON organizatora,
# a indeks listy zapisujemy jako `[]` (np. `Odwolujacy[].nazwa`).
SIMILARITY_FIELD_PATHS: frozenset[str] = frozenset(
    {
        "Odwolujacy[].pelnomocnik.nazwa",  # nazwa firmy pełnomocnika
        "przelew_bankowy.tytul",  # tytuł przelewu
        "Odwolujacy[].nazwa",  # nazwa odwołującego
        "Zamawiajacy[].nazwa",  # nazwa zamawiającego
        "ZamowieniePubliczne.tytul",  # tytuł zamówienia
    }
)

_SCORERS: dict[SimilarityMethod, Callable[[str, str], float]] = {
    "ratio": fuzz.ratio,
    "token_sort_ratio": fuzz.token_sort_ratio,
    "partial_ratio": fuzz.partial_ratio,
}


def similarity(
    left: str, right: str, method: SimilarityMethod = DEFAULT_SIMILARITY_METHOD
) -> float:
    """Podobieństwo w zakresie 0.0–1.0 wybranym wariantem rapidfuzz."""
    return _SCORERS[method](left, right) / 100
