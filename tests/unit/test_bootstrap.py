"""Testy bootstrapu po sprawach i porównania sparowanego."""

from __future__ import annotations

import pytest
from odwolania2json.bootstrap import (
    bootstrap_f1,
    case_totals,
    paired_bootstrap_delta,
)
from odwolania2json.evaluator import ClassTotals, DocumentMetrics, FieldOutcome


def _t(tp: int, fp: int = 0, fn: int = 0) -> ClassTotals:
    return ClassTotals(tp=tp, tn=0, fp=fp, fn=fn)


def test_case_totals_groups_documents_by_case_id() -> None:
    def doc(case_id: str, verdicts: list[str]) -> DocumentMetrics:
        return DocumentMetrics(
            case_id=case_id,
            input_name="x.pdf",
            document_class="przelew",
            outcomes=[FieldOutcome(path="p", verdict=v) for v in verdicts],  # type: ignore[arg-type]  # literal z listy str w teście
            classification="tp",
        )

    totals = case_totals([doc("a", ["tp", "fp"]), doc("a", ["fn", "tn"]), doc("b", ["tp"])])

    assert totals == {"a": _t(1, 1, 1).model_copy(update={"tn": 1}), "b": _t(1)}


def test_identical_cases_give_degenerate_interval() -> None:
    result = bootstrap_f1({"a": _t(2, 1, 1), "b": _t(2, 1, 1)}, seed=1, resamples=50)

    assert result.f1 == pytest.approx(4 / 6)
    assert result.low == pytest.approx(4 / 6)
    assert result.high == pytest.approx(4 / 6)


def test_interval_brackets_point_estimate_and_is_reproducible() -> None:
    totals = {f"c{i}": _t(10 - i, i, 0) for i in range(10)}

    first = bootstrap_f1(totals, seed=7, resamples=500)
    second = bootstrap_f1(totals, seed=7, resamples=500)

    assert first == second
    assert first.low < first.f1 < first.high
    assert first.seed == 7
    assert first.resamples == 500
    assert first.confidence == 0.95
    assert bootstrap_f1(totals, seed=8, resamples=500) != first


def test_resamples_whole_cases_not_fields() -> None:
    # Jedna sprawa idealna, jedna bez trafień: losowanie spraw daje tylko F1 ∈ {0, 2/3?, 1}.
    totals = {"good": _t(10), "bad": _t(0, 10, 10)}

    result = bootstrap_f1(totals, seed=3, resamples=400)

    assert result.low == 0.0
    assert result.high == 1.0


def test_wider_confidence_gives_wider_or_equal_interval() -> None:
    totals = {f"c{i}": _t(i + 1, 3, 2) for i in range(12)}

    narrow = bootstrap_f1(totals, seed=5, resamples=600, confidence=0.5)
    wide = bootstrap_f1(totals, seed=5, resamples=600, confidence=0.99)

    assert wide.low <= narrow.low
    assert wide.high >= narrow.high


def test_paired_delta_of_identical_sets_is_zero() -> None:
    totals = {"a": _t(3, 1), "b": _t(2, 0, 1)}

    result = paired_bootstrap_delta(totals, totals, seed=1, resamples=100)

    assert (result.delta, result.low, result.high) == (0.0, 0.0, 0.0)
    assert result.cases == 2


def test_paired_delta_detects_consistent_improvement() -> None:
    baseline = {f"c{i}": _t(5, 3, 3) for i in range(20)}
    candidate = {f"c{i}": _t(8, 1, 1) for i in range(20)}

    result = paired_bootstrap_delta(baseline, candidate, seed=11, resamples=300)

    assert result.delta == pytest.approx(16 / 18 - 10 / 16)
    assert result.low > 0.0
    assert result.high >= result.delta


def test_paired_delta_sign_and_reproducibility() -> None:
    baseline = {f"c{i}": _t(8, 1, 1) for i in range(10)}
    candidate = {f"c{i}": _t(5, 3, 3) for i in range(10)}

    a = paired_bootstrap_delta(baseline, candidate, seed=2, resamples=200)
    b = paired_bootstrap_delta(baseline, candidate, seed=2, resamples=200)

    assert a == b
    assert a.delta < 0.0
    assert a.high < 0.0


def test_paired_delta_requires_same_cases() -> None:
    with pytest.raises(ValueError, match="różne sprawy"):
        paired_bootstrap_delta({"a": _t(1)}, {"b": _t(1)}, seed=1)


def test_invalid_arguments_are_rejected() -> None:
    with pytest.raises(ValueError, match="co najmniej jednej"):
        bootstrap_f1({}, seed=1)
    with pytest.raises(ValueError, match="losowań"):
        bootstrap_f1({"a": _t(1)}, seed=1, resamples=0)
    with pytest.raises(ValueError, match="ufności"):
        bootstrap_f1({"a": _t(1)}, seed=1, confidence=1.0)
    with pytest.raises(ValueError, match="ufności"):
        bootstrap_f1({"a": _t(1)}, seed=1, confidence=0.0)
