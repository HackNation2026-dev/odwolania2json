"""Zamrożony podział 60 spraw organizatora na część rozwojową i kontrolną.

Podział jest po całych sprawach: wszystkie pliki jednej sprawy trafiają do tej
samej strony, bo rodzina duplikatów rozdzielona między strony zawyżyłaby wynik
kontrolny. Plik ``data/podzial.json`` jest źródłem prawdy; test SHA-256 blokuje
ciche zmiany, więc zmiana podziału wymaga świadomej zmiany testu.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

__all__ = ["DATA_SPLIT", "Split", "load_split"]

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_SPLIT = REPO_ROOT / "data" / "podzial.json"
WSZYSTKIE_SPRAWY = frozenset(f"przyklad_{numer:02d}" for numer in range(1, 61))


class _PlikPodzialu(BaseModel):
    """Granica pliku: surowe listy identyfikatorów przed zamianą na zbiory."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metoda: str
    rozwojowy: list[str]
    kontrolny: list[str]

    @model_validator(mode="after")
    def _sprawdz_pokrycie(self) -> _PlikPodzialu:
        """Wymaga 60 unikalnych spraw, każda dokładnie w jednej stronie.

        Sprawdzane są listy, a nie zbiory, bo zbiór po cichu zgubiłby duplikat
        wpisany dwa razy w tej samej stronie.
        """
        nakladajace = sorted(set(self.rozwojowy) & set(self.kontrolny))
        if nakladajace:
            raise ValueError(f"sprawy w obu stronach podziału: {', '.join(nakladajace)}")
        wszystkie = [*self.rozwojowy, *self.kontrolny]
        if len(set(wszystkie)) != len(wszystkie):
            raise ValueError("identyfikatory spraw w podziale się powtarzają")
        brakujace = sorted(WSZYSTKIE_SPRAWY - set(wszystkie))
        nadmiarowe = sorted(set(wszystkie) - WSZYSTKIE_SPRAWY)
        if brakujace or nadmiarowe:
            raise ValueError(
                f"podział nie pokrywa 60 spraw: brak {brakujace}, nadmiar {nadmiarowe}"
            )
        return self


class Split(BaseModel):
    """Niezmienny podział: zbiory identyfikatorów ``przyklad_NN`` po obu stronach."""

    model_config = ConfigDict(frozen=True)

    rozwojowy: frozenset[str]
    kontrolny: frozenset[str]


def load_split(path: Path = DATA_SPLIT) -> Split:
    """Wczytuje i waliduje podział; błąd zgłaszany jawnie, bez cichego zestawu zastępczego."""
    plik = _PlikPodzialu.model_validate_json(path.read_bytes())
    return Split(rozwojowy=frozenset(plik.rozwojowy), kontrolny=frozenset(plik.kontrolny))
