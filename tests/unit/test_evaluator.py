"""Testy ewaluatora TP/TN/FP/FN i F1.

Oczekiwane wartości są policzone ręcznie na małych przykładach, a nie wyprowadzone
z implementacji, żeby test nie powtarzał tej samej logiki co kod.
"""

from __future__ import annotations

import pytest
from odwolania2json.evaluator import (
    ClassTotals,
    EvalConfig,
    EvaluatedDocument,
    FieldOutcome,
    compare_document,
    evaluate_document,
    evaluate_variants,
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


def test_wrong_value_is_only_fp_without_extra_fn() -> None:
    predicted = {"przelew_bankowy": {"kwota": 100.0}}
    reference = {"przelew_bankowy": {"kwota": 200.0}}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("przelew_bankowy.kwota", "fp")]


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

    # `b` zgodne (indeks referencji 1), `c` sparowane z `a` jako błędna wartość: tylko FP.
    assert _outcomes(outcomes) == [("osoby[0]", "fp"), ("osoby[1]", "tp")]


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

    assert _outcomes(outcomes) == [("flaga", "fp")]


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


def _counts(outcomes: list[FieldOutcome]) -> dict[str, int]:
    return {v: sum(1 for o in outcomes if o.verdict == v) for v in ("tp", "tn", "fp", "fn")}


def test_wrong_value_fp_fn_variant_adds_fn() -> None:
    config = EvalConfig(wrong_value="fp_fn")

    outcomes = compare_document({"kwota": 1.0}, {"kwota": 2.0}, config)

    assert _outcomes(outcomes) == [("kwota", "fn"), ("kwota", "fp")]


def test_container_versus_scalar_is_single_wrong_value() -> None:
    outcomes = compare_document({"a": {"x": 1}}, {"a": "tekst"})

    assert _outcomes(outcomes) == [("a", "fp")]


def test_empty_containers_without_outcomes() -> None:
    assert compare_document({"a": {}, "b": []}, {"a": {}, "b": []}) == []


def test_fuzzy_field_above_threshold_is_tp() -> None:
    reference = {"Odwolujacy": [{"nazwa": "Belmoria Rozwiązania S.A."}]}
    predicted = {"Odwolujacy": [{"nazwa": "Belmoria Rozwiązania S.B."}]}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("Odwolujacy[0].nazwa", "tp")]


def test_fuzzy_field_below_threshold_is_fp_only() -> None:
    reference = {"Odwolujacy": [{"nazwa": "Belmoria Rozwiązania S.A."}]}
    predicted = {"Odwolujacy": [{"nazwa": "Aurelink Automatyka S.A."}]}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("Odwolujacy[0].nazwa", "fp")]


def test_fuzzy_threshold_is_inclusive() -> None:
    # ratio("abcde", "abcdX") = 80,0: dokładnie na progu, więc zgodność.
    config = EvalConfig(fuzzy_fields=frozenset({"nazwa"}))

    outcomes = compare_document({"nazwa": "abcdX"}, {"nazwa": "abcde"}, config)

    assert _outcomes(outcomes) == [("nazwa", "tp")]


def test_non_fuzzy_field_requires_exact_match() -> None:
    reference = {"przelew_bankowy": {"numer_transakcji": "CEN2604016344389"}}
    predicted = {"przelew_bankowy": {"numer_transakcji": "CEN2604016344380"}}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [("przelew_bankowy.numer_transakcji", "fp")]


def test_fuzzy_field_ignores_non_string_values() -> None:
    config = EvalConfig(fuzzy_fields=frozenset({"nazwa"}))

    outcomes = compare_document({"nazwa": 1}, {"nazwa": 2}, config)

    assert _outcomes(outcomes) == [("nazwa", "fp")]


def test_similarity_variant_changes_verdict_for_reordered_tokens() -> None:
    fields = frozenset({"nazwa"})
    reference = {"nazwa": "Alfa Beta Gamma Sp. z o.o."}
    predicted = {"nazwa": "Gamma Beta Alfa Sp. z o.o."}

    plain = compare_document(predicted, reference, EvalConfig(fuzzy_fields=fields))
    sorted_tokens = compare_document(
        predicted, reference, EvalConfig(fuzzy_fields=fields, similarity="token_sort_ratio")
    )

    assert _outcomes(plain) == [("nazwa", "fp")]
    assert _outcomes(sorted_tokens) == [("nazwa", "tp")]


def test_list_order_is_irrelevant() -> None:
    reference = {"pelnomocnicy": [{"imie_nazwisko": "Anna"}, {"imie_nazwisko": "Jan"}]}
    predicted = {"pelnomocnicy": [{"imie_nazwisko": "Jan"}, {"imie_nazwisko": "Anna"}]}

    outcomes = compare_document(predicted, reference)

    assert _counts(outcomes) == {"tp": 2, "tn": 0, "fp": 0, "fn": 0}


