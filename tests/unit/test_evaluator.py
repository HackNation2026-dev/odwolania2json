"""Testy ewaluatora TP/TN/FP/FN i F1.

Oczekiwane wartości są policzone ręcznie na małych przykładach, a nie wyprowadzone
z implementacji, żeby test nie powtarzał tej samej logiki co kod.
"""

from __future__ import annotations

import pytest
from odwolania2json.evaluator import (
    ClassTotals,
    FieldOutcome,
    compare_document,
    evaluate_document,
    summarize,
)
from odwolania2json.loader import CaseReference, DocumentClass


def _case(document_class: DocumentClass = "przelew") -> CaseReference:
    return CaseReference(
        case_id="przyklad_1",
        input_name="potwierdzenie_przelewu.pdf",
        document_class=document_class,
        reference_name="przelew.json",
    )


def _outcomes(
    outcomes: list[FieldOutcome],
) -> list[tuple[str, str]]:
    return sorted((o.path, o.verdict) for o in outcomes)


def test_identical_documents_all_tp() -> None:
    dokument = {"przelew_bankowy": {"kwota": 200.0, "na_rachunek": "PL01"}}

    outcomes = compare_document(dokument, dokument)

    assert _outcomes(outcomes) == [
        ("przelew_bankowy.kwota", "tp"),
        ("przelew_bankowy.na_rachunek", "tp"),
    ]


def test_matching_present_value_is_tp_and_both_absent_is_tn() -> None:
    predicted: dict[str, object] = {"kwota": 200.0, "tytul": None}
    reference: dict[str, object] = {"kwota": 200.0, "tytul": None}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("kwota", "tp"), ("tytul", "tn")]


def test_wrong_value_is_fp_and_fn_not_tn() -> None:
    predicted = {"przelew_bankowy": {"kwota": 100.0}}
    reference = {"przelew_bankowy": {"kwota": 200.0}}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [
        ("przelew_bankowy.kwota", "fn"),
        ("przelew_bankowy.kwota", "fp"),
    ]


def test_missing_field_is_fn() -> None:
    predicted: dict[str, object] = {"przelew_bankowy": {}}
    reference = {"przelew_bankowy": {"kwota": 200.0}}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("przelew_bankowy.kwota", "fn")]


def test_extra_field_is_fp() -> None:
    predicted = {"dodatkowe": "x"}
    reference: dict[str, object] = {}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("dodatkowe", "fp")]


def test_both_missing_is_tn() -> None:
    predicted: dict[str, object] = {"kwota": None}
    reference: dict[str, object] = {}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("kwota", "tn")]


def test_lists_matched_by_content() -> None:
    predicted = {"osoby": ["b", "c"]}
    reference = {"osoby": ["a", "b"]}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [
        ("osoby", "fn"),
        ("osoby", "fp"),
        ("osoby", "tp"),
    ]


def test_f1_formula_hand_computed() -> None:
    totals = ClassTotals(tp=2, tn=0, fp=1, fn=1)

    assert totals.f1 == pytest.approx(2 * 2 / (2 * 2 + 1 + 1), abs=1e-9)


def test_f1_zero_when_denominator_zero() -> None:
    totals = ClassTotals(tp=0, tn=3, fp=0, fn=0)

    assert totals.f1 == 0.0


def test_classification_verdict() -> None:
    metrics = evaluate_document(
        _case("obcy"),
        predicted={},
        reference={},
        predicted_class="przelew",
    )

    assert metrics.classification == "fn"


def test_obcy_matched_class_is_classification_tp() -> None:
    metrics = evaluate_document(
        _case("obcy"),
        predicted={},
        reference={},
        predicted_class="obcy",
    )

    assert metrics.classification == "tp"


def test_bool_versus_int_is_field_error() -> None:
    predicted: dict[str, object] = {"flaga": 1}
    reference: dict[str, object] = {"flaga": True}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("flaga", "fn"), ("flaga", "fp")]


def test_summarize_report_shape() -> None:
    metrics = [
        evaluate_document(_case("przelew"), {"kwota": 1}, {"kwota": 1}, "przelew"),
        evaluate_document(_case("obcy"), {}, {}, "przelew"),
    ]

    report = summarize(metrics)

    assert set(report) == {"totals", "per_class", "per_document", "classification"}
    assert report["totals"]["tp"] == 1
    assert report["totals"]["tn"] == 0
    assert report["classification"]["tp"] == 1
    assert report["classification"]["fp"] == 1
    assert report["classification"]["fn"] == 1
