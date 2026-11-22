"""Testy normalizatorów pól.

Wartości pochodzą z materiałów organizatora (`docs/02-materialy/organizator-uzp/dane`).
Etykieta w dokumencie rozstrzyga: normalizatory zwracają wartość o poprawnej
długości, a `checksum_valid` służy wyłącznie do porządkowania kandydatów.
"""

from __future__ import annotations

import pytest
from odwolania2json.domain.normalize import (
    checksum_valid,
    collapse_spaces,
    find_postepowanie_number,
    find_value,
    fold,
    normalize_account,
    normalize_amount,
    normalize_date,
    normalize_krs,
    normalize_nip,
    normalize_pesel,
    normalize_regon,
    normalize_ted,
    rank_by_checksum,
    strip_quotes,
)


def test_normalize_ted_from_pdf_format():
    assert normalize_ted("2026/S086-999073") == "999073-2026"


def test_normalize_account_removes_spaces():
    assert normalize_account("PL54 7164 9675 2472 1141 8071 4012") == "54716496752472114180714012"


def test_normalize_date_polish_words():
    assert normalize_date("27 czerwca 2026 roku") == "2026-06-27"


def test_normalize_date_dotted():
    assert normalize_date("02.07.2026") == "2026-07-02"


def test_normalize_pesel_keeps_eleven_digits():
    assert normalize_pesel("85071204278") == "85071204278"


def test_normalize_pesel_keeps_value_without_valid_checksum():
    # etykieta rozstrzyga, suma kontrolna tylko porzadkuje kandydatow
    assert normalize_pesel("85071204279") == "85071204279"


def test_normalize_nip_keeps_value_without_valid_checksum():
    # wartosc z materialow organizatora ma byc zwrocona niezależnie od sumy kontrolnej
    assert normalize_nip("9997518659") == "9997518659"


def test_normalize_regon_keeps_value_without_valid_checksum():
    assert normalize_regon("999184816") == "999184816"


def test_normalize_account_keeps_value_without_valid_iban_sum():
    assert normalize_account("68438223049992295262834736") == "68438223049992295262834736"


def test_checksum_valid_is_only_a_ranking_signal():
    # checksum_valid("nip", ...) rozroznia poprawne od blednych, ale nie odrzuca zlych
    assert checksum_valid("pesel", "85071204278") is True


def test_normalize_nip_accepts_synthetic_prefix():
    assert normalize_nip("9999284065") == "9999284065"


def test_normalize_amount_handles_spaces_and_cents():
    assert normalize_amount("1 000,50 zł") == 1000.5


def test_find_value_uses_label_window():
    assert find_value("KRS: 9999405188\nNIP: 9999284065", ["KRS"]) == "9999405188"


# --- tekst ---


def test_fold_removes_diacritics_and_lowercases():
    assert fold("P E Ł N O M O C N I C T W O") == "p e l n o m o c n i c t w o"


def test_fold_collapses_spaces():
    assert fold("Zamawiający   S.A.\n") == "zamawiajacy s.a."


def test_collapse_spaces_joins_lines():
    assert collapse_spaces("Zakup\ni dostawa  sprzętu") == "Zakup i dostawa sprzętu"


def test_strip_quotes_removes_polish_quotes():
    assert strip_quotes("„Zakup i dostawa sprzętu”") == "Zakup i dostawa sprzętu"


def test_strip_quotes_removes_straight_quotes():
    assert strip_quotes("\"Zakup\" i 'dostawa'") == "Zakup i dostawa"


# --- identyfikatory ---


def test_normalize_nip_takes_first_ten_digits_from_line():
    """W PDF identyfikatory występują w jednym wierszu, po etykiecie."""
    assert normalize_nip("KRS: 9999405188, NIP: 9999284065, REGON: 999642785") == "9999405188"


def test_normalize_nip_rejects_wrong_length():
    assert normalize_nip("999928406") is None


def test_normalize_krs_keeps_ten_digits():
    assert normalize_krs("9999405188") == "9999405188"


def test_normalize_regon_accepts_fourteen_digits():
    assert normalize_regon("12345678512347") == "12345678512347"


def test_normalize_regon_rejects_wrong_length():
    assert normalize_regon("99918481") is None


