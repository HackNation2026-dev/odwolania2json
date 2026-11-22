"""Testy pipeline'u: tekst stron, normalizacja, para powodu, klasy, błędy LLM."""

from __future__ import annotations

import json

import pytest
from odwolania2json.errors import ProcessingError
from odwolania2json.extract.answer import parse_answer
from odwolania2json.extract.pipeline import (
    REASON_DESCRIPTION_POINTER,
    REASON_ID_POINTER,
    PageText,
    build_extraction,
    document_text,
    enforce_reason_pair,
    extract,
    normalize_value,
)
from odwolania2json.extract.prompt import COMMIT_NOTE, SYSTEM_PROMPT
from odwolania2json.loader import MATERIALS_DIR
from odwolania2json_contracts.powody import APPEAL_REASONS
from support.llm import API_KEY, FakeLlmServer, answer, field

TRANSFER = answer(
    "bank_transfer",
    field("/przelew_bankowy/data_operacji", "9 października 2025 r."),
    field("/przelew_bankowy/kwota", "15 000,00 zł"),
    field("/przelew_bankowy/na_rachunek", "PL 60 1010 1010 0081 3622 3100 0000"),
    field("/przelew_bankowy/numer_transakcji", None),
    field("/przelew_bankowy/tytul", "  WPIS OD ODWOLANIA  "),
    field("/przelew_bankowy/z_rachunku", "50802054600000588874424400"),
)


def _reference_keys(name: str) -> list[str]:
    path = MATERIALS_DIR / "dane" / "przyklad_01" / name
    return list(json.loads(path.read_text(encoding="utf-8")))


def test_document_text_marks_pages_in_order() -> None:
    text = document_text([PageText(1, "Pierwsza\nlinia"), PageText(2, ""), PageText(3, "Trzecia")])

    assert text == "[[strona 1]]\nPierwsza\nlinia\n[[strona 2]]\n\n[[strona 3]]\nTrzecia"


def test_document_text_of_no_pages_is_empty() -> None:
    assert document_text([]) == ""


@pytest.mark.parametrize(
    ("pointer", "value", "expected"),
    [
        ("/Odwolujacy/0/nip", "NIP: 9990678035", ("9990678035", False)),
        ("/Odwolujacy/0/regon", "REGON 999114017", ("999114017", False)),
        ("/Zamawiajacy/0/krs", 9993122884, ("9993122884", False)),
        ("/pelnomocnicy/0/pesel", "44051401458", ("44051401458", False)),
        ("/przelew_bankowy/kwota", "15 000,00 zł", (15000.0, False)),
        ("/przelew_bankowy/kwota", 15000, (15000, False)),
        ("/przelew_bankowy/kwota", 0.5, (0.5, False)),
        ("/przelew_bankowy/data_operacji", "09.10.2025", ("2025-10-09", False)),
        ("/OdwolanieKIO/data", "3 września 2026 roku", ("2026-09-03", False)),
        ("/OdwolanieKIO/czynnosc_dzien", "2026-08-28", ("2026-08-28", False)),
        ("/ZamowieniePubliczne/numer_ted", "2025/S 112-383751", ("383751-2025", False)),
        ("/Odwolujacy/0/nazwa", "Hartica Serwis S.A.", ("Hartica Serwis S.A.", False)),
        ("/Odwolujacy/0/nip", None, (None, False)),
        ("/Odwolujacy/0/nip", "brak numeru", ("brak numeru", True)),
        ("/OdwolanieKIO/data", "wczoraj", ("wczoraj", True)),
        ("/Odwolujacy/0/nip", ["9990678035"], (["9990678035"], True)),
        ("/Odwolujacy/0/przez-pelnomocnika", True, (1, False)),
        ("/Zamawiajacy/0/prowadzacy_postepowanie", False, (0, False)),
        ("/Odwolujacy/0/nazwa", True, (True, False)),
    ],
)
def test_normalize_value(pointer: str, value: object, expected: tuple[object, bool]) -> None:
    assert normalize_value(pointer, value) == expected


def test_account_fields_are_normalized_to_26_digits() -> None:
    for key in ("na_rachunek", "z_rachunku"):
        assert normalize_value(
            f"/przelew_bankowy/{key}", "PL 60 1010 1010 0081 3622 3100 0000"
        ) == ("60101010100081362231000000", False)


def test_reason_pair_valid_id_sets_dictionary_text() -> None:
    items: dict[str, object] = {REASON_ID_POINTER: 11, REASON_DESCRIPTION_POINTER: "Opis (OPZ)"}

    flags = enforce_reason_pair(items)

    assert items == {
        REASON_ID_POINTER: 11,
        REASON_DESCRIPTION_POINTER: "Opis przedmiotu zamówienia (OPZ)",
    }
    assert flags == [f"reason_text_replaced:{REASON_DESCRIPTION_POINTER}"]


def test_reason_pair_matching_text_needs_no_flag() -> None:
    items: dict[str, object] = {
        REASON_ID_POINTER: "2",
        REASON_DESCRIPTION_POINTER: APPEAL_REASONS[2],
    }

    assert enforce_reason_pair(items) == []
    assert items[REASON_ID_POINTER] == 2


