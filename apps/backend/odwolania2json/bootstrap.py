"""Przedziały niepewności F1: bootstrap po sprawach oraz porównanie sparowane.

Losujemy całe sprawy, nie pola: pola jednej sprawy są zależne (te same dokumenty,
często ta sama rodzina duplikatów), więc bootstrap po polach zawyżałby pewność.
Ziarno jest jawnym parametrem, dzięki czemu przedziały są powtarzalne.
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from odwolania2json.evaluator import ClassTotals, DocumentMetrics

__all__ = [
    "DeltaInterval",
    "F1Interval",
    "bootstrap_f1",
    "case_totals",
    "paired_bootstrap_delta",
]

DEFAULT_RESAMPLES = 2000
DEFAULT_CONFIDENCE = 0.95


class F1Interval(BaseModel):
    """F1 całego zestawu i percentylowy przedział bootstrapu."""

    model_config = ConfigDict(frozen=True)

    f1: float
    low: float
    high: float
    confidence: float
    resamples: int
    seed: int


class DeltaInterval(BaseModel):
    """ΔF1 = F1(B) − F1(A) na wspólnych sprawach z przedziałem bootstrapu."""

    model_config = ConfigDict(frozen=True)

    delta: float
    low: float
    high: float
    confidence: float
    resamples: int
    seed: int
    cases: int


def case_totals(metrics: list[DocumentMetrics]) -> dict[str, ClassTotals]:
    """Sumuje liczniki pól po `case_id` (klasyfikacja nie wchodzi do F1 pól)."""
    counts: dict[str, Counter[str]] = {}
    for item in metrics:
        counter = counts.setdefault(item.case_id, Counter())
        counter.update(o.verdict for o in item.outcomes)
    return {
        case_id: ClassTotals(tp=c["tp"], tn=c["tn"], fp=c["fp"], fn=c["fn"])
        for case_id, c in counts.items()
    }


def bootstrap_f1(
    totals: Mapping[str, ClassTotals],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE,
) -> F1Interval:
    """Przedział F1 z losowania ze zwracaniem całych spraw (metoda percentylowa)."""
    _check(totals, resamples, confidence)
    ordered = [totals[key] for key in sorted(totals)]
    rng = random.Random(seed)  # noqa: S311  # symulacja statystyczna, nie kryptografia
    samples = sorted(_f1_of(_pick(ordered, rng, len(ordered))) for _ in range(resamples))
    low, high = _percentiles(samples, confidence)
    return F1Interval(
        f1=_f1_of(ordered),
        low=low,
        high=high,
        confidence=confidence,
        resamples=resamples,
        seed=seed,
    )


def paired_bootstrap_delta(
    baseline: Mapping[str, ClassTotals],
    candidate: Mapping[str, ClassTotals],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE,
) -> DeltaInterval:
    """ΔF1 = F1(candidate) − F1(baseline); w każdej próbie te same sprawy w obu zestawach.

    Zestawy muszą dotyczyć dokładnie tych samych spraw: brak sprawy w jednym z nich
    to błąd, a nie ciche porównanie na części wspólnej.
    """
    if baseline.keys() != candidate.keys():
        raise ValueError(
            "zestawy wyników mają różne sprawy; porównanie sparowane wymaga tych samych"
        )
    _check(baseline, resamples, confidence)
    keys = sorted(baseline)
    first = [baseline[key] for key in keys]
    second = [candidate[key] for key in keys]
    rng = random.Random(seed)  # noqa: S311  # symulacja statystyczna, nie kryptografia
    deltas: list[float] = []
    for _ in range(resamples):
        indexes = [rng.randrange(len(keys)) for _ in keys]
        deltas.append(_f1_of([second[i] for i in indexes]) - _f1_of([first[i] for i in indexes]))
    deltas.sort()
    low, high = _percentiles(deltas, confidence)
    return DeltaInterval(
        delta=_f1_of(second) - _f1_of(first),
        low=low,
        high=high,
        confidence=confidence,
        resamples=resamples,
        seed=seed,
        cases=len(keys),
    )


def _check(totals: Mapping[str, ClassTotals], resamples: int, confidence: float) -> None:
    if not totals:
        raise ValueError("bootstrap wymaga co najmniej jednej sprawy")
    if resamples < 1:
        raise ValueError("liczba losowań musi być dodatnia")
    if not 0.0 < confidence < 1.0:
        raise ValueError("poziom ufności musi leżeć w przedziale (0, 1)")


def _pick(items: list[ClassTotals], rng: random.Random, size: int) -> list[ClassTotals]:
    return [items[rng.randrange(len(items))] for _ in range(size)]


def _f1_of(items: list[ClassTotals]) -> float:
    return ClassTotals(
        tp=sum(i.tp for i in items),
        tn=sum(i.tn for i in items),
        fp=sum(i.fp for i in items),
        fn=sum(i.fn for i in items),
    ).f1


def _percentiles(sorted_values: list[float], confidence: float) -> tuple[float, float]:
    """Dolny i górny percentyl (najbliższy rank) z posortowanych wartości."""
    tail = (1.0 - confidence) / 2.0
    last = len(sorted_values) - 1
    return sorted_values[round(tail * last)], sorted_values[round((1.0 - tail) * last)]