def test_normalize_pesel_rejects_wrong_length():
    assert normalize_pesel("8507120427") is None


def test_normalize_account_takes_number_from_payment_text():
    """Potwierdzenie przelewu podaje rachunek z prefiksem `PL` w osobnym wierszu."""
    assert normalize_account("PL05470680287581539721455024") == "05470680287581539721455024"


def test_normalize_account_rejects_wrong_length():
    assert normalize_account("0547068028758153972145") is None


# --- sumy kontrolne: tylko sygnał rankingowy ---


def test_checksum_valid_nip_distinguishes_valid_and_invalid():
    # Oba NIP-y pochodzą z materiałów organizatora.
    assert checksum_valid("nip", "9999284065") is True
    assert checksum_valid("nip", "9990264287") is False


def test_checksum_valid_regon_uses_official_weights():
    assert checksum_valid("regon", "123456785") is True
    assert checksum_valid("regon", "123456786") is False


def test_checksum_valid_regon_on_organizer_data():
    assert checksum_valid("regon", "999184816") is True
    assert checksum_valid("regon", "999015873") is False


def test_checksum_valid_regon_accepts_fourteen_digits():
    assert checksum_valid("regon", "12345678512347") is True


def test_checksum_valid_pesel_distinguishes_valid_and_invalid():
    assert checksum_valid("pesel", "85071204278") is True
    assert checksum_valid("pesel", "85071204279") is False


def test_checksum_valid_iban_uses_mod_97():
    assert checksum_valid("iban", "54716496752472114180714012") is True
    assert checksum_valid("iban", "68438223049992295262834736") is False


def test_checksum_valid_accepts_full_iban():
    assert checksum_valid("iban", "PL54716496752472114180714012") is True


def test_checksum_valid_is_false_for_unknown_kind():
    assert checksum_valid("krs", "9999405188") is False


# --- daty ---


def test_normalize_date_accepts_iso_text():
    assert normalize_date("2026-03-21") == "2026-03-21"


def test_normalize_date_accepts_year_suffix():
    assert normalize_date("18.03.2026 r.") == "2026-03-18"
    assert normalize_date("06.11.2026 r.") == "2026-11-06"


def test_normalize_date_accepts_single_digit_day():
    assert normalize_date("7 marca 2026 roku") == "2026-03-07"


def test_normalize_date_reads_date_from_header_line():
    assert normalize_date("Gdańsk, dnia 3 września 2026 roku") == "2026-09-03"


def test_normalize_date_reads_october():
    """Nazwa miesiąca z diakrytyką trafia do słownika już złożonego (`fold`)."""
    assert normalize_date("Kraków, dnia 28 października 2026 roku") == "2026-10-28"


def test_normalize_date_rejects_impossible_date():
    assert normalize_date("31.02.2026") is None


def test_normalize_date_returns_none_without_date():
    assert normalize_date("brak danych") is None


# --- kwoty ---


def test_normalize_amount_accepts_pln():
    assert normalize_amount("200,00 PLN") == 200.0


def test_normalize_amount_accepts_integer():
    assert normalize_amount("200") == 200.0


def test_normalize_amount_returns_none_without_number():
    assert normalize_amount("brak kwoty") is None


# --- numery referencyjne ---


def test_normalize_ted_accepts_reference_format():
    assert normalize_ted("numer ogłoszenia TED: 999137-2026") == "999137-2026"


def test_normalize_ted_accepts_space_after_series_marker():
    """W PDF bywa „2026/S 187-999584”, a czasem ze złamaniem wiersza po „S”."""
    assert normalize_ted("ogłoszenie nr 2026/S 187-999584") == "999584-2026"
    assert normalize_ted("ogłoszenie nr 2026/S\r\n199-999065") == "999065-2026"


def test_normalize_ted_takes_first_number_in_text():
    """Dokument może cytować ogłoszenie porównywalnego zamówienia z 2025 roku."""
    tekst = (
        "ogłoszenie w Dzienniku Urzędowym Unii Europejskiej nr 999165-2026 "
        "postępowanie prowadzone przez inny podmiot, pod numerem 2025/S 079-998721"
    )
    assert normalize_ted(tekst) == "999165-2026"


