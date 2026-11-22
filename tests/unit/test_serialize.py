"""Testy serializera wyniku: szablon klasy, jawne `null`, kolejność kluczy, typy liści."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest
from odwolania2json.loader import MATERIALS_DIR, load_case_references, load_reference_json
from odwolania2json.serialize import (
    TEMPLATES,
    build_values,
    leaf_pointers,
    serialize,
)
from odwolania2json_contracts.models import Odwolanie, Pelnomocnictwo, Przelew

PATTERN_DIR = MATERIALS_DIR / "oczekiwane-json"
PATTERN_FILES = {
    "odwolanie": "odwolanie.json",
    "pelnomocnictwo": "pelnomocnictwo.json",
    "przelew": "przelew.json",
}
CONTRACT_MODELS = {"odwolanie": Odwolanie, "pelnomocnictwo": Pelnomocnictwo, "przelew": Przelew}


def _dump(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _keys_in_order(node: object) -> list[str]:
    """Klucze w kolejności wystąpienia (listy: pierwszy element)."""
    if isinstance(node, dict):
        keys: list[str] = []
        for key, value in node.items():
            keys.append(key)
            keys.extend(_keys_in_order(value))
        return keys
    if isinstance(node, list) and node:
        return _keys_in_order(node[0])
    return []


def test_round_trip_reproduces_all_180_reference_files_byte_for_byte() -> None:
    references = [ref for ref in load_case_references() if ref.reference_name is not None]
    assert len(references) == 180
    for ref in references:
        source = load_reference_json(ref)
        payload, flags = serialize(ref.document_class, source)
        assert _dump(payload) == _dump(source), (ref.case_id, ref.input_name)
        assert flags == [], (ref.case_id, ref.input_name)


def test_round_trip_reproduces_uncorrected_reference_files() -> None:
    for ref in load_case_references():
        if ref.reference_name is None:
            continue
        path = Path(MATERIALS_DIR / "dane" / ref.case_id / ref.reference_name)
        source = json.loads(path.read_text(encoding="utf-8"))
        payload, _ = serialize(ref.document_class, source)
        assert _dump(payload) == _dump(source), path


@pytest.mark.parametrize("document_class", sorted(PATTERN_FILES))
def test_template_key_order_matches_organizer_pattern(document_class: str) -> None:
    # Wzorce organizatora nie są poprawnym JSON-em (komentarze, brak przecinka),
    # więc kolejność kluczy czytamy wprost z tekstu.
    text = (PATTERN_DIR / PATTERN_FILES[document_class]).read_text(encoding="utf-8")
    without_comments = "\n".join(line.split("//")[0] for line in text.splitlines())
    pattern_keys = re.findall(r'"([^"]+)"\s*:', without_comments)

    payload, _ = serialize(document_class, {})

    assert _keys_in_order(payload) == pattern_keys


@pytest.mark.parametrize("document_class", sorted(CONTRACT_MODELS))
def test_empty_values_give_explicit_nulls_accepted_by_contract_model(document_class: str) -> None:
    payload, flags = serialize(document_class, {})

    assert flags == []
    CONTRACT_MODELS[document_class].model_validate(payload)


def test_empty_values_keep_one_skeleton_element_in_every_list() -> None:
    payload, _ = serialize("pelnomocnictwo", {})

    assert payload == {
        "mocodawca": [
            {
                "data": {
                    "imie_nazwisko": None,
                    "krs": None,
                    "nazwa": None,
                    "nip": None,
                    "typ": None,
                },
                "podpisujacy": [{"imie_nazwisko": None}],
            }
        ],
        "pelnomocnicy": [{"imie_nazwisko": None, "pesel": None}],
    }


def test_all_null_list_elements_are_not_pruned() -> None:
    values = {"pelnomocnicy": [{"imie_nazwisko": "Anna Nowak"}, {}, {"pesel": "85120133547"}]}

    payload, _ = serialize("pelnomocnictwo", values)

    assert payload["pelnomocnicy"] == [
        {"imie_nazwisko": "Anna Nowak", "pesel": None},
        {"imie_nazwisko": None, "pesel": None},
        {"imie_nazwisko": None, "pesel": "85120133547"},
    ]


def test_key_order_follows_template_not_input() -> None:
    values = {"przelew_bankowy": {"z_rachunku": "1", "kwota": 5, "data_operacji": "2026-01-02"}}

    payload, _ = serialize("przelew", values)

    assert list(payload["przelew_bankowy"]) == [  # type: ignore[call-overload]
        "data_operacji",
        "kwota",
        "na_rachunek",
        "numer_transakcji",
        "tytul",
        "z_rachunku",
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (85120133547, "85120133547"),
        ("85120133547", "85120133547"),
        (None, None),
    ],
)
def test_pesel_is_text_or_null(raw: object, expected: object) -> None:
    payload, flags = serialize("pelnomocnictwo", {"pelnomocnicy": [{"pesel": raw}]})

    assert payload["pelnomocnicy"] == [{"imie_nazwisko": None, "pesel": expected}]
    assert flags == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(200, 200.0), (200.5, 200.5), ("1 234,50 zł", 1234.5), ("200.00", 200.0)],
)
def test_amount_is_a_number(raw: object, expected: float) -> None:
    payload, flags = serialize("przelew", {"przelew_bankowy": {"kwota": raw}})

    kwota = payload["przelew_bankowy"]["kwota"]  # type: ignore[index]
    assert kwota == expected
    assert isinstance(kwota, float)
    assert flags == []


@pytest.mark.parametrize("raw", [math.inf, math.nan, "brak", True, [1], {"a": 1}])
def test_unusable_amount_becomes_null_with_flag(raw: object) -> None:
    payload, flags = serialize("przelew", {"przelew_bankowy": {"kwota": raw}})

    assert payload["przelew_bankowy"]["kwota"] is None  # type: ignore[index]
    assert flags == ["type_mismatch:/przelew_bankowy/kwota"]
    json.dumps(payload, allow_nan=False)


@pytest.mark.parametrize(
    ("raw", "expected", "flagged"),
    [(4, 4, False), ("4", 4, False), (4.0, 4, False), ("cztery", None, True), (4.5, None, True)],
)
def test_integer_leaf(raw: object, expected: object, flagged: bool) -> None:
    payload, flags = serialize("odwolanie", {"OdwolanieKIO": {"czynnosc_powod_id": raw}})

    assert payload["OdwolanieKIO"]["czynnosc_powod_id"] == expected  # type: ignore[index]
    assert (flags == ["type_mismatch:/OdwolanieKIO/czynnosc_powod_id"]) is flagged


def test_identifier_given_as_number_becomes_text() -> None:
    payload, flags = serialize("odwolanie", {"Zamawiajacy": [{"nip": 5540240549, "krs": 54588}]})

    assert payload["Zamawiajacy"] == [
        {
            "krs": "54588",
            "nazwa": None,
            "nip": "5540240549",
            "regon": None,
            "prowadzacy_postepowanie": None,
        }
    ]
    assert flags == []


def test_empty_text_is_null_and_structured_text_is_flagged() -> None:
    payload, flags = serialize(
        "przelew", {"przelew_bankowy": {"tytul": "  ", "numer_transakcji": ["A"]}}
    )

    assert payload["przelew_bankowy"]["tytul"] is None  # type: ignore[index]
    assert payload["przelew_bankowy"]["numer_transakcji"] is None  # type: ignore[index]
    assert flags == ["type_mismatch:/przelew_bankowy/numer_transakcji"]


def test_wrong_container_types_fall_back_to_skeleton_with_flag() -> None:
    payload, flags = serialize(
        "odwolanie",
        {"OdwolanieKIO": "tekst", "Odwolujacy": {"nazwa": "X"}, "Zamawiajacy": ["tekst"]},
    )

    assert payload["OdwolanieKIO"] == dict.fromkeys(TEMPLATES["odwolanie"]["OdwolanieKIO"])  # type: ignore[arg-type]
    assert len(payload["Odwolujacy"]) == 1  # type: ignore[arg-type]
    assert payload["Zamawiajacy"][0]["nazwa"] is None  # type: ignore[index]
    assert flags == [
        "type_mismatch:/OdwolanieKIO",
        "type_mismatch:/Odwolujacy",
        "type_mismatch:/Zamawiajacy/0",
    ]


def test_unknown_keys_are_dropped_with_flag() -> None:
    payload, flags = serialize("przelew", {"przelew_bankowy": {"waluta": "PLN"}, "inne": 1})

    assert "inne" not in payload
    assert "waluta" not in payload["przelew_bankowy"]  # type: ignore[operator]
    assert flags == ["unknown_key:/przelew_bankowy/waluta", "unknown_key:/inne"]


def test_foreign_class_and_unknown_class_serialize_to_empty_object() -> None:
    assert serialize("obcy", {"cokolwiek": 1}) == ({}, [])
    with pytest.raises(KeyError):
        serialize("nieznana", {})


def test_leaf_pointers_list_template_leaves_with_zero_index() -> None:
    assert leaf_pointers("przelew") == [
        "/przelew_bankowy/data_operacji",
        "/przelew_bankowy/kwota",
        "/przelew_bankowy/na_rachunek",
        "/przelew_bankowy/numer_transakcji",
        "/przelew_bankowy/tytul",
        "/przelew_bankowy/z_rachunku",
    ]
    assert "/Odwolujacy/0/pelnomocnik/mail" in leaf_pointers("odwolanie")
    assert "/mocodawca/0/podpisujacy/0/imie_nazwisko" in leaf_pointers("pelnomocnictwo")


def test_build_values_places_pointer_values_and_extends_lists() -> None:
    values, rejected = build_values(
        "pelnomocnictwo",
        [
            ("/mocodawca/0/data/nazwa", "FAMBUD"),
            ("/mocodawca/0/podpisujacy/1/imie_nazwisko", "Jan Kowalski"),
            ("/pelnomocnicy/1/imie_nazwisko", "Anna Nowak"),
        ],
    )

    assert rejected == []
    payload, _ = serialize("pelnomocnictwo", values)
    assert payload["mocodawca"][0]["data"]["nazwa"] == "FAMBUD"  # type: ignore[index]
    assert payload["mocodawca"][0]["podpisujacy"] == [  # type: ignore[index]
        {"imie_nazwisko": None},
        {"imie_nazwisko": "Jan Kowalski"},
    ]
    assert payload["pelnomocnicy"] == [
        {"imie_nazwisko": None, "pesel": None},
        {"imie_nazwisko": "Anna Nowak", "pesel": None},
    ]


@pytest.mark.parametrize(
    "pointer",
    [
        "/przelew_bankowy/waluta",
        "/przelew_bankowy",
        "przelew_bankowy/kwota",
        "/przelew_bankowy/kwota/0",
        "",
        "/",
    ],
)
def test_build_values_rejects_pointers_outside_template(pointer: str) -> None:
    values, rejected = build_values("przelew", [(pointer, 1)])

    assert values == {}
    assert rejected == [pointer]


@pytest.mark.parametrize(
    "pointer",
    ["/Odwolujacy/x/nazwa", "/Odwolujacy/-1/nazwa", "/Odwolujacy/nazwa", "/Odwolujacy/500/nazwa"],
)
def test_build_values_rejects_bad_list_indexes(pointer: str) -> None:
    values, rejected = build_values("odwolanie", [(pointer, "X")])

    assert values == {}
    assert rejected == [pointer]
