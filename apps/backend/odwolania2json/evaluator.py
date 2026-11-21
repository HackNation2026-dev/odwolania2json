"""Ewaluator wyników ekstrakcji: TP/TN/FP/FN per pole, klasa i dokument oraz F1.

Porównujemy wynik z referencją pole po polu. Każde pole daje wpis `tp`/`tn`/`fp`/`fn`,
a F1 liczymy z tych liczników, więc raport jest powtarzalny i nie zależy od formatu
pliku wyjściowego.

Przyjęta interpretacja (ADR-005, do potwierdzenia z mentorem, pytania U-Q01/U-Q02):
błędna wartość obecna po obu stronach to wyłącznie FP, bez dodatkowego FN. Wariant
FP+FN jest dostępny w `EvalConfig.wrong_value` do porównania. Pięć pól tekstowych
z `SIMILARITY_FIELD_PATHS` jest zgodnych przy podobieństwie ≥ progu (domyślnie 0,8),
pozostałe pola wymagają dokładnej równości. Elementy list parujemy po najlepszym
przypisaniu, a pola wewnątrz pary oceniamy osobno.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict

from odwolania2json.loader import CaseReference, DocumentClass
from odwolania2json.similarity import (
    DEFAULT_SIMILARITY_METHOD,
    DEFAULT_SIMILARITY_THRESHOLD,
    SIMILARITY_FIELD_PATHS,
    SIMILARITY_METHODS,
    SimilarityMethod,
    similarity,
)

__all__ = [
    "DEFAULT_CONFIG",
    "ClassTotals",
    "DocumentMetrics",
    "EvalConfig",
    "EvaluatedDocument",
    "FieldOutcome",
    "Verdict",
    "WrongValueMode",
    "compare_document",
    "evaluate_document",
    "evaluate_variants",
    "summarize",
]

Verdict = Literal["tp", "tn", "fp", "fn"]
WrongValueMode = Literal["fp", "fp_fn"]


class EvalConfig(BaseModel):
    """Parametry interpretacji F1; domyślne wartości to interpretacja z ADR-005."""

    model_config = ConfigDict(frozen=True)

    # `fp`: błędna wartość to tylko FP (przyjęte). `fp_fn`: FP i FN (wariant do porównania).
    wrong_value: WrongValueMode = "fp"
    similarity: SimilarityMethod = DEFAULT_SIMILARITY_METHOD
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    fuzzy_fields: frozenset[str] = SIMILARITY_FIELD_PATHS


DEFAULT_CONFIG = EvalConfig()


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
    predicted: dict[str, object],
    reference: dict[str, object],
    config: EvalConfig = DEFAULT_CONFIG,
) -> list[FieldOutcome]:
    """Porównuje wynik z referencją i zwraca werdykt dla każdego pola."""
    outcomes: list[FieldOutcome] = []
    _compare_mapping("", "", predicted, reference, config, outcomes)
    return outcomes


def evaluate_document(
    case: CaseReference,
    predicted: dict[str, object],
    reference: dict[str, object],
    predicted_class: DocumentClass,
    config: EvalConfig = DEFAULT_CONFIG,
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
        outcomes=compare_document(predicted, reference, config),
        classification=classification,
    )


class EvaluatedDocument(BaseModel):
    """Wejście ewaluacji jednego dokumentu: sprawa, wynik, referencja i klasa z klasyfikatora."""

    model_config = ConfigDict(frozen=True)

    case: CaseReference
    predicted: dict[str, object]
    reference: dict[str, object]
    predicted_class: DocumentClass


def evaluate_variants(
    documents: list[EvaluatedDocument],
    base: EvalConfig = DEFAULT_CONFIG,
    methods: tuple[SimilarityMethod, ...] = SIMILARITY_METHODS,
) -> dict[str, dict[str, object]]:
    """Raport dla każdego wariantu podobieństwa, żeby pokazać rozrzut F1.

    Algorytm podobieństwa nie jest znany (U-Q01), więc ten sam zestaw liczymy
    każdą wymienną miarą i pozostałe parametry bierzemy z `base`.
    """
    return {
        method: summarize(
            [
                evaluate_document(
                    d.case,
                    d.predicted,
                    d.reference,
                    d.predicted_class,
                    base.model_copy(update={"similarity": method}),
                )
                for d in documents
            ]
        )
        for method in methods
    }


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
    path: str,
    generic: str,
    predicted: dict[str, object],
    reference: dict[str, object],
    config: EvalConfig,
    outcomes: list[FieldOutcome],
) -> None:
    # Iteracja po sumie kluczy: klucz obecny tylko po jednej stronie też jest porównany.
    for key in sorted(predicted.keys() | reference.keys()):
        _compare_value(
            _join(path, key),
            _join(generic, key),
            predicted.get(key),
            reference.get(key),
            config,
            outcomes,
        )


def _compare_value(
    path: str,
    generic: str,
    predicted: object,
    reference: object,
    config: EvalConfig,
    outcomes: list[FieldOutcome],
) -> None:
    """Porównuje wartość; `generic` to ścieżka z `[]` zamiast indeksów (klucz konfiguracji)."""
    # `None` jest traktowany tak samo jak brak klucza: oba znaczą „brak wartości”.
    if predicted is None and reference is None:
        _add(outcomes, path, "tn")
        return
    if reference is None:
        _only_in_result(path, generic, predicted, config, outcomes)
        return
    if predicted is None:
        _only_in_reference(path, generic, reference, config, outcomes)
        return
    if isinstance(predicted, dict) and isinstance(reference, dict):
        _compare_mapping(path, generic, predicted, reference, config, outcomes)
        return
    if isinstance(predicted, list) and isinstance(reference, list):
        _compare_lists(path, generic, predicted, reference, config, outcomes)
        return
    if _values_match(generic, predicted, reference, config):
        # Wartość obecna i zgodna z referencją to TP; TN oznacza brak po obu stronach.
        _add(outcomes, path, "tp")
        return
    # Błędna obecna wartość (także zmiana typu lub struktury) to FP (ADR-005).
    _add(outcomes, path, "fp")
    if config.wrong_value == "fp_fn":
        _add(outcomes, path, "fn")


def _only_in_result(
    path: str, generic: str, value: object, config: EvalConfig, outcomes: list[FieldOutcome]
) -> None:
    """Wartość tylko w wyniku: FP każdego niepustego liścia."""
    if isinstance(value, dict):
        _compare_mapping(path, generic, value, {}, config, outcomes)
    elif isinstance(value, list):
        _compare_lists(path, generic, value, [], config, outcomes)
    else:
        _add(outcomes, path, "fp")


def _only_in_reference(
    path: str, generic: str, value: object, config: EvalConfig, outcomes: list[FieldOutcome]
) -> None:
    """Wartość tylko w referencji: FN każdego niepustego liścia."""
    if isinstance(value, dict):
        _compare_mapping(path, generic, {}, value, config, outcomes)
    elif isinstance(value, list):
        _compare_lists(path, generic, [], value, config, outcomes)
    else:
        _add(outcomes, path, "fn")


def _values_match(generic: str, predicted: object, reference: object, config: EvalConfig) -> bool:
    """Zgodność liści: próg podobieństwa dla pól tekstowych z konfiguracji, reszta dokładnie."""
    if generic in config.fuzzy_fields and isinstance(predicted, str) and isinstance(reference, str):
        return similarity(predicted, reference, config.similarity) >= config.threshold
    # `True == 1` w Pythonie, więc typ bool sprawdzamy osobno: zmiana bool<->liczba to błąd pola.
    return predicted == reference and isinstance(predicted, bool) == isinstance(reference, bool)


def _leaf_count(value: object) -> int:
    """Liczba niepustych liści; tyle FP (lub FN) daje element występujący po jednej stronie."""
    if value is None:
        return 0
    if isinstance(value, dict):
        return sum(_leaf_count(item) for item in value.values())
    if isinstance(value, list):
        return sum(_leaf_count(item) for item in value)
    return 1


def _compare_lists(
    path: str,
    generic: str,
    predicted: list[object],
    reference: list[object],
    config: EvalConfig,
    outcomes: list[FieldOutcome],
) -> None:
    """Element do elementu po najlepszym przypisaniu; kolejność nie ma znaczenia.

    Indeks w ścieżce to pozycja elementu referencji. Elementy tylko w wyniku dostają
    kolejne indeksy za końcem referencji, więc ścieżki są jednoznaczne.
    """
    item_generic = f"{generic}[]"
    paths = [f"{path}[{index}]" for index in range(len(reference) + len(predicted))]
    pair_outcomes: dict[tuple[int, int], list[FieldOutcome]] = {}
    weights: list[list[int]] = []
    for p_index, p_item in enumerate(predicted):
        row: list[int] = []
        for r_index, r_item in enumerate(reference):
            pair: list[FieldOutcome] = []
            _compare_value(paths[r_index], item_generic, p_item, r_item, config, pair)
            pair_outcomes[(p_index, r_index)] = pair
            counts = Counter(o.verdict for o in pair)
            row.append(
                2 * counts["tp"]
                - counts["fp"]
                - counts["fn"]
                + _leaf_count(p_item)
                + _leaf_count(r_item)
            )
        weights.append(row)
    assignment = _best_assignment(weights, len(reference))
    matched_reference = {r_index: p_index for p_index, r_index in assignment.items()}
    for r_index, r_item in enumerate(reference):
        if r_index in matched_reference:
            outcomes.extend(pair_outcomes[(matched_reference[r_index], r_index)])
        else:
            _only_in_reference(paths[r_index], item_generic, r_item, config, outcomes)
    extra = 0
    for p_index, p_item in enumerate(predicted):
        if p_index not in assignment:
            _only_in_result(paths[len(reference) + extra], item_generic, p_item, config, outcomes)
            extra += 1


def _best_assignment(weights: list[list[int]], reference_size: int) -> dict[int, int]:
    """Przypisanie wynik→referencja o maksymalnej sumie wag; zawsze `min(n, m)` par.

    Waga każdej pary jest nieujemna, więc pełne przypisanie nie jest gorsze od
    częściowego. Remisy rozstrzyga deterministycznie premia za bliskość indeksów,
    a w razie dalszego remisu kolejność przeglądania algorytmu węgierskiego.
    """
    rows = len(weights)
    if rows == 0 or reference_size == 0:
        return {}
    size = max(rows, reference_size)
    scale = size * size + 1
    cost = [[0] * size for _ in range(size)]
    for p_index in range(rows):
        for r_index in range(reference_size):
            closeness = size - abs(p_index - r_index)
            cost[p_index][r_index] = -(weights[p_index][r_index] * scale + closeness)
    column_of_row = _hungarian(cost)
    return {
        p_index: column_of_row[p_index]
        for p_index in range(rows)
        if column_of_row[p_index] < reference_size
    }


def _hungarian(cost: list[list[int]]) -> list[int]:
    """Algorytm węgierski O(n³) dla kwadratowej macierzy kosztów; zwraca kolumnę każdego wiersza."""
    n = len(cost)
    infinity = sum(abs(value) for row in cost for value in row) + 1
    u = [0] * (n + 1)
    v = [0] * (n + 1)
    matched_row = [0] * (n + 1)
    way = [0] * (n + 1)
    for row in range(1, n + 1):
        matched_row[0] = row
        column = 0
        minimum = [infinity] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[column] = True
            current = matched_row[column]
            delta = infinity
            next_column = 0
            for j in range(1, n + 1):
                if used[j]:
                    continue
                reduced = cost[current - 1][j - 1] - u[current] - v[j]
                if reduced < minimum[j]:
                    minimum[j] = reduced
                    way[j] = column
                if minimum[j] < delta:
                    delta = minimum[j]
                    next_column = j
            for j in range(n + 1):
                if used[j]:
                    u[matched_row[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            column = next_column
            if matched_row[column] == 0:
                break
        while column:
            previous = way[column]
            matched_row[column] = matched_row[previous]
            column = previous
    column_of_row = [0] * n
    for j in range(1, n + 1):
        column_of_row[matched_row[j] - 1] = j - 1
    return column_of_row


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
