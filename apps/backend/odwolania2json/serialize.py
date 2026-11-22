"""Serializer wyniku z szablonu klasy dokumentu (ADR-006).

Szablon odwzorowuje wzorce organizatora (`oczekiwane-json`): te same klucze w tej
samej kolejności. Brak wartości to jawne `null`, a elementy list nie są usuwane,
nawet gdy mają same `null` (uprząż je usuwała i gubiła strukturę, E16). Serializer
nigdy nie blokuje eksportu: wartość o złym typie staje się `null` i dostaje flagę
do raportu.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

from .domain.normalize import normalize_amount

__all__ = ["MAX_LIST_ITEMS", "TEMPLATES", "build_values", "leaf_pointers", "serialize"]

# Rodzaje liści: tekst (także identyfikatory i PESEL), liczba całkowita, kwota.
TEXT = "text"
INTEGER = "integer"
AMOUNT = "amount"

type Node = str | dict[str, Node] | list[dict[str, Node]]
type Template = dict[str, Node]

# Limit elementów listy: odpowiedź LLM nie może rozdmuchać wyniku indeksem `/999999/`.
MAX_LIST_ITEMS = 50

TEMPLATES: dict[str, Template] = {
    "odwolanie": {
        "OdwolanieKIO": {
            "data": TEXT,
            "czynnosc_dzien": TEXT,
            "czynnosc_powod_id": INTEGER,
            "czynnosc_opis": TEXT,
            "miejscowosc": TEXT,
        },
        "Odwolujacy": [
            {
                "krs": TEXT,
                "nazwa": TEXT,
                "nip": TEXT,
                "regon": TEXT,
                "przez-pelnomocnika": INTEGER,
                "pelnomocnik": {"imie_nazwisko": TEXT, "nazwa": TEXT, "mail": TEXT},
            }
        ],
        "Zamawiajacy": [
            {
                "krs": TEXT,
                "nazwa": TEXT,
                "nip": TEXT,
                "regon": TEXT,
                "prowadzacy_postepowanie": INTEGER,
            }
        ],
        "ZamowieniePubliczne": {
            "numer_bzp": TEXT,
            "numer_postepowania": TEXT,
            "numer_ted": TEXT,
            "tytul": TEXT,
        },
    },
    "pelnomocnictwo": {
        "mocodawca": [
            {
                "data": {
                    "imie_nazwisko": TEXT,
                    "krs": TEXT,
                    "nazwa": TEXT,
                    "nip": TEXT,
                    "typ": TEXT,
                },
                "podpisujacy": [{"imie_nazwisko": TEXT}],
            }
        ],
        "pelnomocnicy": [{"imie_nazwisko": TEXT, "pesel": TEXT}],
    },
    "przelew": {
        "przelew_bankowy": {
            "data_operacji": TEXT,
            "kwota": AMOUNT,
            "na_rachunek": TEXT,
            "numer_transakcji": TEXT,
            "tytul": TEXT,
            "z_rachunku": TEXT,
        }
    },
}


def serialize(
    document_class: str, values: Mapping[str, object]
) -> tuple[dict[str, object], list[str]]:
    """Układa `values` według szablonu klasy; zwraca wynik i flagi do raportu.

    Dokument obcy zawsze daje `{}`. Nieznana klasa to błąd programisty (`KeyError`),
    a nie sytuacja, którą wolno zamaskować pustym wynikiem.
    """
    if document_class == "obcy":
        return {}, []
    flags: list[str] = []
    payload = _mapping(TEMPLATES[document_class], values, "", flags)
    return payload, flags


def leaf_pointers(document_class: str) -> list[str]:
    """Ścieżki (JSON Pointer) liści szablonu; elementy list mają indeks `0`."""
    pointers: list[str] = []
    _collect(TEMPLATES[document_class], "", pointers)
    return pointers


def build_values(
    document_class: str, items: Iterable[tuple[str, object]]
) -> tuple[dict[str, object], list[str]]:
    """Składa luźną strukturę z par (ścieżka, wartość); zwraca też ścieżki odrzucone.

    Ścieżka spoza szablonu nie trafia do wyniku: model nie może dopisać własnych
    kluczy (E13, M05). Odrzucone ścieżki wracają do raportu zamiast znikać po cichu.
    """
    template = TEMPLATES[document_class]
    values: dict[str, object] = {}
    rejected: list[str] = []
    for pointer, value in items:
        if not _place(template, values, pointer, value):
            rejected.append(pointer)
    return values, rejected


def _collect(node: Node, prefix: str, pointers: list[str]) -> None:
    if isinstance(node, dict):
        for key, child in node.items():
            _collect(child, f"{prefix}/{key}", pointers)
    elif isinstance(node, list):
        _collect(node[0], f"{prefix}/0", pointers)
    else:
        pointers.append(prefix)


def _tokens(pointer: str) -> list[str] | None:
    if not pointer.startswith("/"):
        return None
    return [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]


def _list_index(token: str) -> int | None:
    if not (token.isascii() and token.isdigit()):
        return None
    index = int(token)
    return index if index < MAX_LIST_ITEMS else None


def _resolves(template: Template, tokens: list[str]) -> bool:
    """Czy ścieżka wskazuje liść szablonu (sprawdzane przed jakąkolwiek zmianą)."""
    node: Node = template
    for token in tokens:
        if isinstance(node, dict):
            if token not in node:
                return False
            node = node[token]
        elif isinstance(node, list):
            if _list_index(token) is None:
                return False
            node = node[0]
        else:
            return False
    return isinstance(node, str)


def _place(template: Template, values: dict[str, object], pointer: str, value: object) -> bool:
    tokens = _tokens(pointer)
    if tokens is None or not _resolves(template, tokens):
        return False
    node: Node = template
    target: object = values
    for position, token in enumerate(tokens):
        last = position == len(tokens) - 1
        if isinstance(node, dict) and isinstance(target, dict):
            node = node[token]
            if last:
                target[token] = value
            else:
                empty: object = [] if isinstance(node, list) else {}
                target = target.setdefault(token, empty)
        elif isinstance(node, list) and isinstance(target, list):
            index = int(token)
            while len(target) <= index:
                target.append({})
            node = node[0]
            target = target[index]
    return True


def _mapping(template: Template, values: object, path: str, flags: list[str]) -> dict[str, object]:
    source: Mapping[str, object]
    if isinstance(values, Mapping):
        source = values
    else:
        source = {}
        if values is not None:
            flags.append(f"type_mismatch:{path}")
    result: dict[str, object] = {}
    for key, node in template.items():
        child_path = f"{path}/{key}"
        value = source.get(key)
        if isinstance(node, dict):
            result[key] = _mapping(node, value, child_path, flags)
        elif isinstance(node, list):
            result[key] = _sequence(node[0], value, child_path, flags)
        else:
            result[key] = _leaf(node, value, child_path, flags)
    flags.extend(f"unknown_key:{path}/{key}" for key in source if key not in template)
    return result


def _sequence(
    item_template: Template, values: object, path: str, flags: list[str]
) -> list[dict[str, object]]:
    if not isinstance(values, list):
        if values is not None:
            flags.append(f"type_mismatch:{path}")
        values = []
    items = [
        _mapping(item_template, value, f"{path}/{index}", flags)
        for index, value in enumerate(values)
    ]
    # Pusta lista dostaje jeden element szkieletowy: struktura wyniku zawsze ma
    # komplet kluczy wzorca, a same `null` nie są ani trafieniem, ani błędem pola.
    return items or [_mapping(item_template, None, f"{path}/0", flags)]


def _leaf(kind: str, value: object, path: str, flags: list[str]) -> object:
    if value is None:
        return None
    converted = _CONVERTERS[kind](value)
    if converted is _MISMATCH:
        flags.append(f"type_mismatch:{path}")
        return None
    return converted


_MISMATCH = object()


def _text(value: object) -> object:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, bool):
        return _MISMATCH
    if isinstance(value, int):
        return str(value)
    return _MISMATCH


def _integer(value: object) -> object:
    if isinstance(value, bool):
        return _MISMATCH
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else _MISMATCH
    if isinstance(value, str):
        text = value.strip()
        return int(text) if text.isascii() and text.isdigit() else _MISMATCH
    return _MISMATCH


def _amount(value: object) -> object:
    if isinstance(value, bool):
        return _MISMATCH
    if isinstance(value, int | float):
        number = float(value)
        return number if math.isfinite(number) else _MISMATCH
    if isinstance(value, str):
        parsed = normalize_amount(value)
        return parsed if parsed is not None and math.isfinite(parsed) else _MISMATCH
    return _MISMATCH


_CONVERTERS = {TEXT: _text, INTEGER: _integer, AMOUNT: _amount}