def test_find_postepowanie_number_reads_dotted_format():
    assert (
        find_postepowanie_number("nr referencyjny sprawy: ZS.791.2026, ogłoszenie") == "ZS.791.2026"
    )


def test_find_postepowanie_number_reads_slashed_format():
    assert find_postepowanie_number("nr referencyjny sprawy: ZP/PN/48/2026") == "ZP/PN/48/2026"


def test_find_postepowanie_number_reads_mixed_format():
    assert find_postepowanie_number("IR.271-35/2026") == "IR.271-35/2026"


def test_find_postepowanie_number_ignores_legal_quotes():
    assert find_postepowanie_number("art. 527 ust. 2 pkt 1) lit. a) ustawy Pzp") is None


# --- wyszukiwanie po etykiecie ---


def test_find_value_takes_value_on_next_line():
    assert find_value(
        "Rachunek obciążany\nPL05470680287581539721455024", ["Rachunek obciążany"]
    ) == ("PL05470680287581539721455024")


def test_find_value_skips_leading_dots():
    assert find_value("KWOTA PRZELEWU ......... 50,00 PLN", ["KWOTA PRZELEWU"]) == "50,00 PLN"


def test_find_value_is_case_insensitive():
    assert find_value("RACHUNEK NADAWCY\nPL39203888965989833490230983", ["Rachunek nadawcy"]) == (
        "PL39203888965989833490230983"
    )


def test_find_value_returns_none_without_label():
    assert find_value("KRS: 9999405188", ["REGON"]) is None


# --- luki z E19: identyfikatory ze spacjami i myślnikami ---


@pytest.mark.parametrize(
    "raw",
    [
        "999-928-40-65",
        "999 928 40 65",
        "NIP 999-92-84-065",
        "NIP: 999 92 84 065",
        "999\u00a0928\u00a040\u00a065",
        "PL 999-928-40-65",
    ],
)
def test_normalize_nip_accepts_grouped_notation(raw):
    assert normalize_nip(raw) == "9999284065"


@pytest.mark.parametrize(
    "raw",
    [
        "999-928-40-6",  # 9 cyfr
        "999-928-40-650",  # 11 cyfr
        "99-928-40-65",
        "9999-928-40-65",  # grupy w niedozwolonym układzie
        "999--928-40-65",  # podwójny separator
        "999 928  40 65",
        "0999 928 40 65",  # poprzedzone cyfrą: to ciąg dłuższy niż NIP
        "999 928 40 65 7",  # po grupach kolejna cyfra
    ],
)
def test_normalize_nip_rejects_wrong_grouped_notation(raw):
    assert normalize_nip(raw) is None


def test_normalize_nip_takes_earliest_candidate_contiguous_or_grouped():
    assert normalize_nip("NIP 999 928 40 65, KRS 9999405188") == "9999284065"
    assert normalize_nip("KRS 9999405188, NIP 999 928 40 65") == "9999405188"


def test_normalize_nip_does_not_glue_two_adjacent_numbers():
    assert normalize_nip("9999284065 9999405188") == "9999284065"


@pytest.mark.parametrize("raw", ["999 642 785", "999-642-785", "REGON: 999 642 785"])
def test_normalize_regon_accepts_grouped_nine_digits(raw):
    assert normalize_regon(raw) == "999642785"


@pytest.mark.parametrize("raw", ["999 642 785 00123", "999-642-785-00123"])
def test_normalize_regon_accepts_grouped_fourteen_digits(raw):
    assert normalize_regon(raw) == "99964278500123"


@pytest.mark.parametrize("raw", ["99 642 785", "999 642 78", "9996 427 85", "999 642 785 001"])
def test_normalize_regon_rejects_wrong_grouped_notation(raw):
    assert normalize_regon(raw) is None


def test_normalize_regon_prefers_nine_digits_before_fourteen():
    assert normalize_regon("999642785 oraz 99964278500123") == "999642785"
    assert normalize_regon("99964278500123 oraz 999642785") == "999642785"


