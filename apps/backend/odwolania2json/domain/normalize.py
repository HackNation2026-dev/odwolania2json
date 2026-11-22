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
    "rank_by_checksum",
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
    maly = znak.lower()  # „İ” daje dwa znaki: „i” i kropkę kombinującą, którą usuwa NFD niżej
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


# Separator grup cyfr w identyfikatorze: pojedyncza spacja, twarda spacja albo myślnik.
_SEP = r"[ \u00a0\-]"


def _wzorzec_grupowy(grupy: Sequence[int]) -> str:
    """Wzorzec cyfr w grupach o podanych długościach, rozdzielonych jednym separatorem."""
    return _SEP.join(rf"\d{{{rozmiar}}}" for rozmiar in grupy)


def _blok_cyfr(text: str, dlugosc: int, uklady: Sequence[Sequence[int]] = ()) -> str | None:
    """Pierwszy numer o `dlugosc` cyfrach: ciągły albo w jednym z dozwolonych układów grup.

    Numer nie może sąsiadować z cyfrą (to fragment dłuższego ciągu). Z kilku kandydatów
    wygrywa ten, który zaczyna się najwcześniej; przy remisie ciągły. Układy grup są
    jawne (np. NIP 3-3-2-2), więc daty i inne liczby z myślnikami nie są brane za numery.
    """
    wzorce = [rf"(?<!\d)\d{{{dlugosc}}}(?!\d)"]
    # Zapis grupowy nie może być końcówką ani początkiem dłuższego ciągu grup (`… 65 7`).
    wzorce.extend(
        rf"(?<!\d)(?<!\d{_SEP}){_wzorzec_grupowy(grupy)}(?!\d)(?!{_SEP}\d)" for grupy in uklady
    )
    najlepszy: re.Match[str] | None = None
    for wzorzec in wzorce:
        dopasowanie = re.search(wzorzec, text)
        if dopasowanie and (najlepszy is None or dopasowanie.start() < najlepszy.start()):
            najlepszy = dopasowanie
    if najlepszy is None:
        return None
    return re.sub(r"\D", "", najlepszy.group(0))


# Układy grup zapisu: NIP „999-928-40-65” i „999-92-84-065”, REGON „999 642 785”
# i „999 642 785 00123”, KRS „9999 405 188” i „999 940 5188”.
_UKLADY_NIP = ((3, 3, 2, 2), (3, 2, 2, 3))
_UKLADY_REGON_9 = ((3, 3, 3),)
_UKLADY_REGON_14 = ((3, 3, 3, 5),)
_UKLADY_KRS = ((4, 3, 3), (3, 3, 4))


def normalize_nip(text: str) -> str | None:
    """NIP: dokładnie 10 cyfr, także w zapisie z myślnikami lub spacjami (`999-928-40-65`).

    Suma kontrolna nie odrzuca wartości — etykieta w dokumencie rozstrzyga,
    suma jedynie porządkuje kandydatów (:func:`rank_by_checksum`).
    """
    return _blok_cyfr(text, 10, _UKLADY_NIP)


def normalize_regon(text: str) -> str | None:
    """REGON: 9 albo 14 cyfr (też z grupami), bez odrzucania po sumie kontrolnej."""
    for dlugosc, uklady in ((9, _UKLADY_REGON_9), (14, _UKLADY_REGON_14)):
        wartosc = _blok_cyfr(text, dlugosc, uklady)
        if wartosc is not None:
            return wartosc
    return None


def normalize_krs(text: str) -> str | None:
    """KRS: 10 cyfr, także w grupach (`9999 405 188`). Numer KRS nie ma sumy kontrolnej."""
    return _blok_cyfr(text, 10, _UKLADY_KRS)


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

_MIESIAC = r"[a-z]+"
# Daty słowne: „27 czerwca 2026 roku”.
_DATA_SLOWNA = re.compile(rf"(?<!\d)(\d{{1,2}})\s+({_MIESIAC})\s+(\d{{4}})(?!\d)")
# Daty liczbowe z rokiem czterocyfrowym: „02.07.2026”, „18-03-2026 r.”, „01/04/2026”.
_DATA_LICZBOWA = re.compile(r"(?<!\d)(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})(?!\d)")
# Daty liczbowe z rokiem dwucyfrowym: „01.04.26”.
_DATA_LICZBOWA_KROTKA = re.compile(r"(?<!\d)(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2})(?!\d)")
# Daty w formacie ISO i pochodnych: „2026-03-21”, „2026/04/01”, „2026.04.01”.
_DATA_ISO = re.compile(r"(?<!\d)(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})(?!\d)")
# Miesiąc rzymski (wielkimi literami, bo „i” to spójnik): „1 IV 2026”, „01.IV.26”.
_RZYMSKIE = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
}
_DATA_RZYMSKA = re.compile(
    r"(?<!\d)(\d{1,2})[\s.\-/]+(XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)\b[\s.\-/]+(\d{4}|\d{2})(?!\d)"
)

