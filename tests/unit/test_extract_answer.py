"""Testy schematu odpowiedzi LLM: akceptacja, tolerancja pól pomocniczych, naruszenia."""

from __future__ import annotations

import pytest
from odwolania2json.errors import ProcessingError
from odwolania2json.extract.answer import AnswerField, parse_answer


def test_valid_answer_is_parsed() -> None:
    parsed = parse_answer(
        {
            "class": "bank_transfer",
            "fields": [
                {"field": "/przelew_bankowy/kwota", "value": 15000, "quote": "15 000", "page": 1}
            ],
        }
    )

    assert parsed.label == "bank_transfer"
    assert parsed.fields == (
        AnswerField(field="/przelew_bankowy/kwota", value=15000, quote="15 000", page=1),
    )


@pytest.mark.parametrize("label", ["foreign", "ambiguous"])
def test_classes_without_fields_accept_missing_or_null_list(label: str) -> None:
    assert parse_answer({"class": label}).fields == ()
    assert parse_answer({"class": label, "fields": None}).fields == ()
    assert parse_answer({"class": label, "fields": []}).label == label


def test_explicit_null_value_is_kept_as_none() -> None:
    parsed = parse_answer({"class": "appeal", "fields": [{"field": "/a", "value": None}]})

    assert parsed.fields[0].value is None
    assert (parsed.fields[0].quote, parsed.fields[0].page) == (None, None)


def test_helper_fields_of_wrong_type_become_none() -> None:
    parsed = parse_answer(
        {
            "class": "appeal",
            "fields": [{"field": "/a", "value": "x", "quote": 5, "page": "2"}],
            "komentarz": "nadmiarowy klucz",
        }
    )

    assert (parsed.fields[0].quote, parsed.fields[0].page) == (None, None)


def test_boolean_page_is_not_a_page_number() -> None:
    parsed = parse_answer(
        {"class": "appeal", "fields": [{"field": "/a", "value": 1, "page": True}]}
    )

    assert parsed.fields[0].page is None


def test_non_scalar_value_is_accepted_for_later_flagging() -> None:
    parsed = parse_answer({"class": "appeal", "fields": [{"field": "/a", "value": {"x": 1}}]})

    assert parsed.fields[0].value == {"x": 1}


@pytest.mark.parametrize(
    ("data", "violation"),
    [
        ({"fields": []}, "class_out_of_vocabulary"),
        ({"class": "wyrok", "fields": []}, "class_out_of_vocabulary"),
        ({"class": None, "fields": []}, "class_out_of_vocabulary"),
        ({"class": "appeal"}, "fields_not_list"),
        ({"class": "appeal", "fields": None}, "fields_not_list"),
        ({"class": "appeal", "fields": {"a": 1}}, "fields_not_list"),
        ({"class": "foreign", "fields": "brak"}, "fields_not_list"),
        ({"class": "appeal", "fields": ["tekst"]}, "field_item_invalid"),
        ({"class": "appeal", "fields": [{"value": 1}]}, "field_item_invalid"),
        ({"class": "appeal", "fields": [{"field": 7, "value": 1}]}, "field_item_invalid"),
        ({"class": "appeal", "fields": [{"field": "/a"}]}, "field_item_invalid"),
    ],
)
def test_schema_violation_is_reported_with_code(data: dict[str, object], violation: str) -> None:
    with pytest.raises(ProcessingError) as caught:
        parse_answer(data)

    assert caught.value.code == "llm_invalid_response"
    assert caught.value.message == f"odpowiedź modelu poza schematem: {violation}"


def test_violation_message_never_quotes_model_output() -> None:
    with pytest.raises(ProcessingError) as caught:
        parse_answer({"class": "TAJNA-TRESC-DOKUMENTU", "fields": []})

    assert "TAJNA" not in str(caught.value)