@pytest.mark.parametrize(
    "raw", ["9999 405 188", "9999-405-188", "KRS 9999 405 188", "999 940 5188"]
)
def test_normalize_krs_accepts_grouped_notation(raw):
    assert normalize_krs(raw) == "9999405188"


@pytest.mark.parametrize("raw", ["9999 405 18", "9999 405 1881", "99 405 188", "9999 405 188 1"])
def test_normalize_krs_rejects_wrong_notation(raw):
    assert normalize_krs(raw) is None


def test_normalize_pesel_does_not_accept_grouped_notation():
    assert normalize_pesel("850 712 042 78") is None


def test_grouped_identifiers_keep_values_without_valid_checksum():
    """Suma kontrolna nie jest filtrem: 999 928 40 65 nie ma poprawnej sumy NIP."""
    assert checksum_valid("nip", "9999284065") is True
    assert normalize_nip("999 000 00 00") == "9990000000"
    assert checksum_valid("nip", "9990000000") is False


def test_rank_by_checksum_puts_valid_first_without_dropping_candidates():
    assert rank_by_checksum("nip", ["9990264287", "9999284065", "123"]) == [
        "9999284065",
        "9990264287",
        "123",
    ]


def test_rank_by_checksum_is_stable_and_keeps_order_within_groups():
    assert rank_by_checksum("nip", ["9990264287", "1", "9999284065", "9"]) == [
        "9999284065",
        "9990264287",
        "1",
        "9",
    ]


def test_rank_by_checksum_handles_other_kinds():
    assert rank_by_checksum("regon", ["999015873", "999184816"]) == ["999184816", "999015873"]
    assert rank_by_checksum(
        "iban", ["68438223049992295262834736", "54716496752472114180714012"]
    ) == [
        "54716496752472114180714012",
        "68438223049992295262834736",
    ]
    assert rank_by_checksum("pesel", ["85071204279", "85071204278"]) == [
        "85071204278",
        "85071204279",
    ]
    assert rank_by_checksum("nip", []) == []


# --- luki z E19: kwoty z separatorem tysięcy ---


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.000,50", 1000.5),
        ("1,000.50", 1000.5),
        ("12.345,60 zł", 12345.6),
        ("12,345.60 PLN", 12345.6),
        ("1.234.567,89", 1234567.89),
        ("1,234,567.89", 1234567.89),
        ("1.000.000", 1000000.0),
        ("1,000,000", 1000000.0),
        ("1.000", 1000.0),
        ("1,000", 1000.0),
        ("999.000", 999000.0),
        ("1 000,50", 1000.5),
        ("10 000,00 zł", 10000.0),
        ("0,500", 0.5),
        ("0.125", 0.125),
        ("1000,5", 1000.5),
        ("1000.50", 1000.5),
        ("200,00", 200.0),
        ("17", 17.0),
        ("3,5", 3.5),
        ("1234,567", 1234.567),
        ("10.5", 10.5),
    ],
)
def test_normalize_amount_handles_thousands_separators(raw, expected):
    assert normalize_amount(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "1.2.3",  # grupy tysięcy nie po 3 cyfry
        "1.000,50,5",  # dwa separatory dziesiętne
        "1,000.50.5",
        "1.00.000",
        "10.000.00",
        "1,0000,000",
        "12.34.567",
    ],
)
def test_normalize_amount_returns_none_for_ambiguous_notation(raw):
    assert normalize_amount(raw) is None


def test_normalize_amount_never_returns_integer_part_of_thousands_notation():
    """Cicha wartość błędna (1.0 zamiast 1000.5) jest groźniejsza niż `None`."""
    assert normalize_amount("1.000,50") != 1.0
    assert normalize_amount("1,000.50") != 1.0


def test_normalize_amount_ignores_sign_and_text_around():
    assert normalize_amount("\u221250,00") == 50.0
    assert normalize_amount("kwota: 34,00 PLN") == 34.0
    assert normalize_amount("10 000,00 zł słownie: dziesięć tysięcy") == 10000.0
    assert normalize_amount("") is None