def test_reason_pair_id_alone_fills_text() -> None:
    items: dict[str, object] = {REASON_ID_POINTER: 7.0}

    assert enforce_reason_pair(items) == []
    assert items == {REASON_ID_POINTER: 7, REASON_DESCRIPTION_POINTER: APPEAL_REASONS[7]}


def test_reason_pair_text_alone_sets_id_ignoring_case_and_diacritics() -> None:
    items: dict[str, object] = {REASON_DESCRIPTION_POINTER: "DECYZJA O ODRZUCENIU OFERTY"}

    assert enforce_reason_pair(items) == [f"reason_text_replaced:{REASON_DESCRIPTION_POINTER}"]
    assert items == {REASON_ID_POINTER: 1, REASON_DESCRIPTION_POINTER: APPEAL_REASONS[1]}


def test_reason_pair_invalid_id_falls_back_to_text() -> None:
    items: dict[str, object] = {
        REASON_ID_POINTER: 99,
        REASON_DESCRIPTION_POINTER: APPEAL_REASONS[12],
    }

    assert enforce_reason_pair(items) == []
    assert items[REASON_ID_POINTER] == 12


@pytest.mark.parametrize("bad_id", [0, 13, 99, True, "abc", 2.5, [1]])
def test_reason_pair_outside_dictionary_is_flagged_and_kept(bad_id: object) -> None:
    items: dict[str, object] = {REASON_ID_POINTER: bad_id, REASON_DESCRIPTION_POINTER: "Inny powód"}

    assert enforce_reason_pair(items) == [f"reason_pair_invalid:{REASON_ID_POINTER}"]
    assert items == {REASON_ID_POINTER: bad_id, REASON_DESCRIPTION_POINTER: "Inny powód"}


def test_reason_pair_absent_changes_nothing() -> None:
    items: dict[str, object] = {"/OdwolanieKIO/miejscowosc": "Gdańsk"}

    assert enforce_reason_pair(items) == []
    assert items == {"/OdwolanieKIO/miejscowosc": "Gdańsk"}


def test_transfer_payload_follows_reference_structure_and_types() -> None:
    extraction = build_extraction(parse_answer(TRANSFER))

    assert extraction.document_class == "przelew"
    assert extraction.flags == ()
    assert list(extraction.payload) == _reference_keys("przelew.json")
    assert extraction.payload == {
        "przelew_bankowy": {
            "data_operacji": "2025-10-09",
            "kwota": 15000.0,
            "na_rachunek": "60101010100081362231000000",
            "numer_transakcji": None,
            "tytul": "WPIS OD ODWOLANIA",
            "z_rachunku": "50802054600000588874424400",
        }
    }


def test_appeal_payload_has_all_template_keys_and_enforced_reason() -> None:
    extraction = build_extraction(
        parse_answer(
            answer(
                "appeal",
                field("/OdwolanieKIO/czynnosc_powod_id", 2),
                field("/OdwolanieKIO/czynnosc_opis", "wybór oferty"),
                field("/Odwolujacy/0/nazwa", "Alfa S.A."),
                field("/Odwolujacy/1/nazwa", "Beta sp. z o.o."),
                field("/Odwolujacy/0/przez-pelnomocnika", "1"),
                field("/Odwolujacy/0/pelnomocnik/mail", ""),
            )
        )
    )

    payload = extraction.payload
    assert list(payload) == _reference_keys("odwolanie.json")
    kio = payload["OdwolanieKIO"]
    assert isinstance(kio, dict)
    assert kio["czynnosc_powod_id"] == 2
    assert kio["czynnosc_opis"] == "Ogłoszenie wyboru oferty"
    assert kio["data"] is None
    appellants = payload["Odwolujacy"]
    assert isinstance(appellants, list)
    assert [item["nazwa"] for item in appellants] == ["Alfa S.A.", "Beta sp. z o.o."]
    assert appellants[0]["przez-pelnomocnika"] == 1
    assert appellants[0]["pelnomocnik"] == {"imie_nazwisko": None, "nazwa": None, "mail": None}
    assert extraction.flags == (f"reason_text_replaced:{REASON_DESCRIPTION_POINTER}",)


def test_power_of_attorney_payload_keeps_pesel_as_text() -> None:
    extraction = build_extraction(
        parse_answer(
            answer(
                "power_of_attorney",
                field("/pelnomocnicy/0/imie_nazwisko", "Jan Kowalski"),
                field("/pelnomocnicy/0/pesel", 44051401458),
                field("/mocodawca/0/data/nip", "NIP 9990678035"),
            )
        )
    )

    assert extraction.document_class == "pelnomocnictwo"
    assert list(extraction.payload) == _reference_keys("pelnomocnictwo.json")
    assert extraction.payload["pelnomocnicy"] == [
        {"imie_nazwisko": "Jan Kowalski", "pesel": "44051401458"}
    ]


