"""Ewaluator na 180 plikach referencyjnych organizatora (60 spraw × 3 dokumenty)."""

from __future__ import annotations

import copy

import pytest
from odwolania2json.evaluator import (
    EvalConfig,
    EvaluatedDocument,
    FieldOutcome,
    compare_document,
    evaluate_document,
    evaluate_variants,
    summarize,
)
from odwolania2json.loader import CaseReference, load_case_references, load_reference_json


def _references() -> list[tuple[CaseReference, dict[str, object]]]:
    return [
        (ref, load_reference_json(ref))
        for ref in load_case_references()
        if ref.reference_name is not None
    ]


def _counts(outcomes: list[FieldOutcome]) -> dict[str, int]:
    return {v: sum(1 for o in outcomes if o.verdict == v) for v in ("tp", "tn", "fp", "fn")}


def _przelew() -> tuple[CaseReference, dict[str, object]]:
    return next((r, d) for r, d in _references() if r.document_class == "przelew")


def test_reference_has_180_files() -> None:
    assert len(_references()) == 180


def test_reference_versus_reference_is_perfect_on_all_files() -> None:
    metrics = [
        evaluate_document(ref, copy.deepcopy(data), data, ref.document_class)
        for ref, data in _references()
    ]

    report = summarize(metrics)

    totals = report["totals"]
    assert isinstance(totals, dict)
    assert totals["f1"] == 1.0
    assert totals["fp"] == 0
    assert totals["fn"] == 0
    assert totals["tp"] > 0
    assert all(o.verdict in {"tp", "tn"} for m in metrics for o in m.outcomes)


def test_reference_is_perfect_in_every_similarity_variant() -> None:
    documents = [
        EvaluatedDocument(
            case=ref,
            predicted=copy.deepcopy(data),
            reference=data,
            predicted_class=ref.document_class,
        )
        for ref, data in _references()
    ]

    for report in evaluate_variants(documents).values():
        assert report["totals"]["f1"] == 1.0  # type: ignore[index]  # dict[str, object] w raporcie


def test_one_broken_value_is_one_fp() -> None:
    _, data = _przelew()
    broken = copy.deepcopy(data)
    broken["przelew_bankowy"]["kwota"] = 1.0  # type: ignore[index]  # struktura referencji znana z danych

    counts = _counts(compare_document(broken, data))

    assert (counts["fp"], counts["fn"]) == (1, 0)
    assert counts["tp"] == 5


def test_added_field_is_one_fp_and_removed_field_is_one_fn() -> None:
    _, data = _przelew()
    added = copy.deepcopy(data)
    added["przelew_bankowy"]["nowe_pole"] = "x"  # type: ignore[index]  # struktura referencji znana z danych
    removed = copy.deepcopy(data)
    del removed["przelew_bankowy"]["kwota"]  # type: ignore[attr-defined]  # struktura referencji znana z danych

    assert _counts(compare_document(added, data))["fp"] == 1
    removed_counts = _counts(compare_document(removed, data))
    assert (removed_counts["fn"], removed_counts["fp"]) == (1, 0)


def test_list_permutation_keeps_perfect_score() -> None:
    ref = next(
        (r, d)
        for r, d in _references()
        if r.document_class == "pelnomocnictwo" and len(d["pelnomocnicy"]) > 1  # type: ignore[arg-type]  # lista z danych
    )
    data = ref[1]
    permuted = copy.deepcopy(data)
    permuted["pelnomocnicy"].reverse()  # type: ignore[attr-defined]  # lista z danych

    counts = _counts(compare_document(permuted, data))

    assert (counts["fp"], counts["fn"]) == (0, 0)


def test_name_one_char_off_is_tp_and_many_chars_off_is_fp() -> None:
    ref = next((r, d) for r, d in _references() if r.document_class == "odwolanie")
    data = ref[1]
    close = copy.deepcopy(data)
    far = copy.deepcopy(data)
    name = data["Odwolujacy"][0]["nazwa"]  # type: ignore[index]  # struktura odwołania
    close["Odwolujacy"][0]["nazwa"] = name[:-1] + "#"  # type: ignore[index]  # j.w.
    far["Odwolujacy"][0]["nazwa"] = "Zupełnie inna firma"  # type: ignore[index]  # j.w.

    close_counts = _counts(compare_document(close, data))
    far_counts = _counts(compare_document(far, data))

    assert (close_counts["fp"], close_counts["fn"]) == (0, 0)
    assert (far_counts["fp"], far_counts["fn"]) == (1, 0)


def test_eval_config_defaults_and_rejects_unknown_mode() -> None:
    assert EvalConfig().wrong_value == "fp"
    with pytest.raises(ValueError, match="wrong_value"):
        EvalConfig(wrong_value="x")  # type: ignore[arg-type]  # celowo zła wartość