# --- luki z E19: daty ---


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("01.04.26", "2026-04-01"),
        ("1.4.26", "2026-04-01"),
        ("01-04-26", "2026-04-01"),
        ("01/04/26", "2026-04-01"),
        ("31.12.69", "2069-12-31"),
        ("01.01.70", "1970-01-01"),
        ("01.01.00", "2000-01-01"),
        ("1 IV 2026", "2026-04-01"),
        ("01.IV.2026", "2026-04-01"),
        ("1-IV-2026", "2026-04-01"),
        ("1/XII/2026 r.", "2026-12-01"),
        ("2026/04/01", "2026-04-01"),
        ("2026.04.01", "2026-04-01"),
        ("2026-4-1", "2026-04-01"),
        ("pierwszego kwietnia 2026", "2026-04-01"),
        ("Pierwszego Kwietnia 2026 roku", "2026-04-01"),
    ],
)
def test_normalize_date_accepts_notation_from_e19_gaps(raw, expected):
    assert normalize_date(raw) == expected


@pytest.mark.parametrize(
    ("roman", "month"),
    [
        ("I", 1),
        ("II", 2),
        ("III", 3),
        ("IV", 4),
        ("V", 5),
        ("VI", 6),
        ("VII", 7),
        ("VIII", 8),
        ("IX", 9),
        ("X", 10),
        ("XI", 11),
        ("XII", 12),
    ],
)
def test_normalize_date_reads_every_roman_month(roman, month):
    assert normalize_date(f"15 {roman} 2026") == f"2026-{month:02d}-15"


@pytest.mark.parametrize(
    ("words", "day"),
    [
        ("pierwszego", 1),
        ("drugiego", 2),
        ("trzeciego", 3),
        ("czwartego", 4),
        ("piątego", 5),
        ("szóstego", 6),
        ("siódmego", 7),
        ("ósmego", 8),
        ("dziewiątego", 9),
        ("dziesiątego", 10),
        ("jedenastego", 11),
        ("dwunastego", 12),
        ("trzynastego", 13),
        ("czternastego", 14),
        ("piętnastego", 15),
        ("szesnastego", 16),
        ("siedemnastego", 17),
        ("osiemnastego", 18),
        ("dziewiętnastego", 19),
        ("dwudziestego", 20),
        ("dwudziestego pierwszego", 21),
        ("dwudziestego drugiego", 22),
        ("dwudziestego trzeciego", 23),
        ("dwudziestego czwartego", 24),
        ("dwudziestego piątego", 25),
        ("dwudziestego szóstego", 26),
        ("dwudziestego siódmego", 27),
        ("dwudziestego ósmego", 28),
        ("dwudziestego dziewiątego", 29),
        ("trzydziestego", 30),
        ("trzydziestego pierwszego", 31),
    ],
)
def test_normalize_date_reads_day_given_in_words(words, day):
    assert normalize_date(f"{words} marca 2026") == f"2026-03-{day:02d}"


def test_normalize_date_day_in_words_rejects_nonexistent_day():
    assert normalize_date("trzydziestego pierwszego kwietnia 2026") is None
    assert normalize_date("trzydziestego lutego 2026") is None


def test_normalize_date_rejects_unknown_month_word_and_two_digit_garbage():
    assert normalize_date("pierwszego kwietniaa 2026") is None
    assert normalize_date("1 xx 2026") is None
    assert normalize_date("31.04.26") is None
    assert normalize_date("13.13.26") is None
    assert normalize_date("0 IV 2026") is None


def test_normalize_date_two_digit_year_does_not_cut_a_longer_number():
    assert normalize_date("01.04.20261") is None
    assert normalize_date("101.04.26") is None


def test_normalize_date_four_digit_year_wins_over_two_digit_reading():
    assert normalize_date("01.04.2026") == "2026-04-01"


def test_normalize_date_iso_with_separators_does_not_cut_longer_number():
    assert normalize_date("12026/04/01") is None
    assert normalize_date("2026/04/011") is None


def test_normalize_date_roman_month_requires_capital_letters():
    assert normalize_date("1 iv 2026") is None
    assert normalize_date("5 i 2026") is None


def test_normalize_date_roman_month_inside_word_is_not_a_month():
    assert normalize_date("5 Xerox 2026") is None


def test_normalize_date_prefers_word_date_over_other_notations():
    assert normalize_date("1 kwietnia 2026 (01.05.2026)") == "2026-04-01"