def test_unknown_and_unnormalized_fields_are_flagged_not_blocking() -> None:
    extraction = build_extraction(
        parse_answer(
            answer(
                "bank_transfer",
                field("/przelew_bankowy/kwota", "dużo"),
                field("/przelew_bankowy/z_rachunku", "nie widać"),
                field("/przelew_bankowy/wymyslone", "x"),
                field("/OdwolanieKIO/data", "2026-01-01"),
                field("/przelew_bankowy/tytul", {"zagniezdzone": 1}),
            )
        )
    )

    transfer = extraction.payload["przelew_bankowy"]
    assert isinstance(transfer, dict)
    # Wartość bez normalizacji zostaje (flaga), a typ niezgodny z szablonem daje null.
    assert transfer["z_rachunku"] == "nie widać"
    assert transfer["kwota"] is None
    assert transfer["tytul"] is None
    assert set(extraction.flags) == {
        "unnormalized:/przelew_bankowy/kwota",
        "unnormalized:/przelew_bankowy/z_rachunku",
        "unknown_field:/przelew_bankowy/wymyslone",
        "unknown_field:/OdwolanieKIO/data",
        "type_mismatch:/przelew_bankowy/kwota",
        "type_mismatch:/przelew_bankowy/tytul",
    }


def test_last_duplicate_field_wins() -> None:
    extraction = build_extraction(
        parse_answer(
            answer(
                "bank_transfer",
                field("/przelew_bankowy/tytul", "pierwszy"),
                field("/przelew_bankowy/tytul", "drugi"),
            )
        )
    )

    assert extraction.payload["przelew_bankowy"]["tytul"] == "drugi"  # type: ignore[index]


def test_foreign_document_gives_empty_payload_even_with_fields() -> None:
    extraction = build_extraction(parse_answer(answer("foreign", field("/a", "b"))))

    assert (extraction.document_class, extraction.payload, extraction.flags) == ("obcy", {}, ())


def test_extract_makes_exactly_one_call_with_prompt_and_text() -> None:
    server = FakeLlmServer([TRANSFER])

    extraction = extract("[[strona 1]]\nPotwierdzenie przelewu", server.client())

    assert extraction.document_class == "przelew"
    assert len(server.requests) == 1
    assert server.requests[0]["system"] == SYSTEM_PROMPT
    assert server.user_texts == ["[[strona 1]]\nPotwierdzenie przelewu"]
    assert server.requests[0]["temperature"] == 0.0


def test_ambiguous_answer_gets_one_commit_call_and_best_class() -> None:
    server = FakeLlmServer([answer("ambiguous"), TRANSFER])

    extraction = extract("tekst", server.client())

    assert extraction.document_class == "przelew"
    assert extraction.flags == ("class_ambiguous",)
    assert server.user_texts == ["tekst", "tekst" + COMMIT_NOTE]


def test_twice_ambiguous_gives_no_class_and_empty_payload() -> None:
    server = FakeLlmServer([answer("ambiguous"), answer("ambiguous")])

    extraction = extract("tekst", server.client())

    assert (extraction.document_class, extraction.payload) == (None, {})
    assert extraction.flags == ("class_ambiguous",)
    assert len(server.requests) == 2


def test_ambiguous_then_foreign_is_foreign_with_flag() -> None:
    server = FakeLlmServer([answer("ambiguous"), answer("foreign")])

    extraction = extract("tekst", server.client())

    assert (extraction.document_class, extraction.payload) == ("obcy", {})
    assert extraction.flags == ("class_ambiguous",)


def test_invalid_answer_is_retried_once_with_shorter_output_limit() -> None:
    server = FakeLlmServer(["to nie jest JSON", TRANSFER])

    extraction = extract("tekst", server.client(max_output_tokens=9000, retry_output_tokens=3000))

    assert extraction.document_class == "przelew"
    assert [body["max_tokens"] for body in server.requests] == [9000, 3000]


def test_answer_outside_schema_is_retried_then_fails_explicitly() -> None:
    server = FakeLlmServer([{"class": "wyrok", "fields": []}, {"class": "appeal"}])

    with pytest.raises(ProcessingError) as caught:
        extract("tekst", server.client())

    assert caught.value.code == "llm_invalid_response"
    assert len(server.requests) == 2


def test_fenced_json_answer_is_accepted() -> None:
    server = FakeLlmServer(["```json\n" + json.dumps(TRANSFER) + "\n```"])

    assert extract("tekst", server.client()).document_class == "przelew"


@pytest.mark.parametrize(
    ("status", "code", "calls"),
    [(401, "llm_authorization", 1), (403, "llm_authorization", 1), (429, "llm_rate_limit", 4)],
)
def test_http_failures_surface_as_processing_errors_without_key(
    status: int, code: str, calls: int
) -> None:
    server = FakeLlmServer([status] * calls)

    with pytest.raises(ProcessingError) as caught:
        extract("tekst", server.client())

    assert caught.value.code == code
    assert len(server.requests) == calls
    assert API_KEY not in str(caught.value)
    assert API_KEY not in repr(caught.value)


def test_server_error_is_retried_and_then_succeeds() -> None:
    server = FakeLlmServer([500, 502, TRANSFER])

    assert extract("tekst", server.client()).document_class == "przelew"
    assert len(server.requests) == 3
