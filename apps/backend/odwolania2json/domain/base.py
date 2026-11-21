"""Wspólne typy warstwy dziedzinowej."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class Ekstrakcja:
    """Wynik ekstrakcji klasy: model dokumentu i dowody źródłowe jego pól.

    ``evidence`` mapuje ścieżkę pola (np. ``przelew_bankowy.kwota``) na parę
    ``(numer strony, pozycja znaku)`` w tekście źródłowym.
    """

    model: BaseModel
    evidence: dict[str, tuple[int, int]]