# Dzień słowny w dopełniaczu, już bez diakrytyków: „pierwszego”, „dwudziestego piątego”.
_DNI_DO_19 = (
    "pierwszego",
    "drugiego",
    "trzeciego",
    "czwartego",
    "piatego",
    "szostego",
    "siodmego",
    "osmego",
    "dziewiatego",
    "dziesiatego",
    "jedenastego",
    "dwunastego",
    "trzynastego",
    "czternastego",
    "pietnastego",
    "szesnastego",
    "siedemnastego",
    "osiemnastego",
    "dziewietnastego",
)


def _dni_slowne() -> dict[str, int]:
    dni = {slowo: numer for numer, slowo in enumerate(_DNI_DO_19, start=1)}
    dni["dwudziestego"] = 20
    dni["trzydziestego"] = 30
    for numer, slowo in enumerate(_DNI_DO_19[:9], start=1):
        dni[f"dwudziestego {slowo}"] = 20 + numer
    dni["trzydziestego pierwszego"] = 31
    return dni


_DNI_SLOWNE = _dni_slowne()
_DATA_DZIEN_SLOWNY = re.compile(
    "(?<![a-z])("
    + "|".join(re.escape(fraza) for fraza in sorted(_DNI_SLOWNE, key=len, reverse=True))
    + rf")\s+({_MIESIAC})\s+(\d{{4}})(?!\d)"
)


def _data_iso(rok: int, miesiac: int, dzien: int) -> str | None:
    """Data w formacie ISO albo `None`, gdy dzień nie istnieje w kalendarzu."""
    try:
        return date(rok, miesiac, dzien).isoformat()
    except ValueError:
        return None


def _rok_z_dwoch_cyfr(rok: str) -> int:
    """Rok dwucyfrowy: 00–69 to 2000–2069, 70–99 to 1970–1999 (jak `strptime`)."""
    liczba = int(rok)
    return 2000 + liczba if liczba <= 69 else 1900 + liczba


def _rok(rok: str) -> int:
    return int(rok) if len(rok) == 4 else _rok_z_dwoch_cyfr(rok)


def normalize_date(text: str) -> str | None:
    """Data w formacie ISO `YYYY-MM-DD`.

    Rozpoznaje daty słowne (`27 czerwca 2026`, `pierwszego kwietnia 2026`), liczbowe
    (`02.07.2026`, `01.04.26`), z miesiącem rzymskim (`1 IV 2026`) i ISO (`2026/04/01`).
    Pierwszy wzorzec, który daje istniejącą datę kalendarzową, rozstrzyga.
    """
    if not text:
        return None
    zlozony = fold(text)
    kandydaci: list[tuple[int, int | None, int]] = []

    for dopasowanie in _DATA_SLOWNA.finditer(zlozony):
        kandydaci.append(
            (
                int(dopasowanie.group(3)),
                _MIESIACE.get(dopasowanie.group(2)),
                int(dopasowanie.group(1)),
            )
        )
    for dopasowanie in _DATA_DZIEN_SLOWNY.finditer(zlozony):
        kandydaci.append(
            (
                int(dopasowanie.group(3)),
                _MIESIACE.get(dopasowanie.group(2)),
                _DNI_SLOWNE[dopasowanie.group(1)],
            )
        )
    for dopasowanie in _DATA_RZYMSKA.finditer(text):
        kandydaci.append(
            (_rok(dopasowanie.group(3)), _RZYMSKIE[dopasowanie.group(2)], int(dopasowanie.group(1)))
        )
    for dopasowanie in _DATA_LICZBOWA.finditer(zlozony):
        kandydaci.append(
            (int(dopasowanie.group(3)), int(dopasowanie.group(2)), int(dopasowanie.group(1)))
        )
    for dopasowanie in _DATA_LICZBOWA_KROTKA.finditer(zlozony):
        kandydaci.append(
            (
                _rok_z_dwoch_cyfr(dopasowanie.group(3)),
                int(dopasowanie.group(2)),
                int(dopasowanie.group(1)),
            )
        )
    for dopasowanie in _DATA_ISO.finditer(zlozony):
        kandydaci.append(
            (int(dopasowanie.group(1)), int(dopasowanie.group(2)), int(dopasowanie.group(3)))
        )

    for rok, miesiac, dzien in kandydaci:
        if miesiac is None:
            continue
        wynik = _data_iso(rok, miesiac, dzien)
        if wynik is not None:
            return wynik
    return None


# --- kwoty ---

_KWOTA = re.compile(r"\d+(?:[.,]\d+)*")
_WALUTA = re.compile(r"(?i)(?:zł|zl|pln)")


def _grupy_tysiecy(cyfry: str, separator: str) -> bool:
    """Czy `cyfry` to 1–3 cyfry i grupy po dokładnie 3 cyfry rozdzielone `separator`."""
    return re.fullmatch(rf"\d{{1,3}}(?:{re.escape(separator)}\d{{3}})+", cyfry) is not None


