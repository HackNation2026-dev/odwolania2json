"""Pipeline dokumentu: tekst stron → jedno wywołanie LLM → normalizacja → serializer.

Kolejność i zasady (Z01, ADR-006):
- tekst dokumentu ma znaczniki stron `[[strona N]]`, tak jak w pomiarze E10;
- model zwraca klasę i pola w jednej odpowiedzi; odpowiedź `ambiguous` dostaje
  jedno dodatkowe wywołanie z poleceniem wyboru najlepszej klasy;
- wartości przechodzą przez normalizatory pól o stałym formacie; wartość, której
  nie da się znormalizować, zostaje i dostaje flagę (walidacja nie blokuje eksportu);
- parę `czynnosc_powod_id` ↔ `czynnosc_opis` ustala kod ze słownika organizatora;
- cytat i strona nie decydują o treści wyniku.

Flagi to krótkie kody ze ścieżką pola (bez wartości), przeznaczone do raportu.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final

from odwolania2json_contracts.powody import APPEAL_REASONS

from odwolania2json.domain import normalize
from odwolania2json.loader import DocumentClass
from odwolania2json.serialize import build_values, serialize

from .answer import LlmAnswer, parse_answer
from .ports import JsonLlm
from .prompt import CLASS_BY_LABEL, COMMIT_NOTE, PAGE_MARKER, SYSTEM_PROMPT

__all__ = [
    "REASON_DESCRIPTION_POINTER",
    "REASON_ID_POINTER",
    "Extraction",
    "PageText",
    "build_extraction",
    "document_text",
    "enforce_reason_pair",
    "extract",
    "normalize_value",
]

REASON_ID_POINTER: Final = "/OdwolanieKIO/czynnosc_powod_id"
REASON_DESCRIPTION_POINTER: Final = "/OdwolanieKIO/czynnosc_opis"

type _Normalizer = Callable[[str], str | float | None]

# Normalizator według ostatniego segmentu ścieżki (klucza organizatora).
_NORMALIZERS: Final[dict[str, _Normalizer]] = {
    "nip": normalize.normalize_nip,
    "regon": normalize.normalize_regon,
    "krs": normalize.normalize_krs,
    "pesel": normalize.normalize_pesel,
    "na_rachunek": normalize.normalize_account,
    "z_rachunku": normalize.normalize_account,
    "kwota": normalize.normalize_amount,
    "numer_ted": normalize.normalize_ted,
    "data": normalize.normalize_date,
    "data_operacji": normalize.normalize_date,
    "czynnosc_dzien": normalize.normalize_date,
}
# Flagi 0/1 organizatora: model bywa zwraca je jako `true`/`false`.
_BINARY_KEYS: Final = frozenset({"przez-pelnomocnika", "prowadzacy_postepowanie"})
_REASON_BY_TEXT: Final = {normalize.fold(text): key for key, text in APPEAL_REASONS.items()}


@dataclass(frozen=True)
class PageText:
    """Tekst jednej strony przekazywany modelowi (z warstwy PDF albo z OCR)."""

    number: int
    text: str


@dataclass(frozen=True)
class Extraction:
    """Wynik ekstrakcji: klasa, JSON według szablonu klasy i flagi do raportu.

    `document_class` jest `None` tylko wtedy, gdy model dwukrotnie nie wybrał klasy.
    """

    document_class: DocumentClass | None
    payload: dict[str, object]
    flags: tuple[str, ...]


def document_text(pages: Sequence[PageText]) -> str:
    """Tekst dokumentu ze znacznikami stron, w kolejności stron."""
    return "\n".join(f"{PAGE_MARKER.format(number=page.number)}\n{page.text}" for page in pages)


def normalize_value(pointer: str, value: object) -> tuple[object, bool]:
    """Zwraca (wartość, czy normalizacja zawiodła) dla pola o podanej ścieżce.

    Nieudana normalizacja zostawia wartość modelu: lepsza wartość do sprawdzenia
    niż utrata pola (ADR-006, walidacja nie blokuje eksportu).
    """
    key = pointer.rsplit("/", 1)[-1]
    if isinstance(value, bool):
        return (int(value), False) if key in _BINARY_KEYS else (value, False)
    normalizer = _NORMALIZERS.get(key)
    if normalizer is None or value is None:
        return value, False
    if key == "kwota" and isinstance(value, int | float):
        return value, False
    if not isinstance(value, str | int | float):
        return value, True
    normalized = normalizer(str(value))
    return (value, True) if normalized is None else (normalized, False)


def _reason_id(value: object) -> int | None:
    """Identyfikator powodu ze słownika albo `None`, gdy wartość nim nie jest."""
    if isinstance(value, bool):
        return None
    if isinstance(value, str) and value.strip().isascii() and value.strip().isdigit():
        value = int(value.strip())
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return value if isinstance(value, int) and value in APPEAL_REASONS else None


def enforce_reason_pair(items: dict[str, object]) -> list[str]:
    """Uzgadnia w miejscu parę identyfikator ↔ opis powodu ze słownikiem organizatora.

    Poprawny identyfikator wyznacza opis dosłownie ze słownika. Bez poprawnego
    identyfikatora opis zgodny ze słownikiem wyznacza identyfikator. Gdy żadne
    z nich nie wskazuje wpisu słownika, wartości zostają i dostają flagę.
    """
    raw_id = items.get(REASON_ID_POINTER)
    raw_text = items.get(REASON_DESCRIPTION_POINTER)
    if raw_id is None and raw_text is None:
        return []
    reason = _reason_id(raw_id)
    if reason is None and isinstance(raw_text, str):
        reason = _REASON_BY_TEXT.get(normalize.fold(raw_text))
    if reason is None:
        return [f"reason_pair_invalid:{REASON_ID_POINTER}"]
    flags: list[str] = []
    if raw_text is not None and raw_text != APPEAL_REASONS[reason]:
        flags.append(f"reason_text_replaced:{REASON_DESCRIPTION_POINTER}")
    items[REASON_ID_POINTER] = reason
    items[REASON_DESCRIPTION_POINTER] = APPEAL_REASONS[reason]
    return flags


def build_extraction(answer: LlmAnswer) -> Extraction:
    """Składa wynik z poprawnej odpowiedzi modelu (bez wywołań sieciowych)."""
    document_class = CLASS_BY_LABEL.get(answer.label)
    if document_class is None:
        return Extraction(None, {}, ("class_ambiguous",))
    if document_class == "obcy":
        return Extraction("obcy", {}, ())
    flags: list[str] = []
    items: dict[str, object] = {}
    for field in answer.fields:
        if field.value is None or field.value == "":
            continue  # `null` albo pusty tekst to brak pola
        value, failed = normalize_value(field.field, field.value)
        if failed:
            flags.append(f"unnormalized:{field.field}")
        items[field.field] = value
    if document_class == "odwolanie":
        flags.extend(enforce_reason_pair(items))
    values, rejected = build_values(document_class, items.items())
    flags.extend(f"unknown_field:{pointer}" for pointer in rejected)
    payload, serializer_flags = serialize(document_class, values)
    flags.extend(serializer_flags)
    return Extraction(document_class, payload, tuple(flags))


def extract(text: str, llm: JsonLlm) -> Extraction:
    """Jedno wywołanie LLM na dokument; `ambiguous` dostaje jedno dodatkowe.

    Błąd sieci, autoryzacji albo odpowiedź poza schematem po ponowieniu wychodzą
    jako `ProcessingError`: wynik dokumentu nigdy nie jest wtedy zmyślany.
    """
    answer = llm.complete_json(SYSTEM_PROMPT, text, None, parse_answer)
    if answer.label != "ambiguous":
        return build_extraction(answer)
    second = build_extraction(
        llm.complete_json(SYSTEM_PROMPT, text + COMMIT_NOTE, None, parse_answer)
    )
    if second.document_class is None:
        return second
    return Extraction(second.document_class, second.payload, ("class_ambiguous", *second.flags))