def test_list_fields_inside_matched_element_are_scored_separately() -> None:
    reference = {"osoby": [{"imie": "Anna", "pesel": "1"}, {"imie": "Jan", "pesel": "2"}]}
    predicted = {"osoby": [{"imie": "Jan", "pesel": "9"}, {"imie": "Anna", "pesel": "1"}]}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [
        ("osoby[0].imie", "tp"),
        ("osoby[0].pesel", "tp"),
        ("osoby[1].imie", "tp"),
        ("osoby[1].pesel", "fp"),
    ]


def test_best_assignment_beats_greedy_first_match() -> None:
    # Zachłanne parowanie pierwszego wyniku z pierwszą referencją dałoby mniej trafień.
    reference = {"o": [{"a": "1", "b": "1"}, {"a": "1", "b": "2"}]}
    predicted = {"o": [{"a": "1", "b": "2"}, {"a": "9", "b": "1"}]}

    outcomes = compare_document(predicted, reference)

    assert _counts(outcomes) == {"tp": 3, "tn": 0, "fp": 1, "fn": 0}


def test_extra_result_element_is_fp_of_all_its_fields() -> None:
    reference = {"o": [{"a": "1", "b": "2"}]}
    predicted = {"o": [{"a": "1", "b": "2"}, {"a": "x", "b": None, "c": "z"}]}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [
        ("o[0].a", "tp"),
        ("o[0].b", "tp"),
        ("o[1].a", "fp"),
        ("o[1].b", "tn"),
        ("o[1].c", "fp"),
    ]


def test_missing_reference_element_is_fn_of_all_its_fields() -> None:
    reference = {"o": [{"a": "1", "b": "2"}, {"a": "x", "b": None}]}
    predicted = {"o": [{"a": "1", "b": "2"}]}

    outcomes = compare_document(predicted, reference)

    assert _outcomes(outcomes) == [
        ("o[0].a", "tp"),
        ("o[0].b", "tp"),
        ("o[1].a", "fn"),
        ("o[1].b", "tn"),
    ]


def test_list_ties_are_deterministic() -> None:
    reference = {"o": [{"a": "1"}, {"a": "1"}, {"a": "1"}]}
    predicted = {"o": [{"a": "1"}, {"a": "1"}]}

    first = compare_document(predicted, reference)

    assert first == compare_document(predicted, reference)
    assert _outcomes(first) == [("o[0].a", "tp"), ("o[1].a", "tp"), ("o[2].a", "fn")]


def test_list_of_lists_and_none_items() -> None:
    outcomes = compare_document({"m": [[1, 2], None]}, {"m": [[2, 1], None]})

    assert _counts(outcomes) == {"tp": 2, "tn": 1, "fp": 0, "fn": 0}


def test_list_against_missing_value_expands_elements() -> None:
    assert _outcomes(compare_document({"o": [{"a": 1}]}, {})) == [("o[0].a", "fp")]
    assert _outcomes(compare_document({}, {"o": [{"a": 1}]})) == [("o[0].a", "fn")]
    assert _outcomes(compare_document({"o": {"a": 1}}, {})) == [("o.a", "fp")]
    assert _outcomes(compare_document({}, {"o": {"a": 1}})) == [("o.a", "fn")]


def test_report_has_separate_counts() -> None:
    metrics = [
        evaluate_document(
            _case("przelew"),
            {"a": 1, "b": 5, "c": None, "d": 1},
            {"a": 1, "b": 6, "c": None, "e": 1},
            "przelew",
        )
    ]

    totals = summarize(metrics)["totals"]

    assert isinstance(totals, dict)
    assert (totals["tp"], totals["tn"], totals["fp"], totals["fn"]) == (1, 1, 2, 1)


def test_evaluate_variants_reports_each_similarity_method() -> None:
    reference = {"przelew_bankowy": {"tytul": "Alfa Beta Gamma Sp. z o.o. opłata"}}
    predicted = {"przelew_bankowy": {"tytul": "opłata Gamma Beta Alfa Sp. z o.o."}}
    documents = [
        EvaluatedDocument(
            case=_case(), predicted=predicted, reference=reference, predicted_class="przelew"
        )
    ]

    report = evaluate_variants(documents)

    assert set(report) == {"ratio", "token_sort_ratio", "partial_ratio"}
    assert report["ratio"]["totals"]["f1"] == 0.0  # type: ignore[index]  # dict[str, object] w teście
    assert report["token_sort_ratio"]["totals"]["f1"] == 1.0  # type: ignore[index]  # j.w.
