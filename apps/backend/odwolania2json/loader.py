"""Loader 60 spraw testowych organizatora (tylko odczyt).

Referencje (`odwolanie.json`, `pelnomocnictwo.json`, `przelew.json`) to wzorce,
z którymi porównuje się wyniki ekstrakcji. Część referencji organizator poprawił
w osobnej aktualizacji; poprawki nakładamy w pamięci, bo oryginały w
`docs/02-materialy/` nie mogą się zmieniać.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

__all__ = [
    "CORRECTIONS_DIR",
    "MATERIALS_DIR",
    "CaseReference",
    "DocumentClass",
    "input_to_reference_name",
    "load_case_references",
    "load_reference_json",
    "result_name_for",
]

DocumentClass = Literal["odwolanie", "pelnomocnictwo", "przelew", "obcy"]

_REPO_ROOT = Path(__file__).resolve().parents[3]
MATERIALS_DIR = _REPO_ROOT / "docs" / "02-materialy" / "organizator-uzp"
CORRECTIONS_DIR = (
    _REPO_ROOT / "docs" / "02-materialy" / "organizator-uzp-aktualizacje" / "main-7590db8"
)

_NEGATYWNE = "negatywne"

# Trzy znane nazwy PDF-ów i ich klasa oraz plik referencji. `potwierdzenie_przelewu.pdf`
# ma referencję `przelew.json` — jedyny przypadek, w którym nazwy się nie pokrywają.
_KLASY_WEJSCIA: dict[str, tuple[DocumentClass, str]] = {
    "odwolanie.pdf": ("odwolanie", "odwolanie.json"),
    "pelnomocnictwo.pdf": ("pelnomocnictwo", "pelnomocnictwo.json"),
    "potwierdzenie_przelewu.pdf": ("przelew", "przelew.json"),
}

# Sprawy, w których organizator poprawił `odwolanie.json` (opis czynności).
_POPRAWIONE_SPRAWY = frozenset(
    {"przyklad_19", "przyklad_23", "przyklad_25", "przyklad_44", "przyklad_55"}
)


class CaseReference(BaseModel):
    """Jeden dokument wejściowy sprawy wraz z plikiem referencji."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    input_name: str
    document_class: DocumentClass
    reference_name: str | None


def input_to_reference_name(input_name: str) -> str | None:
    """Nazwa pliku referencji dla PDF-a wejściowego albo `None` dla obcego dokumentu."""
    wpis = _KLASY_WEJSCIA.get(input_name)
    return wpis[1] if wpis else None


def result_name_for(input_name: str) -> str:
    """Nazwa pliku wyniku: stem wejścia z rozszerzeniem `.json`."""
    return f"{Path(input_name).stem}.json"


def _dokumenty_sprawy(katalog_sprawy: Path) -> list[tuple[str, DocumentClass, str]]:
    """Trzy znane PDF-y istniejące w katalogu sprawy, w stałej kolejności."""
    dokumenty: list[tuple[str, DocumentClass, str]] = []
    for input_name, (klasa, referencja) in _KLASY_WEJSCIA.items():
        if (katalog_sprawy / input_name).is_file():
            dokumenty.append((input_name, klasa, referencja))
    return dokumenty


def load_case_references(
    materials_dir: Path = MATERIALS_DIR,
    corrections_dir: Path | None = CORRECTIONS_DIR,
) -> list[CaseReference]:
    """Wpisy wszystkich spraw (klasy znanych PDF-ów) oraz obcych PDF-ów z `dane/negatywne/`.

    Poprawki nie zmieniają listy wpisów, więc `corrections_dir` jest przyjmowany
    dla spójnej sygnatury z :func:`load_reference_json`, ale nie jest tu czytany.
    Sprawa nie musi mieć wszystkich trzech PDF-ów; wpis powstaje z istniejących plików.
    """
    dane = materials_dir / "dane"
    refs: list[CaseReference] = []
    for katalog_sprawy in sorted(dane.glob("przyklad_*")):
        if not katalog_sprawy.is_dir():
            continue
        for input_name, klasa, referencja in _dokumenty_sprawy(katalog_sprawy):
            refs.append(
                CaseReference(
                    case_id=katalog_sprawy.name,
                    input_name=input_name,
                    document_class=klasa,
                    reference_name=referencja,
                )
            )
    for pdf in sorted((dane / _NEGATYWNE).glob("*.pdf")):
        refs.append(
            CaseReference(
                case_id=_NEGATYWNE,
                input_name=pdf.name,
                document_class="obcy",
                reference_name=None,
            )
        )
    return refs


def load_reference_json(
    ref: CaseReference,
    materials_dir: Path = MATERIALS_DIR,
    corrections_dir: Path | None = CORRECTIONS_DIR,
) -> dict[str, object]:
    """Treść referencji z naniesionymi poprawkami organizatora (tylko odczyt).

    Dla obcego dokumentu zwraca `{}`. Brakujący plik referencji dla pozostałych
    klas jest błędem (`FileNotFoundError`), a nie cichym pustym wynikiem.
    """
    if ref.reference_name is None:
        return {}
    if (
        ref.document_class == "odwolanie"
        and corrections_dir is not None
        and ref.case_id in _POPRAWIONE_SPRAWY
    ):
        sciezka = corrections_dir / "dane" / ref.case_id / ref.reference_name
    else:
        sciezka = materials_dir / "dane" / ref.case_id / ref.reference_name
    tresc = json.loads(sciezka.read_text(encoding="utf-8"))
    if not isinstance(tresc, dict):
        raise ValueError(f"referencja {sciezka} nie jest obiektem JSON")
    return tresc
