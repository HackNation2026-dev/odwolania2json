"""Normalizatory pól dokumentów odwoławczych.

Etykieta w dokumencie rozstrzyga, a suma kontrolna tylko porządkuje kandydatów.
Dane organizatora są syntetyczne i mają losowe cyfry kontrolne, więc normalizatory
zwracają wartość o poprawnej długości, a :func:`checksum_valid` informuje, czy
suma się zgadza.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from datetime import date

__all__ = [
    "checksum_valid",
    "collapse_spaces",
    "find_postepowanie_number",
    "find_value",
    "fold",
    "normalize_account",
    "normalize_amount",
    "normalize_date",
    "normalize_krs",
    "normalize_nip",
    "normalize_pesel",
    "normalize_regon",
    "normalize_ted",
    "strip_quotes",
]


# --- tekst ---

# Litery, które nie rozkładają się na znak bazowy plus znacznik kombinowany.
_ZNAKI_BEZ_DIAKRYTYKOW = {"ł": "l", "Ł": "l"}

# Polskie i proste cudzysłowy oraz apostrofy usuwane przez `strip_quotes`.
_CUDZISLOWY = "„”\"'‘’"


def _fold_znak(znak: str) -> str:
    """Zwraca pojedynczy znak bez diakrytyków, w małej literze.

    Zawsze zwraca dokładnie jeden znak, więc długość tekstu się nie zmienia
    (potrzebne do dopasowania etykiet z zachowaniem pozycji w tekście).
    """
    if znak in _ZNAKI_BEZ_DIAKRYTYKOW:
        return _ZNAKI_BEZ_DIAKRYTYKOW[znak]
    maly = znak.lower()
    if len(maly) != 1:
        maly = maly[0]
    rozbior = unicodedata.normalize("NFD", maly)
    bez_diakrytykow = "".join(c for c in rozbior if not unicodedata.combining(c))
    return bez_diakrytykow[0] if bez_diakrytykow else maly


def _fold_zachowuj_dlugosc(tekst: str) -> str:
    """Jak `fold`, ale bez scalania spacji (pozycje znaków pozostają zgodne)."""
    return "".join(_fold_znak(znak) for znak in tekst)


def collapse_spaces(text: str) -> str:
    """Zastępuje ciągi spacji (wraz z nowymi wierszami) jedną spacją i obcina brzegi."""
    return re.sub(r"\s+", " ", text).strip()


def fold(text: str) -> str:
    """Usuwa diakrytyki, zamienia na małe litery i scala spacje."""
    return collapse_spaces(_fold_zachowuj_dlugosc(text))


def strip_quotes(text: str) -> str:
    """Usuwa polskie i proste cudzysłowy oraz apostrofy."""
    for znak in _CUDZISLOWY:
        text = text.replace(znak, "")
    return text.strip()


# --- identyfikatory ---

_WAGI_NIP = (6, 5, 7, 2, 3, 4, 5, 6, 7)
_WAGI_REGON = (8, 9, 2, 3, 4, 5, 6, 7)
_WAGI_REGON_14 = (2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8)
_WAGI_PESEL = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)


def _blok_cyfr(text: str, dlugosc: int) -> str | None:
    """Pierwszy ciąg dokładnie `dlugosc` cyfr, będący całym ciągiem cyfr w tekście."""
    dopasowanie = re.search(rf"(?<!\d)\d{{{dlugosc}}}(?!\d)", text)
    return dopasowanie.group(0) if dopasowanie else None


def normalize_nip(text: str) -> str | None:
    """NIP: dokładnie 10 cyfr.

    Suma kontrolna nie odrzuca wartości — etykieta w dokumencie rozstrzyga,
    suma jedynie porządkuje kandydatów.
    """
    return _blok_cyfr(text, 10)


def normalize_regon(text: str) -> str | None:
    """REGON: 9 albo 14 cyfr, bez odrzucania po sumie kontrolnej."""
    for dlugosc in (9, 14):
        wartosc = _blok_cyfr(text, dlugosc)
        if wartosc is not None:
            return wartosc
    return None


def normalize_krs(text: str) -> str | None:
    """KRS: 10 cyfr. Numer KRS nie ma sumy kontrolnej."""
    return _blok_cyfr(text, 10)


def normalize_pesel(text: str) -> str | None:
    """PESEL: 11 cyfr, niezależnie od sumy kontrolnej."""
    return _blok_cyfr(text, 11)


def normalize_account(text: str) -> str | None:
    """Numer rachunku: 26 cyfr po usunięciu spacji (prefiks `PL` nie zawiera cyfr)."""
    zwiezly = re.sub(r"\s+", "", text)
    return _blok_cyfr(zwiezly, 26)


# --- daty ---

_MIESIACE = {
    "styczen": 1,
    "stycznia": 1,
    "luty": 2,
    "lutego": 2,
    "marzec": 3,
    "marca": 3,
    "kwiecien": 4,
    "kwietnia": 4,
    "maj": 5,
    "maja": 5,
    "czerwiec": 6,
    "czerwca": 6,
    "lipiec": 7,
    "lipca": 7,
    "sierpien": 8,
    "sierpnia": 8,
    "wrzesien": 9,
    "wrzesnia": 9,
    "pazdziernik": 10,
    "pazdziernika": 10,
    "listopad": 11,
    "listopada": 11,
    "grudzien": 12,
    "grudnia": 12,
}

# Daty słowne: „27 czerwca 2026 roku”.
_DATA_SLOWNA = re.compile(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})")
# Daty liczbowe: „02.07.2026”, „18.03.2026 r.”.
_DATA_LICZBOWA = re.compile(r"(\d{1,2})[.\-](\d{1,2})[.\-](\d{4})")
# Daty w formacie ISO: „2026-03-21”.
_DATA_ISO = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")


def _data_iso(rok: int, miesiac: int, dzien: int) -> str | None:
    """Data w formacie ISO albo `None`, gdy dzień nie istnieje w kalendarzu."""
    try:
        return date(rok, miesiac, dzien).isoformat()
    except ValueError:
        return None


def normalize_date(text: str) -> str | None:
    """Data w formacie ISO `YYYY-MM-DD` (daty słowne, liczbowe i ISO)."""
    if not text:
        return None
    zlozony = fold(text)

    slowna = _DATA_SLOWNA.search(zlozony)
    if slowna:
        miesiac = _MIESIACE.get(slowna.group(2))
        if miesiac is not None:
            wynik = _data_iso(int(slowna.group(3)), miesiac, int(slowna.group(1)))
            if wynik is not None:
                return wynik

    liczbowa = _DATA_LICZBOWA.search(zlozony)
    if liczbowa:
        wynik = _data_iso(int(liczbowa.group(3)), int(liczbowa.group(2)), int(liczbowa.group(1)))
        if wynik is not None:
            return wynik

    iso = _DATA_ISO.search(zlozony)
    if iso:
        wynik = _data_iso(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        if wynik is not None:
            return wynik

    return None


# --- kwoty ---

_KWOTA = re.compile(r"\d+(?:[.,]\d+)?")
_WALUTA = re.compile(r"(?i)(?:zł|zl|pln)(?![a-ząćęłńóśźż])")


def normalize_amount(text: str) -> float | None:
    """Kwota jako liczba: spacje i waluta pomijane, przecinek dziesiętny dopuszczony."""
    if not text:
        return None
    zwiezly = _WALUTA.sub("", re.sub(r"\s+", "", text))
    dopasowanie = _KWOTA.search(zwiezly)
    if dopasowanie is None:
        return None
    try:
        return float(dopasowanie.group(0).replace(",", "."))
    except ValueError:
        return None


# --- numery referencyjne ---

# Numer TED w PDF: „2026/S086-999073”, „2026/S 187-999584” (spacja lub złamanie wiersza).
_TED_Z_PDF = re.compile(r"(?<!\d)(\d{4})/S\s*(\d+)-(\d{6})(?!\d)")
# Numer TED w referencji organizatora: „999073-2026”.
_TED_Z_REFERENCJI = re.compile(r"(?<!\d)(\d{6})-(\d{4})(?!\d)")


def normalize_ted(text: str) -> str | None:
    """Numer TED w formacie referencji organizatora: `NNNNNN-YYYY`.

    Dokument może zawierać kilka numerów TED (np. ogłoszenie porównywalnego
    zamówienia z 2025 roku), więc brany jest pierwszy z nich w tekście.
    """
    if not text:
        return None
    kandydaci: list[tuple[int, str]] = []
    z_pdf = _TED_Z_PDF.search(text)
    if z_pdf:
        kandydaci.append((z_pdf.start(), f"{z_pdf.group(3)}-{z_pdf.group(1)}"))
    z_referencji = _TED_Z_REFERENCJI.search(text)
    if z_referencji:
        kandydaci.append((z_referencji.start(), f"{z_referencji.group(1)}-{z_referencji.group(2)}"))
    if not kandydaci:
        return None
    return min(kandydaci, key=lambda kandydat: kandydat[0])[1]


# Numer postępowania: „ZS.791.2026”, „ZP/PN/48/2026”, „IR.271-35/2026”.
_POSTEPOWANIE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{2,6}(?:[./-][A-Za-z0-9]{1,5}){1,5}(?![A-Za-z0-9])")
_ROK_CZTEROCYFRONY = re.compile(r"(?:19|20)\d{2}")


def _czy_numer_postepowania(kandydat: str) -> bool:
    """Czy kandydat wygląda na numer postępowania (ma cyfry i rok)?"""
    cyfry = re.sub(r"\D", "", kandydat)
    if len(cyfry) < 3:
        return False
    if _ROK_CZTEROCYFRONY.search(kandydat):
        return True
    ostatnia_czesc = re.split(r"[./-]", kandydat)[-1]
    return len(ostatnia_czesc) == 2 and len(cyfry) >= 4


def find_postepowanie_number(text: str) -> str | None:
    """Numer postępowania (np. ``ZP.039.2025``, ``ZP/PN/48/2026``, ``IR.271-35/2026``)."""
    for kandydat in _POSTEPOWANIE.finditer(text):
        if _czy_numer_postepowania(kandydat.group(0)):
            return kandydat.group(0)
    return None


# --- wyszukiwanie po etykiecie ---

_SEPARATORY_WARTOSCI = ":;=–—-."


def _find_label(text: str, label: str) -> int | None:
    """Pozycja pierwszej etykiety w tekście (bez rozróżniania wielkości liter
    i diakrytyków), albo `None`."""
    zlozony_tekst = _fold_zachowuj_dlugosc(text)
    zlozona_etykieta = _fold_zachowuj_dlugosc(label)
    if not zlozona_etykieta:
        return None
    poczatek = 0
    while True:
        pozycja = zlozony_tekst.find(zlozona_etykieta, poczatek)
        if pozycja < 0:
            return None
        przed = text[pozycja - 1] if pozycja > 0 else " "
        po = text[pozycja + len(label)] if pozycja + len(label) < len(text) else " "
        if not przed.isalnum() and not po.isalnum():
            return pozycja
        poczatek = pozycja + 1


def _pierwsza_wartosc(fragment: str) -> str:
    """Pierwsza niepusta wartość w fragmencie tekstu (bez separatorów etykiety)."""
    for linia in fragment.splitlines():
        wartosc = linia.strip().lstrip(_SEPARATORY_WARTOSCI).strip()
        if wartosc:
            return wartosc
    return ""


def find_value(text: str, labels: Sequence[str], window: int = 120) -> str | None:
    """Wartość pola: pierwsza pasująca etykieta, potem tekst w oknie znaków.

    Etykiety sprawdzane są w podanej kolejności; dla każdej bierze się jej
    pierwsze wystąpienie. Wartość pochodzi z pierwszego niepustego wiersza
    po etykiecie (bez odstępów i separatorów).
    """
    for label in labels:
        pozycja = _find_label(text, label)
        if pozycja is None:
            continue
        koniec = pozycja + len(label)
        wartosc = _pierwsza_wartosc(text[koniec : koniec + window])
        if wartosc:
            return wartosc
    return None


# --- sumy kontrolne: sygnał rankingowy, nigdy filtr twardy ---

def _suma_nip(cyfry: str) -> bool:
    """Czy 10 cyfr ma poprawną sumę kontrolną NIP (suma 10 oznacza brak NIP-u)."""
    if len(cyfry) != 10:
        return False
    suma = sum(int(c) * waga for c, waga in zip(cyfry[:9], _WAGI_NIP)) % 11
    return suma != 10 and suma == int(cyfry[9])


def _suma_regon(cyfry: str) -> bool:
    """Czy 9 albo 14 cyfr ma poprawną sumę kontrolną REGON."""
    if len(cyfry) == 9:
        suma = sum(int(c) * waga for c, waga in zip(cyfry[:8], _WAGI_REGON)) % 11
        oczekiwana = 0 if suma == 10 else suma
        return oczekiwana == int(cyfry[8])
    if len(cyfry) == 14:
        if not _suma_regon(cyfry[:9]):
            return False
        suma = sum(int(c) * waga for c, waga in zip(cyfry[:13], _WAGI_REGON_14)) % 11
        oczekiwana = 0 if suma == 10 else suma
        return oczekiwana == int(cyfry[13])
    return False


def _suma_pesel(cyfry: str) -> bool:
    """Czy 11 cyfr ma poprawną sumę kontrolną PESEL."""
    if len(cyfry) != 11:
        return False
    suma = sum(int(c) * waga for c, waga in zip(cyfry[:10], _WAGI_PESEL)) % 10
    return (10 - suma) % 10 == int(cyfry[10])


def _suma_iban(value: str) -> bool:
    """Czy wartość ma poprawną sumę kontrolną IBAN (mod 97).

    Przyjmuje pełny IBAN z kodem kraju (``PL54…``) albo 26 cyfr polskiego
    rachunku (bez kodu kraju).
    """
    zwiezly = re.sub(r"\s+", "", value).upper()
    if re.fullmatch(r"[A-Z]{2}\d+", zwiezly):
        iban = zwiezly
    elif re.fullmatch(r"\d{26}", zwiezly):
        iban = f"PL{zwiezly}"
    else:
        return False
    przestawiony = iban[4:] + iban[:4]
    liczby = "".join(str(int(znak, 36)) for znak in przestawiony)
    return int(liczby) % 97 == 1


def checksum_valid(kind: str, value: str) -> bool:
    """Czy suma kontrolna danego rodzaju zgadza się z wartością.

    ``kind`` to jedno z ``nip``, ``regon``, ``pesel``, ``iban``. Wynik służy
    wyłącznie do porządkowania kandydatów — nigdy do odrzucania wartości,
    bo dane organizatora mają losowe cyfry kontrolne.
    """
    cyfry = re.sub(r"\D", "", value)
    if kind == "nip":
        return _suma_nip(cyfry)
    if kind == "regon":
        return _suma_regon(cyfry)
    if kind == "pesel":
        return _suma_pesel(cyfry)
    if kind == "iban":
        return _suma_iban(value)
    return False
