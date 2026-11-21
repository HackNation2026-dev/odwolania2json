"""Testy zamrożonego podziału 60 spraw na część rozwojową i kontrolną."""

import hashlib
import json
from pathlib import Path

import pytest
from odwolania2json.dataset import DATA_SPLIT, load_split

PODZIAL_SHA256 = "551adfe41f9bdeac960e00f6179df6f5ba836fcdfba43d87cfecff833352dc1a"
WSZYSTKIE_SPRAWY = frozenset(f"przyklad_{numer:02d}" for numer in range(1, 61))


def _zapisz_podzial(sciezka: Path, rozwojowy: list[str], kontrolny: list[str]) -> Path:
    sciezka.write_text(
        json.dumps({"metoda": "test", "rozwojowy": rozwojowy, "kontrolny": kontrolny}),
        encoding="utf-8",
    )
    return sciezka


def test_split_covers_all_60_cases() -> None:
    split = load_split()

    assert len(split.rozwojowy) + len(split.kontrolny) == 60
    assert split.rozwojowy | split.kontrolny == WSZYSTKIE_SPRAWY


def test_split_is_disjoint() -> None:
    split = load_split()

    assert split.rozwojowy.isdisjoint(split.kontrolny)


def test_split_file_frozen() -> None:
    assert hashlib.sha256(DATA_SPLIT.read_bytes()).hexdigest() == PODZIAL_SHA256


def test_load_split_validates_coverage(tmp_path: Path) -> None:
    sciezka = _zapisz_podzial(
        tmp_path / "podzial.json",
        rozwojowy=sorted(WSZYSTKIE_SPRAWY - {"przyklad_05", "przyklad_60"}),
        kontrolny=["przyklad_05"],
    )

    with pytest.raises(ValueError, match="przyklad_60"):
        load_split(sciezka)


def test_load_split_rejects_case_on_both_sides(tmp_path: Path) -> None:
    sciezka = _zapisz_podzial(
        tmp_path / "podzial.json",
        rozwojowy=sorted(WSZYSTKIE_SPRAWY),
        kontrolny=["przyklad_05"],
    )

    with pytest.raises(ValueError, match="przyklad_05"):
        load_split(sciezka)