# --- luki z E19: numer TED ze spacjami ---


@pytest.mark.parametrize(
    "raw",
    [
        "2026/S 224 - 999211",
        "2026 /S 224-999211",
        "2026/ S224-999211",
        "2026 / S 224 - 999211",
        "2026/S\r\n224\r\n-\r\n999211",
        "2026/S224-999211",
        "2026/S 224-999211",
    ],
)
def test_normalize_ted_accepts_spaces_around_series_marker_and_hyphen(raw):
    assert normalize_ted(raw) == "999211-2026"


def test_normalize_ted_rejects_wrong_digit_counts():
    assert normalize_ted("2026/S 224 - 99921") is None
    assert normalize_ted("2026/S 224 - 9992111") is None
    assert normalize_ted("202/S 224 - 999211") is None
    assert normalize_ted("20260/S 224 - 999211") is None


# --- test obiegowy z E19 (55 wariantów zapisu tych samych wartości) ---

_ACCOUNT = "68438223049992295262834736"
_ACCOUNT_GROUPED = "68 4382 2304 9992 2952 6283 4736"

_ROUNDTRIP = [
    # NIP
    (normalize_nip, "9999284065", "9999284065"),
    (normalize_nip, "999-928-40-65", "9999284065"),
    (normalize_nip, "999 928 40 65", "9999284065"),
    (normalize_nip, "NIP: 9999284065", "9999284065"),
    (normalize_nip, "PL 9999284065", "9999284065"),
    (normalize_nip, "NIP 999-92-84-065", "9999284065"),
    (normalize_nip, "9999284065.", "9999284065"),
    (normalize_nip, "99992840650", None),
    # REGON
    (normalize_regon, "999642785", "999642785"),
    (normalize_regon, "999 642 785", "999642785"),
    (normalize_regon, "99964278500123", "99964278500123"),
    (normalize_regon, "REGON: 999642785", "999642785"),
    (normalize_regon, "9996427850012", None),
    # KRS
    (normalize_krs, "0009405188", "0009405188"),
    (normalize_krs, "KRS 9999405188", "9999405188"),
    (normalize_krs, "9999 405 188", "9999405188"),
    (normalize_krs, "99994051881", None),
    # rachunek
    (normalize_account, _ACCOUNT, _ACCOUNT),
    (normalize_account, "PL" + _ACCOUNT, _ACCOUNT),
    (normalize_account, "PL " + _ACCOUNT_GROUPED, _ACCOUNT),
    (normalize_account, _ACCOUNT_GROUPED, _ACCOUNT),
    (normalize_account, "PL68-4382-2304-9992-2952-6283-4736", None),
    (normalize_account, _ACCOUNT[:25], None),
    (normalize_account, _ACCOUNT + "1", None),
    # kwota
    (normalize_amount, "10 000,00 zł", 10000.0),
    (normalize_amount, "10000.00", 10000.0),
    (normalize_amount, "10 000,00 PLN", 10000.0),
    (normalize_amount, "200,00", 200.0),
    (normalize_amount, "10 000,00 zł", 10000.0),  # w E19 ten wariant występuje dwa razy
    (normalize_amount, "1.000,50", 1000.5),
    (normalize_amount, "1 000,50", 1000.5),
    (normalize_amount, "17 PLN", 17.0),
    (normalize_amount, "kwota: 34,00 PLN", 34.0),
    (normalize_amount, "\u221250,00", 50.0),
    (normalize_amount, "10 000,00 zł słownie: dziesięć tysięcy", 10000.0),
    (normalize_amount, "1,000.50", 1000.5),
    # data
    (normalize_date, "1 kwietnia 2026", "2026-04-01"),
    (normalize_date, "1 KWIETNIA 2026 r.", "2026-04-01"),
    (normalize_date, "01.04.2026", "2026-04-01"),
    (normalize_date, "01-04-2026", "2026-04-01"),
    (normalize_date, "2026-04-01", "2026-04-01"),
    (normalize_date, "1.4.2026", "2026-04-01"),
    (normalize_date, "31 lutego 2026", None),
    (normalize_date, "01.04.26", "2026-04-01"),
    (normalize_date, "1 IV 2026", "2026-04-01"),
    (normalize_date, "29 lutego 2026", None),
    (normalize_date, "5 października 2026 roku", "2026-10-05"),
    (normalize_date, "1 kwietnia 2026 14:36", "2026-04-01"),
    (normalize_date, "2026/04/01", "2026-04-01"),
    (normalize_date, "pierwszego kwietnia 2026", "2026-04-01"),
    # TED
    (normalize_ted, "2026/S224-999211", "999211-2026"),
    (normalize_ted, "2026/S 224-999211", "999211-2026"),
    (normalize_ted, "999211-2026", "999211-2026"),
    (normalize_ted, "2026/S 224 - 999211", "999211-2026"),
    (normalize_ted, "TED: 999211-2026", "999211-2026"),
]


