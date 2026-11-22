"""Reguły zaskarżonej czynności oraz pól słabych w odwołaniu (Z05).

Pola `czynnosc_powod_id`, `czynnosc_opis` i `czynnosc_dzien` wynikają z reguł, bo
organizator każe ustalać czynność wyłącznie z pierwszego zarzutu, a model często bierze
„Zarzut nr 1” z dalszej części pisma (E09: reguły F1 0,993, LLM v1 0,749). Opis zawsze
pochodzi literalnie ze słownika organizatora, nigdy z modelu.

Dla `numer_bzp` i `pelnomocnik.imie_nazwisko` wartość modelu przechodzi przez normalizację
i **dowód w tekście**: bez dowodu wynik to `None` (nie zmyślamy wartości).

Reguły są strojone na zbiorze rozwojowym (dane syntetyczne i szablonowe), więc ich wynik to
górna granica, nie prognoza na dowolne odwołania.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from dataclasses import dataclass

from odwolania2json_contracts.powody import APPEAL_REASONS

from odwolania2json.domain.normalize import normalize_date

__all__ = [
    "Act",
    "classify_powod",
    "extract_act",
    "find_bzp",
    "first_act_text",
    "normalize_bzp",
    "reason_description",
    "refine_appeal",
    "validate_bzp",
    "validate_representative_name",
]


# --- zaskarżona czynność ---

_MIESIACE = (
    "stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|"
    "listopada|grudnia"
)
# Pierwszeństwo ma pozycja 1) po „polegających na:” (czynność ustala się z pierwszego zarzutu).
_PIERWSZY_ZARZUT = re.compile(
    r"polegając\w+ na:\s*1\)\s*"
    r"(\S.{9,499}?)(?=\s2\)|\sZarzut|\sUzasadnienie|\sZamawiający w dniu|$)"
)
# Zdanie narracyjne jest zapasowe: bywa o innej czynności niż pierwszy zarzut.
_ZDANIE_NARRACYJNE = re.compile(r"Zamawiający w dniu [^.]{1,40}?\s(?:roku|r\.)\s+(.{5,300}?\.)\s")
_STRONA_Z = re.compile(r"Strona \d+ z \d+")
_DATA_CZYNNOSCI = re.compile(
    rf"(\d{{1,2}}\s+(?:{_MIESIACE})\s+(?:19|20)\d{{2}}|\d{{1,2}}[.\-]\d{{1,2}}[.\-](?:19|20)\d{{2}})"
)
_ZANIECHANIE = re.compile(
    r"zaniechani|zaniechał|nie (?:odrzuci|wyklucz|unieważni)|brak (?:odrzuc|wykluczen|unieważn)"
)


@dataclass(frozen=True)
class Act:
    """Zaskarżona czynność: powód, jego kanoniczny opis i dzień (ISO) albo `None`."""

    powod_id: int | None
    opis: str | None
    dzien: str | None


def reason_description(powod_id: int) -> str | None:
    """Kanoniczny opis powodu ze słownika organizatora albo `None` dla nieznanego id."""
    return APPEAL_REASONS.get(powod_id)


def first_act_text(text: str) -> str:
    """Tekst pierwszego zarzutu albo zdania o czynności; pusty, gdy nie ma żadnego."""
    plaski = re.sub(r"\s+", " ", _STRONA_Z.sub(" ", re.sub(r"\s+", " ", text)))
    pierwszy = _PIERWSZY_ZARZUT.search(plaski)
    if pierwszy:
        return pierwszy.group(1)
    narracyjne = _ZDANIE_NARRACYJNE.search(plaski)
    return narracyjne.group(0).strip() if narracyjne else ""


def classify_powod(act: str) -> int | None:
    """Powód 1–12 z tekstu czynności albo `None`, gdy żaden wzorzec nie pasuje.

    Kolejność rozstrzyga: unieważnienie, wykluczenie i odrzucenie (z rozróżnieniem
    „zaniechania”) przed wyborem oferty, modyfikacją, odpowiedziami, projektowanymi
    postanowieniami umowy, OPZ, SWZ i wzorem umowy.
    """
    tekst = act.lower()
    zaniechanie = _ZANIECHANIE.search(tekst) is not None
    if re.search(r"unieważni", tekst):
        return 10 if zaniechanie else 9
    if re.search(r"wyklucz", tekst):
        return 8 if zaniechanie else 3
    if re.search(r"odrzuceni|odrzuci", tekst):
        return 7 if zaniechanie else 1
    if re.search(r"wybór|wyborze|wybrał", tekst):
        return 2
    if re.search(r"zmodyfikował|modyfikacj", tekst):
        return 5
    if re.search(r"odpowied|wyjaśnie", tekst):
        return 6
    if re.search(r"projektowan\w+ postanowie", tekst):
        return 12
    if re.search(r"opis\w* przedmiotu|\bopz\b", tekst):
        return 11
    if re.search(r"specyfikacj|\bswz\b", tekst):
        return 4
    # Wzór umowy bez słowa o SWZ: sama umowa jest przedmiotem zarzutu (z SWZ wygrywa powód 4).
    if re.search(r"wzor\w+ umowy|postanowień umowy|postanowienia umowy", tekst):
        return 12
    return None


def extract_act(text: str) -> Act:
    """Czynność z pierwszego zarzutu: powód, opis ze słownika i dzień.

    Dzień pochodzi z tego samego fragmentu co powód. Brak fragmentu daje same `None`.
    """
    fragment = first_act_text(text)
    powod = classify_powod(fragment) if fragment else None
    data = _DATA_CZYNNOSCI.search(fragment)
    return Act(
        powod_id=powod,
        opis=reason_description(powod) if powod is not None else None,
        dzien=normalize_date(data.group(1)) if data else None,
    )


# --- numer BZP ---

_BZP = re.compile(r"(?<!\d)((?:19|20)\d{2})\s?/\s?BZP\s?(\d{8})(?:/(\d{2}))?(?!\d)")
_DOTYCZY = re.compile(r"dotyczy")
_TYTUL_PISMA = re.compile(r"ODWOŁANIE|O D W O Ł A N I E|Działając|Prezes Krajowej")
# Blok „dotyczy: … ODWOŁANIE” jest krótki; dalszy tytuł oznacza inną wzmiankę.
_MAKS_BLOK_DOTYCZY = 900


def _kanoniczny_bzp(dopasowanie: re.Match[str]) -> str:
    rok, numer, czesc = dopasowanie.groups()
    return f"{rok}/BZP{numer}" + (f"/{czesc}" if czesc else "")


def normalize_bzp(raw: str) -> str | None:
    """Numer BZP w zapisie organizatora `RRRR/BZPNNNNNNNN[/NN]` (bez spacji) albo `None`."""
    dopasowanie = _BZP.fullmatch(raw.strip())
    return _kanoniczny_bzp(dopasowanie) if dopasowanie else None


def find_bzp(text: str) -> str | None:
    """Numer BZP postępowania z bloku „dotyczy: … ODWOŁANIE”.

    Wzmianki o wcześniejszym postępowaniu (poza blokiem) są pomijane.
    """
    plaski = re.sub(r"\s+", " ", text)
    for dotyczy in _DOTYCZY.finditer(plaski):
        tytul = _TYTUL_PISMA.search(plaski, dotyczy.end())
        if tytul is None or tytul.start() - dotyczy.end() > _MAKS_BLOK_DOTYCZY:
            continue
        dopasowanie = _BZP.search(plaski[dotyczy.end() : tytul.start()])
        return _kanoniczny_bzp(dopasowanie) if dopasowanie else None
    return None


def validate_bzp(raw: str | None, text: str) -> str | None:
    """Numer BZP od modelu, jeśli ma poprawny zapis i występuje w tekście (po usunięciu spacji)."""
    if not raw:
        return None
    numer = normalize_bzp(raw)
    if numer is None:
        return None
    return numer if numer in re.sub(r"\s+", "", text) else None


# --- pełnomocnik odwołującego ---

_ROZDZIELACZ_IMION = re.compile(r"\s*(?:[;,]|\boraz\b|\bi\b)\s*")


def _zlozony(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def validate_representative_name(raw: str | None, text: str) -> str | None:
    """Imię i nazwisko pełnomocnika tylko wtedy, gdy występuje w tekście.

    Model bywa zwraca listę osób („A; B”): bierzemy pierwszą, której nazwa występuje w tekście
    (bez rozróżniania wielkości liter i układu spacji). Gdy żadna nie występuje, wynik to `None`.
    """
    if not raw or not raw.strip():
        return None
    gdzie = _zlozony(text)
    kandydaci = [czesc for czesc in _ROZDZIELACZ_IMION.split(raw.strip()) if czesc.strip()]
    for kandydat in kandydaci:
        if _zlozony(kandydat) in gdzie:
            return re.sub(r"\s+", " ", kandydat).strip()
    return None


# --- zastosowanie reguł do wyniku modelu ---


def _section(payload: dict[str, object], key: str) -> dict[str, object] | None:
    value = payload.get(key)
    return value if isinstance(value, dict) else None


def refine_appeal(payload: Mapping[str, object], text: str) -> dict[str, object]:
    """Poprawia słabe pola wyniku odwołania regułami i dowodem w tekście; zwraca kopię.

    - czynność: powód, opis (ze słownika) i dzień z reguł, gdy reguły coś znalazły;
      w przeciwnym razie wartości modelu zostają (parę id–opis pilnuje osobny krok);
    - `numer_bzp`: numer z bloku „dotyczy”, a bez niego wartość modelu z dowodem w tekście;
    - `pelnomocnik.imie_nazwisko`: tylko osoba występująca w tekście, inaczej `None`.

    Brakujące sekcje wyniku pozostają bez zmian.
    """
    result = copy.deepcopy(dict(payload))
    odwolanie = _section(result, "OdwolanieKIO")
    if odwolanie is not None:
        act = extract_act(text)
        if act.powod_id is not None:
            odwolanie["czynnosc_powod_id"] = act.powod_id
            odwolanie["czynnosc_opis"] = act.opis
            if act.dzien is not None:
                odwolanie["czynnosc_dzien"] = act.dzien
    zamowienie = _section(result, "ZamowieniePubliczne")
    if zamowienie is not None:
        raw = zamowienie.get("numer_bzp")
        zamowienie["numer_bzp"] = find_bzp(text) or validate_bzp(
            raw if isinstance(raw, str) else None, text
        )
    odwolujacy = result.get("Odwolujacy")
    if isinstance(odwolujacy, list) and odwolujacy and isinstance(odwolujacy[0], dict):
        pelnomocnik = odwolujacy[0].get("pelnomocnik")
        if isinstance(pelnomocnik, dict):
            raw_name = pelnomocnik.get("imie_nazwisko")
            pelnomocnik["imie_nazwisko"] = validate_representative_name(
                raw_name if isinstance(raw_name, str) else None, text
            )
    return result
