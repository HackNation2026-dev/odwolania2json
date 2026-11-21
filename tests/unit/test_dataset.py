"""Testy zamrożonego podziału 60 spraw na część rozwojową i kontrolną."""

import hashlib
import json
from pathlib import Path

import pytest
from odwolania2json.dataset import DATA_SPLIT, load_split
from odwolania2json.loader import MATERIALS_DIR

PODZIAL_SHA256 = "3cf406a84c22424e1555e5a6192cd18f3247a9da6c2fd4d20a8dcc12f0122e2e"
WSZYSTKIE_SPRAWY = frozenset(f"przyklad_{numer:02d}" for numer in range(1, 61))
DANE = MATERIALS_DIR / "dane"


def _sha256(sciezka: Path) -> str:
    return hashlib.sha256(sciezka.read_bytes()).hexdigest()


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


def test_control_side_holds_no_duplicate_of_negative_pdf() -> None:
    negatywy = {_sha256(pdf) for pdf in (DANE / "negatywne").rglob("*.pdf")}

    duplikaty = [
        f"{sprawa}/{pdf.name}"
        for sprawa in sorted(load_split().kontrolny)
        for pdf in (DANE / sprawa).rglob("*.pdf")
        if _sha256(pdf) in negatywy
    ]

    assert duplikaty == []


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
