"""Testy loadera 60 spraw organizatora.

Dane pochodzą z `docs/02-materialy/organizator-uzp`. Loader jest tylko do odczytu:
testy pilnują, że pliki materiałów nie zmieniają się po wywołaniach.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from odwolania2json.loader import (
    CORRECTIONS_DIR,
    MATERIALS_DIR,
    CaseReference,
    MaterialsNotFoundError,
    input_to_reference_name,
    load_case_references,
    load_reference_json,
    result_name_for,
)

POPRAWIONE_SPRAWY = ("przyklad_19", "przyklad_23", "przyklad_25", "przyklad_44", "przyklad_55")
OPIS_PO_POPRAWCE = "Odpowiedzi/wyjaśnienia do SWZ"


def _sha256_wszystkich_plikow(katalog: Path) -> dict[str, str]:
    return {
        str(plik.relative_to(katalog)): hashlib.sha256(plik.read_bytes()).hexdigest()
        for plik in sorted(katalog.rglob("*"))
        if plik.is_file()
    }


def _referencja_odwolania(case_id: str) -> CaseReference:
    return CaseReference(
        case_id=case_id,
        input_name="odwolanie.pdf",
        document_class="odwolanie",
        reference_name="odwolanie.json",
    )


def test_loads_all_60_cases_with_three_classes():
    refs = load_case_references()
    pozytywne = [ref for ref in refs if ref.document_class != "obcy"]

    assert len(pozytywne) == 180
    assert len({ref.case_id for ref in pozytywne}) == 60
    for case_id in {ref.case_id for ref in pozytywne}:
        klasy = sorted(ref.document_class for ref in pozytywne if ref.case_id == case_id)
        assert klasy == ["odwolanie", "pelnomocnictwo", "przelew"]


def test_negatives_are_foreign_documents():
    negatywne = [ref for ref in load_case_references() if ref.document_class == "obcy"]

    katalog_negatywne = MATERIALS_DIR / "dane" / "negatywne"
    assert len(negatywne) == len(list(katalog_negatywne.glob("*.pdf")))
    assert negatywne
    for ref in negatywne:
        assert ref.document_class == "obcy"
        assert ref.reference_name is None


def test_loader_applies_organizer_corrections():
    for case_id in POPRAWIONE_SPRAWY:
        ref = _referencja_odwolania(case_id)

        dane = load_reference_json(ref)

        assert dane["OdwolanieKIO"]["czynnosc_opis"] == OPIS_PO_POPRAWCE


def test_missing_materials_dir_raises_instead_of_empty_list(tmp_path: Path):
    with pytest.raises(MaterialsNotFoundError, match="dane"):
        load_case_references(tmp_path / "brak")


def test_missing_negatives_dir_raises_instead_of_silent_skip(tmp_path: Path):
    (tmp_path / "dane").mkdir()

    with pytest.raises(MaterialsNotFoundError, match="negatywne"):
        load_case_references(tmp_path, CORRECTIONS_DIR)


def test_loader_maps_transfer_confirmation():
    assert input_to_reference_name("potwierdzenie_przelewu.pdf") == "przelew.json"


def test_result_name_follows_input():
    assert result_name_for("potwierdzenie_przelewu.pdf") == "potwierdzenie_przelewu.json"
    assert result_name_for("przykład odwolanie.pdf") == "przykład odwolanie.json"


def test_loader_does_not_modify_originals():
    przed = _sha256_wszystkich_plikow(MATERIALS_DIR)

    refs = load_case_references(MATERIALS_DIR, CORRECTIONS_DIR)
    for ref in refs:
        load_reference_json(ref, MATERIALS_DIR, CORRECTIONS_DIR)

    assert _sha256_wszystkich_plikow(MATERIALS_DIR) == przed


def test_obcy_reference_is_empty_dict():
    obcy = next(ref for ref in load_case_references() if ref.document_class == "obcy")

    assert load_reference_json(obcy) == {}
