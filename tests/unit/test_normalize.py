"""Testy normalizatorów pól.

Wartości pochodzą z materiałów organizatora (`docs/02-materialy/organizator-uzp/dane`).
Etykieta w dokumencie rozstrzyga: normalizatory zwracają wartość o poprawnej
długości, a `checksum_valid` służy wyłącznie do porządkowania kandydatów.
"""

from __future__ import annotations

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