def _liczba_z_separatorami(token: str) -> float | None:
    """Wartość liczby z kropkami i przecinkami albo `None`, gdy zapis jest niejednoznaczny.

    Gdy występują oba znaki, ostatni jest dziesiętny, a drugi musi rozdzielać tysiące
    (`1.000,50`, `1,000.50`). Przy jednym znaku powtórzonym są to tysiące (`1.000.000`).
    Pojedynczy znak z trzema cyframi po nim i 1–3 cyframi przed (`1.000`, `1,000`) to
    tysiące; w pozostałych przypadkach to ułamek (`3,5`, `1000,5`, `0,500`).
    """
    separatory = re.findall(r"[.,]", token)
    if not separatory:
        return float(token)
    dziesietny = separatory[-1]
    drugi = "," if dziesietny == "." else "."
    if drugi in separatory:
        calosc, _, ulamek = token.rpartition(dziesietny)
        if not _grupy_tysiecy(calosc, drugi):
            return None
        return float(calosc.replace(drugi, "") + "." + ulamek)
    if len(separatory) > 1:
        return float(token.replace(dziesietny, "")) if _grupy_tysiecy(token, dziesietny) else None
    calosc, _, ulamek = token.partition(dziesietny)
    if len(ulamek) == 3 and len(calosc) <= 3 and calosc[0] != "0":
        return float(calosc + ulamek)
    return float(calosc + "." + ulamek)


def normalize_amount(text: str) -> float | None:
    """Kwota jako liczba: spacje i waluta pomijane, przecinek dziesiętny dopuszczony.

    Separator tysięcy (`1.000,50`, `1,000.50`) jest rozpoznawany; niejednoznaczny zapis
    daje `None`, nigdy cichą wartość błędną.
    """
    if not text:
        return None
    zwiezly = _WALUTA.sub("", re.sub(r"\s+", "", text))
    dopasowanie = _KWOTA.search(zwiezly)
    if dopasowanie is None:
        return None
    return _liczba_z_separatorami(dopasowanie.group(0))


# --- numery referencyjne ---

# Numer TED w PDF: „2026/S086-999073”, „2026/S 187-999584”, „2026 /S 224 - 999211”
# (spacje lub złamania wiersza wokół „/S” i myślnika).
_TED_Z_PDF = re.compile(r"(?<!\d)(\d{4})\s*/\s*S\s*(\d+)\s*-\s*(\d{6})(?!\d)")
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
_POSTEPOWANIE = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z]{2,6}(?:[./-][A-Za-z0-9]{1,5}){1,5}(?![A-Za-z0-9])"
)
_ROK_CZTEROCYFRONY = re.compile(r"(?:19|20)\d{2}")


def _czy_numer_postepowania(kandydat: str) -> bool:
    """Czy kandydat wygląda na numer postępowania (ma cyfry i rok)?"""
    cyfry = re.sub(r"\D", "", kandydat)
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
    suma = sum(int(c) * waga for c, waga in zip(cyfry, _WAGI_NIP, strict=False)) % 11
    # Suma 10 oznacza brak poprawnego NIP-u i nie równa się żadnej cyfrze.
    return suma == int(cyfry[9])


def _suma_regon(cyfry: str) -> bool:
    """Czy 9 albo 14 cyfr ma poprawną sumę kontrolną REGON."""
    if len(cyfry) == 9:
        suma = sum(int(c) * waga for c, waga in zip(cyfry, _WAGI_REGON, strict=False)) % 11
        oczekiwana = 0 if suma == 10 else suma
        return oczekiwana == int(cyfry[8])
    if len(cyfry) == 14:
        if not _suma_regon(cyfry[:9]):
            return False
        suma = sum(int(c) * waga for c, waga in zip(cyfry, _WAGI_REGON_14, strict=False)) % 11
        oczekiwana = 0 if suma == 10 else suma
        return oczekiwana == int(cyfry[13])
    return False


def _suma_pesel(cyfry: str) -> bool:
    """Czy 11 cyfr ma poprawną sumę kontrolną PESEL."""
    if len(cyfry) != 11:
        return False
    suma = sum(int(c) * waga for c, waga in zip(cyfry, _WAGI_PESEL, strict=False)) % 10
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


def rank_by_checksum(kind: str, candidates: Sequence[str]) -> list[str]:
    """Porządkuje kandydatów: z poprawną sumą kontrolną na początku, bez odrzucania.

    Kolejność wewnątrz obu grup zostaje (sortowanie stabilne). Suma jest tylko sygnałem
    rankingowym: w referencjach organizatora poprawną sumę ma 64% NIP, 70% REGON i 34% IBAN,
    więc filtr twardy odrzuciłby prawdziwe wartości (E19).
    """
    return sorted(candidates, key=lambda kandydat: not checksum_valid(kind, kandydat))