def test_roundtrip_table_has_all_e19_variants():
    assert len(_ROUNDTRIP) == 55


@pytest.mark.parametrize(
    ("function", "raw", "expected"),
    _ROUNDTRIP,
    ids=[f"{f.__name__}-{raw}" for f, raw, _ in _ROUNDTRIP],
)
def test_roundtrip_variants_of_the_same_value(function, raw, expected):
    assert function(raw) == expected


# --- testy zabijające mutanty (ADR-003) ---

_MIESIACE_TESTOWE = [
    ("styczeń", 1),
    ("stycznia", 1),
    ("luty", 2),
    ("lutego", 2),
    ("marzec", 3),
    ("marca", 3),
    ("kwiecień", 4),
    ("kwietnia", 4),
    ("maj", 5),
    ("maja", 5),
    ("czerwiec", 6),
    ("czerwca", 6),
    ("lipiec", 7),
    ("lipca", 7),
    ("sierpień", 8),
    ("sierpnia", 8),
    ("wrzesień", 9),
    ("września", 9),
    ("październik", 10),
    ("października", 10),
    ("listopad", 11),
    ("listopada", 11),
    ("grudzień", 12),
    ("grudnia", 12),
]


@pytest.mark.parametrize(("name", "month"), _MIESIACE_TESTOWE)
def test_normalize_date_maps_every_month_name(name, month):
    assert normalize_date(f"15 {name} 2026") == f"2026-{month:02d}-15"


def test_normalize_date_rejects_three_digit_fields():
    # 031 → 31 byłoby poprawnym dniem marca, więc cichy odczyt dałby błędną datę
    assert normalize_date("031.03.2026") is None
    assert normalize_date("031.03.26") is None
    assert normalize_date("01.003.2026") is None
    assert normalize_date("01.003.26") is None
    assert normalize_date("2026.003.01") is None
    assert normalize_date("031 III 2026") is None
    assert normalize_date("01 IV 026") is None


def test_normalize_date_accepts_slash_in_both_positions():
    assert normalize_date("01/04/2026") == "2026-04-01"
    assert normalize_date("01.04/2026") == "2026-04-01"
    assert normalize_date("01/04.2026") == "2026-04-01"


def test_normalize_date_dotted_four_digit_year_with_two_digit_pivot():
    assert normalize_date("15.03.2069") == "2069-03-15"
    assert normalize_date("15.03.69") == "2069-03-15"
    assert normalize_date("15.03.70") == "1970-03-15"


def test_normalize_date_day_in_words_does_not_combine_twentieth_with_tenth():
    # „dwudziestego dziesiątego” nie jest dniem 30; czytane jest samo „dziesiątego”
    assert normalize_date("dwudziestego dziesiątego marca 2026") == "2026-03-10"


@pytest.mark.parametrize("prefix", ["0", "5", "9"])
def test_find_postepowanie_number_ignores_candidate_after_digit(prefix):
    assert find_postepowanie_number(f"{prefix}ABC.039.2025") is None


@pytest.mark.parametrize("letter", ["a", "m", "z", "B", "M", "Y"])
def test_find_postepowanie_number_ignores_candidate_inside_longer_word(letter):
    assert find_postepowanie_number(f"{letter * 10}.039.2025") is None


@pytest.mark.parametrize("tail", ["0", "5", "9", "a", "m", "z", "B", "M", "Y"])
def test_find_postepowanie_number_ignores_candidate_followed_by_alphanumeric(tail):
    assert find_postepowanie_number(f"ABC.039.2025{tail * 2}") is None


