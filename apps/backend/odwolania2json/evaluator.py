"""Ewaluator wyników ekstrakcji: TP/TN/FP/FN per pole, klasa i dokument oraz F1.

Porównujemy wynik z referencją pole po polu. Każde pole daje wpis `tp`/`tn`/`fp`/`fn`,
a F1 liczymy z tych liczników, więc raport jest powtarzalny i nie zależy od formatu
pliku wyjściowego.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict

from odwolania2json.loader import CaseReference, DocumentClass

__all__ = [
    "ClassTotals",
    "DocumentMetrics",
    "FieldOutcome",
    "Verdict",
    "compare_document",
    "evaluate_document",
    "summarize",
]

Verdict = Literal["tp", "tn", "fp", "fn"]


class FieldOutcome(BaseModel):
    """Werdykt jednego porównania na kropkowej ścieżce pola."""

    model_config = ConfigDict(frozen=True)

    path: str
    verdict: Verdict


class DocumentMetrics(BaseModel):
    """Wszystkie werdykty jednego dokumentu oraz werdykt jego klasyfikacji."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    input_name: str
    document_class: DocumentClass
    outcomes: list[FieldOutcome]
    classification: Verdict


class ClassTotals(BaseModel):
    """Liczniki TP/TN/FP/FN z wyliczonym F1."""

    model_config = ConfigDict(frozen=True)

    tp: int
    tn: int
    fp: int
    fn: int

    @property
    def f1(self) -> float:
        """F1 = 2TP / (2TP + FP + FN).

        Przy mianowniku 0 zwracamy 0.0: brak trafień nie może wyglądać jak wynik
        idealny, a dzielenie przez zero byłoby mylące w raporcie.
        """
        denominator = 2 * self.tp + self.fp + self.fn
        if denominator == 0:
            return 0.0
        return 2 * self.tp / denominator


def compare_document(
    predicted: dict[str, object], reference: dict[str, object]
) -> list[FieldOutcome]:
    """Porównuje wynik z referencją i zwraca werdykt dla każdego pola."""
    outcomes: list[FieldOutcome] = []
    _compare_mapping("", predicted, reference, outcomes)
    return outcomes


def evaluate_document(
    case: CaseReference,
    predicted: dict[str, object],
    reference: dict[str, object],
    predicted_class: DocumentClass,
) -> DocumentMetrics:
    """Ocena jednego dokumentu: pola oraz klasyfikacja klasy dokumentu.

    Zła klasa zapisywana jest jako `fn` na `classification`. `summarize` liczy ją
    jako jednocześnie FP i FN, bo pomylenie klasy psuje dwie klasy naraz.
    """
    classification: Verdict = "tp" if predicted_class == case.document_class else "fn"
    return DocumentMetrics(
        case_id=case.case_id,
        input_name=case.input_name,
        document_class=case.document_class,
        outcomes=compare_document(predicted, reference),
        classification=classification,
    )


def summarize(metrics: list[DocumentMetrics]) -> dict[str, object]:
    """Raport JSON: totaly, podział na klasy i dokumenty oraz klasyfikacja osobno."""
    classes: tuple[str, ...] = get_args(DocumentClass)
    per_class = {
        document_class: _report(
            _totals(
                o.verdict for m in metrics if m.document_class == document_class for o in m.outcomes
            )
        )
        for document_class in classes
    }
    per_document = [
        {
            "case_id": m.case_id,
            "input_name": m.input_name,
            "document_class": m.document_class,
            **_report(_totals(o.verdict for o in m.outcomes)),
        }
        for m in metrics
    ]
    return {
        "totals": _report(_totals(o.verdict for m in metrics for o in m.outcomes)),
        "per_class": per_class,
        "per_document": per_document,
        "classification": _report(_totals(_classification_verdicts(metrics))),
    }


def _join(prefix: str, key: str) -> str:
    return key if prefix == "" else f"{prefix}.{key}"


def _add(outcomes: list[FieldOutcome], path: str, verdict: Verdict) -> None:
    outcomes.append(FieldOutcome(path=path, verdict=verdict))


def _compare_mapping(
    prefix: str,
    predicted: dict[str, object],
    reference: dict[str, object],
    outcomes: list[FieldOutcome],
) -> None:
    # Iteracja po sumie kluczy: klucz obecny tylko po jednej stronie też jest porównany.
    for key in sorted(predicted.keys() | reference.keys()):
        _compare_value(
            _join(prefix, key),
            predicted.get(key),
            reference.get(key),
            outcomes,
        )


def _compare_value(
    path: str,
    predicted: object,
    reference: object,
    outcomes: list[FieldOutcome],
) -> None:
    # `None` jest traktowany tak samo jak brak klucza: oba znaczą „brak wartości”.
    if predicted is None and reference is None:
        _add(outcomes, path, "tn")
        return
    if reference is None:
        if isinstance(predicted, dict):
            _compare_mapping(path, predicted, {}, outcomes)
        elif isinstance(predicted, list):
            _compare_lists(path, predicted, [], outcomes)
        else:
            _add(outcomes, path, "fp")
        return
    if predicted is None:
        if isinstance(reference, dict):
            _compare_mapping(path, {}, reference, outcomes)
        elif isinstance(reference, list):
            _compare_lists(path, [], reference, outcomes)
        else:
            _add(outcomes, path, "fn")
        return
    if isinstance(predicted, dict) and isinstance(reference, dict):
        _compare_mapping(path, predicted, reference, outcomes)
        return
    if isinstance(predicted, list) and isinstance(reference, list):
        _compare_lists(path, predicted, reference, outcomes)
        return
    # Zła wartość lub zmiana typu: jednocześnie fałszywie wykryta i brakująca.
    # `True == 1` w Pythonie, więc typ bool sprawdzamy osobno: zmiana bool<->liczba to błąd pola.
    if predicted == reference and isinstance(predicted, bool) == isinstance(reference, bool):
        _add(outcomes, path, "tn")
    else:
        _add(outcomes, path, "fp")
        _add(outcomes, path, "fn")


def _compare_lists(
    path: str,
    predicted: list[object],
    reference: list[object],
    outcomes: list[FieldOutcome],
) -> None:
    # Dopasowanie po treści, bo kolejność osób i pozycji w listach bywa różna.
    unmatched = list(predicted)
    for element in reference:
        if element in unmatched:
            unmatched.remove(element)
            _add(outcomes, path, "tn")
        else:
            _add(outcomes, path, "fn")
    for _ in unmatched:
        _add(outcomes, path, "fp")


def _totals(verdicts: Iterable[Verdict]) -> ClassTotals:
    counts = Counter(verdicts)
    return ClassTotals(
        tp=counts["tp"],
        tn=counts["tn"],
        fp=counts["fp"],
        fn=counts["fn"],
    )


def _classification_verdicts(metrics: list[DocumentMetrics]) -> list[Verdict]:
    verdicts: list[Verdict] = []
    for m in metrics:
        if m.classification == "fn":
            verdicts.extend(("fp", "fn"))
        else:
            verdicts.append(m.classification)
    return verdicts


def _report(totals: ClassTotals) -> dict[str, object]:
    return {
        "tp": totals.tp,
        "tn": totals.tn,
        "fp": totals.fp,
        "fn": totals.fn,
        "f1": totals.f1,
    }
