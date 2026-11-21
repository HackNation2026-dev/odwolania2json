"""Szablon wyniku z referencji organizatora (klucze, kolejność, null) i składanie wyniku z kandydatów.

Szablon powstaje z pierwszej referencji danej klasy po wyzerowaniu liści: zachowuje klucze
i ich kolejność, listy mają jeden element szkieletowy (kopiowany dla kolejnych indeksów).
Po wypełnieniu usuwamy elementy listy, w których nic nie ustawiono.
To warstwa harnessu, nie kontrakt: kontrakt to openapi.yaml.
"""

from __future__ import annotations

import copy
import functools
from typing import Any

import common  # noqa: F401 — ustawia sys.path na backend
from odwolania2json.loader import load_case_references, load_reference_json

_FILE_FOR = {"appeal": "odwolanie", "power_of_attorney": "pelnomocnictwo", "bank_transfer": "przelew"}


def null_like(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: null_like(v) for k, v in x.items()}
    if isinstance(x, list):
        return [null_like(x[0])] if x else []
    return None


@functools.lru_cache(maxsize=None)
def _template_json(class_id: str) -> str:
    import json

    for ref in load_case_references():
        if ref.document_class == _FILE_FOR[class_id]:
            return json.dumps(null_like(load_reference_json(ref)), ensure_ascii=False)
    raise LookupError(class_id)


def template(class_id: str) -> dict[str, Any]:
    import json

    return json.loads(_template_json(class_id))


def _leaves(x: Any, prefix: str, out: list[str]) -> None:
    if isinstance(x, dict):
        for k, v in x.items():
            _leaves(v, f"{prefix}/{k}", out)
    elif isinstance(x, list):
        if x:
            _leaves(x[0], f"{prefix}/0", out)
    else:
        out.append(prefix)


def allowed_pointers(class_id: str) -> list[str]:
    """Ścieżki liści szablonu (listy jako `/0/`)."""
    out: list[str] = []
    _leaves(template(class_id), "", out)
    return out


def _tokens(pointer: str) -> list[str]:
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer.split("/")[1:]]


def set_pointer(doc: dict[str, Any], pointer: str, value: Any, touched: set[tuple[int, ...]] | None = None) -> bool:
    """Ustawia wartość pod wskaźnikiem; rozszerza listy kopią szkieletu. Zwraca False, gdy ścieżka nie istnieje."""
    cur: Any = doc
    toks = _tokens(pointer)
    for i, t in enumerate(toks):
        last = i == len(toks) - 1
        if isinstance(cur, list):
            if not t.isdigit():
                return False
            idx = int(t)
            while len(cur) <= idx:
                if not cur:
                    return False
                cur.append(copy.deepcopy(_blank(cur[0])))
            nxt = cur[idx]
            if last:
                return False
            cur = nxt
        elif isinstance(cur, dict):
            if t not in cur:
                return False
            if last:
                cur[t] = value
                return True
            cur = cur[t]
        else:
            return False
    return False


def _blank(x: Any) -> Any:
    return null_like(x)


def _all_null(x: Any) -> bool:
    if isinstance(x, dict):
        return all(_all_null(v) for v in x.values())
    if isinstance(x, list):
        return all(_all_null(v) for v in x)
    return x is None


def prune(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: prune(v) for k, v in x.items()}
    if isinstance(x, list):
        return [prune(v) for v in x if not _all_null(v)]
    return x


def get_pointer(doc: Any, pointer: str) -> Any:
    cur = doc
    for t in _tokens(pointer):
        cur = cur[int(t)] if isinstance(cur, list) else cur[t]
    return cur