def test_find_postepowanie_number_prefix_is_at_most_six_letters():
    assert find_postepowanie_number("ABCDEFG.039.2025") is None
    assert find_postepowanie_number("ABCDEF.039.2025") == "ABCDEF.039.2025"
    assert find_postepowanie_number("AB.039.2025") == "AB.039.2025"
    assert find_postepowanie_number("A.039.2025") is None


def test_find_postepowanie_number_group_allows_letters_and_up_to_five_characters():
    assert find_postepowanie_number("ZP.mnopq.2025") == "ZP.mnopq.2025"
    assert find_postepowanie_number("ZP.1.2025") == "ZP.1.2025"
    assert find_postepowanie_number("ZP.039.202601") is None
    assert find_postepowanie_number("ZP.2026") == "ZP.2026"


def test_find_postepowanie_number_allows_at_most_five_groups():
    assert find_postepowanie_number("ZP.1.2.3.4.2026") == "ZP.1.2.3.4.2026"
    assert find_postepowanie_number("ZP.1.2.3.4.5.2026") is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ZP.1950", "ZP.1950"),
        ("ZP.2099", "ZP.2099"),
        ("ZP.1050", None),
        ("ZP.2950", None),
        ("AB.12.34", "AB.12.34"),
        ("AB.12-34", "AB.12-34"),
        ("AB.12/34", "AB.12/34"),
        ("AB-12.34", "AB-12.34"),
        ("AB.12.345", None),
        ("ZP.039.123", None),
        ("AB.12", None),
        ("AB.1.1", None),
    ],
)
def test_find_postepowanie_number_validates_candidate_shape(text, expected):
    assert find_postepowanie_number(text) == expected


def test_find_value_window_is_exactly_120_characters():
    assert find_value("A" + " " * 120 + "X", ["A"]) is None
    assert find_value("A" + " " * 119 + "X", ["A"]) == "X"


def test_find_value_skips_label_embedded_in_a_word():
    assert find_value("xKRS: 123", ["KRS"]) is None
    assert find_value(" xKRS: 123", ["KRS"]) is None
    assert find_value("KRS: 123", ["KRS"]) == "123"


def test_find_value_continues_search_one_character_after_rejected_label():
    # etykieta zaczynająca się od znaku niealfanumerycznego: pierwsze trafienie odrzucone
    # (przed nim litera), drugie zaczyna się o jedną pozycję dalej
    assert find_value("x::: wartość", ["::"]) == "wartość"


def test_fold_turns_dotted_capital_i_into_plain_i():
    assert fold("İSTANBUL") == "istanbul"
    assert fold("Łódź") == "lodz"


def test_checksum_valid_rejects_wrong_lengths():
    assert checksum_valid("nip", "123456789") is False
    assert checksum_valid("nip", "99992840650") is False
    assert checksum_valid("regon", "1234567890") is False
    assert checksum_valid("regon", "1234567851234") is False
    assert checksum_valid("pesel", "8507120427") is False
    assert checksum_valid("pesel", "850712042780") is False
    assert checksum_valid("iban", "PL") is False
    assert checksum_valid("iban", "12345") is False


def test_checksum_valid_regon_remainder_ten_means_check_digit_zero():
    assert checksum_valid("regon", "215736810") is True
    assert checksum_valid("regon", "215736811") is False
    assert checksum_valid("regon", "21573681057440") is True
    assert checksum_valid("regon", "21573681057441") is False


def test_checksum_valid_regon_fourteen_digits_requires_valid_nine_digit_prefix():
    assert checksum_valid("regon", "21573681157446") is False


def test_checksum_valid_pesel_uses_every_weight_and_zero_remainder():
    assert checksum_valid("pesel", "15695855637") is True
    assert checksum_valid("pesel", "15695855636") is False
    assert checksum_valid("pesel", "17488851590") is True
    assert checksum_valid("pesel", "17488851591") is False


def test_find_postepowanie_number_prefix_may_be_lowercase():
    assert find_postepowanie_number("nr nmop.039.2025") == "nmop.039.2025"
