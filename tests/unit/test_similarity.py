"""Testy podobieństwa tekstów i listy pól z progiem."""

from __future__ import annotations

import pytest
from odwolania2json.similarity import (
    DEFAULT_SIMILARITY_METHOD,
    DEFAULT_SIMILARITY_THRESHOLD,
    SIMILARITY_FIELD_PATHS,
    SIMILARITY_METHODS,
    similarity,
)


def test_defaults_match_organizer_threshold() -> None:
    assert DEFAULT_SIMILARITY_METHOD == "ratio"
    assert DEFAULT_SIMILARITY_THRESHOLD == 0.8
    assert SIMILARITY_METHODS == ("ratio", "token_sort_ratio", "partial_ratio")


def test_five_fuzzy_fields_use_reference_json_keys() -> None:
    expected = {
        "Odwolujacy[].pelnomocnik.nazwa",
        "przelew_bankowy.tytul",
        "Odwolujacy[].nazwa",
        "Zamawiajacy[].nazwa",
        "ZamowieniePubliczne.tytul",
    }
    assert expected == SIMILARITY_FIELD_PATHS


@pytest.mark.parametrize("method", SIMILARITY_METHODS)
def test_identical_texts_have_full_similarity(method: str) -> None:
    assert similarity("Kancelaria Adwokacka", "Kancelaria Adwokacka", method) == 1.0  # type: ignore[arg-type]  # parametr z krotki metod


def test_ratio_values_are_hand_computed() -> None:
    assert similarity("abcde", "abcdX") == pytest.approx(0.8)
    assert similarity("abc", "xyz") == 0.0


def test_token_sort_ignores_word_order_and_partial_ratio_matches_substring() -> None:
    assert similarity("Alfa Beta", "Beta Alfa", "token_sort_ratio") == 1.0
    assert similarity("Alfa", "Alfa Beta Gamma", "partial_ratio") == 1.0
    assert similarity("Alfa", "Alfa Beta Gamma", "ratio") < 0.8
