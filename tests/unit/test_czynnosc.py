"""Reguły zaskarżonej czynności, numeru BZP i imienia pełnomocnika (Z05).

Testy korpusowe używają wyłącznie 147 dokumentów rozwojowych (`data/podzial.json`); oczekiwane
wartości pochodzą z referencji organizatora. Luki g1 i g2 to dane SYNTETYCZNE (edycje tekstu).
"""

from __future__ import annotations

import pytest
from odwolania2json.domain.czynnosc import (
    Act,
    classify_powod,
    extract_act,
    find_bzp,
    first_act_text,
    normalize_bzp,
    reason_description,
    refine_appeal,
    validate_bzp,
    validate_representative_name,
)
from odwolania2json_contracts.powody import APPEAL_REASONS
from support.devcorpus import dev_documents, synthetic_gap_documents

# --- first_act_text ---


def test_first_act_text_takes_first_item_after_charges_marker():
    text = "Zarzuty polegające na: 1) odrzuceniu oferty odwołującego bez podstawy 2) inne"
    assert first_act_text(text) == "odrzuceniu oferty odwołującego bez podstawy"


def test_first_act_text_item_ends_before_second_item():
    text = "polegających na: 1) odrzuceniu oferty odwołującego 2) wyborze oferty"
    assert first_act_text(text) == "odrzuceniu oferty odwołującego"


@pytest.mark.parametrize("terminator", ["Zarzut nr 1", "Uzasadnienie", "Zamawiający w dniu 1"])
def test_first_act_text_item_ends_before_section_marker(terminator):
    text = f"polegających na: 1) odrzuceniu oferty odwołującego {terminator} dalszy tekst"
    assert first_act_text(text) == "odrzuceniu oferty odwołującego"


def test_first_act_text_item_ends_at_end_of_text():
    assert first_act_text("polegających na: 1) odrzuceniu oferty odwołującego") == (
        "odrzuceniu oferty odwołującego"
    )


def test_first_act_text_collapses_whitespace_and_drops_page_footers():
    text = "polegających\nna:\n1)   odrzuceniu\noferty Strona 2 z 9 odwołującego"
    assert first_act_text(text) == "odrzuceniu oferty odwołującego"


def test_first_act_text_accepts_other_inflections_of_the_marker():
    assert first_act_text("polegającego na: 1) odrzuceniu oferty odwołującego 2)") == (
        "odrzuceniu oferty odwołującego"
    )


def test_first_act_text_item_must_have_at_least_ten_characters():
    assert first_act_text("polegających na: 1) krótki") == ""
    assert first_act_text("polegających na: 1) 123456789") == ""
    assert first_act_text("polegających na: 1) 1234567890") == "1234567890"


def test_first_act_text_item_is_cut_at_five_hundred_characters():
    item = "a" * 600
    assert first_act_text(f"polegających na: 1) {item}") == ""
    assert first_act_text(f"polegających na: 1) {'a' * 500} 2) x") == "a" * 500


def test_first_act_text_falls_back_to_narrative_sentence():
    text = "Zamawiający w dniu 1 kwietnia 2026 roku odrzucił ofertę odwołującego. Dalej."
    assert (
        first_act_text(text)
        == "Zamawiający w dniu 1 kwietnia 2026 roku odrzucił ofertę odwołującego."
    )


def test_first_act_text_narrative_accepts_abbreviated_year_word():
    text = "Zamawiający w dniu 1 kwietnia 2026 r. odrzucił ofertę odwołującego. Dalej."
    assert (
        first_act_text(text)
        == "Zamawiający w dniu 1 kwietnia 2026 r. odrzucił ofertę odwołującego."
    )


def test_first_act_text_narrative_gap_before_year_word_is_one_to_forty_characters():
    assert first_act_text("Zamawiający w dniu 5 roku odrzucił ofertę odwołującego. x") != ""
    assert first_act_text("Zamawiający w dniu roku odrzucił ofertę odwołującego. x") == ""
    gap40 = "Zamawiający w dniu " + "a" * 40 + " roku odrzucił ofertę odwołującego. x"
    gap41 = "Zamawiający w dniu " + "a" * 41 + " roku odrzucił ofertę odwołującego. x"
    assert first_act_text(gap40) != ""
    assert first_act_text(gap41) == ""


def test_first_act_text_narrative_gap_cannot_contain_a_dot():
    assert first_act_text("Zamawiający w dniu 1.04.2026 roku odrzucił ofertę odwołującego. x") == ""


def test_first_act_text_narrative_sentence_is_five_to_three_hundred_characters():
    head = "Zamawiający w dniu 1 kwietnia 2026 roku "
    assert first_act_text(head + "abcd. x") == ""
    assert first_act_text(head + "abcde. x") == head + "abcde."
    assert first_act_text(head + "a" * 300 + ". x") == head + "a" * 300 + "."
    assert first_act_text(head + "a" * 301 + ". x") == ""


def test_first_act_text_prefers_charge_list_over_narrative_sentence():
    text = (
        "Zamawiający w dniu 1 kwietnia 2026 roku dokonał wyboru oferty. "
        "Zarzuty polegające na: 1) zaniechaniu unieważnienia postępowania 2) inne"
    )
    assert first_act_text(text) == "zaniechaniu unieważnienia postępowania"


def test_first_act_text_empty_without_any_marker():
    assert first_act_text("Zwykły tekst bez zarzutów.") == ""
    assert first_act_text("") == ""


# --- classify_powod ---

_POWODY = [
    ("odrzuceniu oferty odwołującego", 1),
    ("odrzucił ofertę odwołującego", 1),
    ("wyborze oferty najkorzystniejszej", 2),
    ("wybór oferty konkurenta", 2),
    ("wybrał ofertę konkurenta", 2),
    ("wykluczeniu odwołującego z postępowania", 3),
    ("wykluczył wykonawcę", 3),
    ("publikacji treści zamówienia", None),
    ("ustaleniu treści Specyfikacji Warunków Zamówienia", 4),
    ("treści SWZ w zakresie kryteriów", 4),
    ("zmodyfikował treść dokumentów zamówienia", 5),
    ("modyfikacji dokumentów zamówienia", 5),
    ("udzieleniu odpowiedzi na pytania wykonawców", 6),
    ("udzieleniu wyjaśnień do dokumentów", 6),
    ("zaniechaniu odrzucenia oferty konkurenta", 7),
    ("zaniechał odrzucenia oferty", 7),
    ("nie odrzucił oferty konkurenta", 7),
    ("brak odrzucenia oferty", 7),
    ("zaniechaniu wykluczenia konkurenta", 8),
    ("nie wykluczył wykonawcy", 8),
    ("brak wykluczenia wykonawcy", 8),
    ("unieważnieniu postępowania", 9),
    ("unieważnił postępowanie", 9),
    ("zaniechaniu unieważnienia postępowania", 10),
    ("nie unieważnił postępowania", 10),
    ("brak unieważnienia postępowania", 10),
    ("opisie przedmiotu zamówienia", 11),
    ("opisu przedmiotu zamówienia", 11),
    ("treści OPZ", 11),
    ("projektowanych postanowień umowy", 12),
    ("udostępnił projektowane postanowienia umowy", 12),
    ("wzoru umowy w zakresie kar", 12),
    ("postanowień umowy w sprawie", 12),
    ("postanowienia umowy dotyczące kar", 12),
]


@pytest.mark.parametrize(("act", "expected"), _POWODY)
def test_classify_powod_maps_phrase_to_reason(act, expected):
    assert classify_powod(act) == expected


def test_classify_powod_covers_every_reason_of_the_dictionary():
    assert {pid for _, pid in _POWODY if pid} == set(APPEAL_REASONS)


def test_classify_powod_ignores_letter_case():
    assert classify_powod("ODRZUCENIU OFERTY") == 1
    assert classify_powod("Zaniechaniu Unieważnienia") == 10


def test_classify_powod_is_none_for_empty_text():
    assert classify_powod("") is None


@pytest.mark.parametrize(
    ("act", "expected"),
    [
        ("unieważnieniu i wykluczeniu", 9),  # unieważnienie przed wykluczeniem
        ("wykluczeniu i odrzuceniu oferty", 3),  # wykluczenie przed odrzuceniem
        ("odrzuceniu oferty i wyborze innej", 1),  # odrzucenie przed wyborem
        ("wyborze oferty i modyfikacji treści", 2),
        ("modyfikacji treści i odpowiedziach", 5),
        ("odpowiedziach na pytania i projektowanych postanowieniach umowy", 6),
        ("projektowanych postanowieniach umowy i opisie przedmiotu zamówienia", 12),
        ("opisie przedmiotu zamówienia i specyfikacji", 11),
        ("specyfikacji warunków zamówienia i wzorze umowy", 4),
    ],
)
def test_classify_powod_precedence(act, expected):
    assert classify_powod(act) == expected


def test_classify_powod_negation_applies_to_the_matched_family():
    assert classify_powod("zaniechaniu unieważnienia, odrzucenia i wykluczenia") == 10
    assert classify_powod("zaniechaniu wykluczenia oraz odrzucenia") == 8
    assert classify_powod("odrzuceniu oferty") == 1
    assert classify_powod("wykluczeniu wykonawcy") == 3
    assert classify_powod("unieważnieniu postępowania") == 9


def test_classify_powod_wzor_umowy_word_boundary_for_opz():
    assert classify_powod("kopz bez granicy") is None
    assert classify_powod("treść OPZ.") == 11


# --- extract_act ---


def test_extract_act_returns_reason_description_and_day_from_the_first_charge():
    text = (
        "Zarzuty polegające na: 1) odrzuceniu oferty odwołującego w dniu 3 maja 2026 roku 2) inne "
        "Zamawiający w dniu 9 czerwca 2026 roku dokonał wyboru oferty."
    )
    assert extract_act(text) == Act(1, "Decyzja o odrzuceniu oferty", "2026-05-03")


def test_extract_act_reads_numeric_day():
    text = "polegających na: 1) zaniechaniu odrzucenia oferty z dnia 05.06.2026 r. 2) inne"
    assert extract_act(text) == Act(7, "Zaniechanie odrzucenia oferty", "2026-06-05")


@pytest.mark.parametrize("month", range(1, 13))
def test_extract_act_reads_every_month_word(month):
    names = [
        "stycznia",
        "lutego",
        "marca",
        "kwietnia",
        "maja",
        "czerwca",
        "lipca",
        "sierpnia",
        "września",
        "października",
        "listopada",
        "grudnia",
    ]
    text = f"polegających na: 1) odrzuceniu oferty z dnia 4 {names[month - 1]} 2026 r. 2) inne"
    assert extract_act(text).dzien == f"2026-{month:02d}-04"


def test_extract_act_without_day_has_none_day():
    act = extract_act("polegających na: 1) odrzuceniu oferty odwołującego 2) inne")
    assert act == Act(1, "Decyzja o odrzuceniu oferty", None)


def test_extract_act_without_fragment_is_all_none():
    assert extract_act("brak zarzutów") == Act(None, None, None)


def test_extract_act_with_unknown_reason_keeps_day_but_no_description():
    act = extract_act("polegających na: 1) czynności z dnia 3 maja 2026 roku 2) inne")
    assert act == Act(None, None, "2026-05-03")


def test_extract_act_day_is_taken_only_from_the_charge_fragment():
    text = (
        "Pismo z dnia 1 stycznia 2026 roku. polegających na: 1) odrzuceniu oferty odwołującego 2) x"
    )
    assert extract_act(text).dzien is None


def test_extract_act_accepts_years_from_the_nineteen_hundreds_and_twenty_first_century():
    assert extract_act("polegających na: 1) odrzuceniu oferty z dnia 3.05.1999 r. 2)").dzien == (
        "1999-05-03"
    )
    assert extract_act("polegających na: 1) odrzuceniu oferty z dnia 3.05.2099 r. 2)").dzien == (
        "2099-05-03"
    )
    assert extract_act("polegających na: 1) odrzuceniu oferty z dnia 3.05.1899 r. 2)").dzien is None
    assert extract_act("polegających na: 1) odrzuceniu oferty z dnia 3.05.2199 r. 2)").dzien is None


def test_reason_description_is_literal_dictionary_value():
    for pid, opis in APPEAL_REASONS.items():
        assert reason_description(pid) == opis
    assert reason_description(0) is None
    assert reason_description(13) is None


# --- numer BZP ---


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026/BZP00999063", "2026/BZP00999063"),
        ("2026/BZP 00999063", "2026/BZP00999063"),
        (" 2026 / BZP 00999063 ", "2026/BZP00999063"),
        ("2026/BZP00999063/01", "2026/BZP00999063/01"),
        ("1999/BZP00000001", "1999/BZP00000001"),
        ("2099/BZP12345678", "2099/BZP12345678"),
    ],
)
def test_normalize_bzp_canonical_form(raw, expected):
    assert normalize_bzp(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "2026/BZP0099906",
        "2026/BZP009990631",
        "2026/BZP00999063/1",
        "2026/BZP00999063/123",
        "1899/BZP00999063",
        "2199/BZP00999063",
        "2026/bzp00999063",
        "2026/BZP0099906X",
        "BZP00999063",
        "26/BZP00999063",
        "2026/BZP 00999063 oraz",
    ],
)
def test_normalize_bzp_rejects_malformed_values(raw):
    assert normalize_bzp(raw) is None


def test_find_bzp_reads_the_number_from_the_subject_block():
    text = (
        "Pismo.\ndotyczy: postępowania o udzielenie zamówienia, numer 2026/BZP 00999112 "
        "(poprzednie 2025/BZP 00998985)\nODWOŁANIE\nTreść."
    )
    assert find_bzp(text) == "2026/BZP00999112"


@pytest.mark.parametrize("end", ["Działając", "Prezes Krajowej", "O D W O Ł A N I E"])
def test_find_bzp_block_ends_at_each_title_marker(end):
    assert find_bzp(f"dotyczy: 2026/BZP00999063 {end} tekst") == "2026/BZP00999063"
    assert find_bzp(f"dotyczy: {end} 2026/BZP00999063") is None


def test_find_bzp_ignores_numbers_outside_the_subject_block():
    assert find_bzp("w sprawie 2026/BZP00999063\ndotyczy: sprawy ODWOŁANIE") is None
    assert find_bzp("2026/BZP00999063 bez bloku dotyczy") is None


def test_find_bzp_block_is_limited_to_nine_hundred_characters():
    number = "2026/BZP00999063"
    exact = " " + number + "x" * (900 - len(number) - 1)
    assert len(exact) == 900
    assert find_bzp("dotyczy" + exact + "ODWOŁANIE") == number
    assert find_bzp("dotyczy" + exact + "x" + "ODWOŁANIE") is None


def test_find_bzp_skips_a_distant_subject_mention_and_reads_the_next_one():
    far = "dotyczy" + "x" * 950 + "ODWOŁANIE "
    assert find_bzp(far + "dotyczy: 2026/BZP00999063 ODWOŁANIE") == "2026/BZP00999063"
    assert find_bzp("dotyczy: bez numeru ODWOŁANIE dotyczy: 2026/BZP00999063 ODWOŁANIE") is None


def test_find_bzp_accepts_label_without_colon_and_optional_suffix():
    assert find_bzp("dotyczy 2026/BZP00999063/02 ODWOŁANIE") == "2026/BZP00999063/02"


def test_find_bzp_requires_no_adjacent_digits():
    assert find_bzp("dotyczy: 12026/BZP00999063 ODWOŁANIE") is None
    assert find_bzp("dotyczy: 2026/BZP009990631 ODWOŁANIE") is None


def test_find_bzp_without_number_in_block_is_none():
    assert find_bzp("dotyczy: sprawy bez numeru ODWOŁANIE") is None


def test_validate_bzp_accepts_value_with_evidence_ignoring_spaces():
    assert validate_bzp("2026/BZP 00999063", "numer 2026/BZP00999063 w tekście") == (
        "2026/BZP00999063"
    )
    assert validate_bzp("2026/BZP00999063", "numer 2026/BZP\n00999063 w tekście") == (
        "2026/BZP00999063"
    )


def test_validate_bzp_rejects_value_without_evidence_in_text():
    assert validate_bzp("2026/BZP00999063", "numer 2026/BZP00999064") is None


def test_validate_bzp_rejects_malformed_and_empty_values():
    assert validate_bzp(None, "2026/BZP00999063") is None
    assert validate_bzp("", "2026/BZP00999063") is None
    assert validate_bzp("2026/BZP999", "2026/BZP999") is None


# --- imię i nazwisko pełnomocnika ---


def test_representative_name_present_in_text_is_kept():
    text = "reprezentowana przez: r. pr. Dorota Siedlecki"
    assert validate_representative_name("Dorota Siedlecki", text) == "Dorota Siedlecki"


def test_representative_name_absent_from_text_is_dropped():
    assert validate_representative_name("Jan Kowalski", "reprezentowana przez: Anna Nowak") is None


@pytest.mark.parametrize("raw", [None, "", "   ", "\n"])
def test_representative_name_empty_values_are_none(raw):
    assert validate_representative_name(raw, "Jan Kowalski") is None


@pytest.mark.parametrize(
    "raw",
    [
        "Dorota Siedlecki; Ryszard Jabłończyk",
        "Dorota Siedlecki, Ryszard Jabłończyk",
        "Dorota Siedlecki i Ryszard Jabłończyk",
        "Dorota Siedlecki oraz Ryszard Jabłończyk",
    ],
)
def test_representative_name_list_gives_first_name_with_evidence(raw):
    text = "r. pr. Dorota Siedlecki oraz adw. Ryszard Jabłończyk"
    assert validate_representative_name(raw, text) == "Dorota Siedlecki"


def test_representative_name_list_skips_names_without_evidence():
    assert validate_representative_name("Ala Kot; Dorota Siedlecki", "adw. Dorota Siedlecki") == (
        "Dorota Siedlecki"
    )


def test_representative_name_ignores_case_and_spacing():
    text = "reprezentowana przez: DOROTA   SIEDLECKI\nadres"
    assert validate_representative_name("Dorota Siedlecki", text) == "Dorota Siedlecki"
    assert validate_representative_name("dorota\nsiedlecki", text) == "dorota siedlecki"


def test_representative_name_with_inner_conjunction_letter_is_not_split_in_words():
    assert validate_representative_name("Iwona Kowalska", "adw. Iwona Kowalska") == "Iwona Kowalska"
    assert validate_representative_name("Kimi Nowak", "adw. Kimi Nowak") == "Kimi Nowak"


def test_representative_name_with_only_separators_is_none():
    assert validate_representative_name(", ;", "tekst, ; z separatorami") is None


# --- refine_appeal ---

_TEKST = (
    "dotyczy: postępowania 2026/BZP00999063 ODWOŁANIE\n"
    "reprezentowana przez: r. pr. Dorota Siedlecki\n"
    "polegających na: 1) odrzuceniu oferty odwołującego w dniu 3 maja 2026 roku 2) inne"
)


def _payload():
    return {
        "OdwolanieKIO": {
            "czynnosc_powod_id": 11,
            "czynnosc_opis": "Opis przedmiotu zamówienia (OPZ)",
            "czynnosc_dzien": "2026-01-01",
            "tytul": "bez zmian",
        },
        "ZamowieniePubliczne": {"numer_bzp": "2026/BZP 00999063", "numer_ted": "1-2026"},
        "Odwolujacy": [
            {
                "nazwa": "Firma",
                "pelnomocnik": {"imie_nazwisko": "Dorota Siedlecki; Ktoś Obcy", "mail": "x@y.pl"},
            }
        ],
    }


def test_refine_appeal_replaces_weak_fields_with_rule_and_evidence_values():
    refined = refine_appeal(_payload(), _TEKST)
    assert refined["OdwolanieKIO"] == {
        "czynnosc_powod_id": 1,
        "czynnosc_opis": "Decyzja o odrzuceniu oferty",
        "czynnosc_dzien": "2026-05-03",
        "tytul": "bez zmian",
    }
    assert refined["ZamowieniePubliczne"] == {
        "numer_bzp": "2026/BZP00999063",
        "numer_ted": "1-2026",
    }
    assert refined["Odwolujacy"] == [
        {"nazwa": "Firma", "pelnomocnik": {"imie_nazwisko": "Dorota Siedlecki", "mail": "x@y.pl"}}
    ]


def test_refine_appeal_does_not_modify_the_input_payload():
    payload = _payload()
    refine_appeal(payload, _TEKST)
    assert payload == _payload()


def test_refine_appeal_keeps_model_values_when_rules_find_nothing():
    payload = _payload()
    refined = refine_appeal(payload, "reprezentowana przez: Dorota Siedlecki; 2026/BZP00999063")
    assert refined["OdwolanieKIO"] == payload["OdwolanieKIO"]
    assert refined["ZamowieniePubliczne"] == {
        "numer_bzp": "2026/BZP00999063",
        "numer_ted": "1-2026",
    }


def test_refine_appeal_keeps_model_day_when_rules_find_reason_without_day():
    payload = _payload()
    text = "polegających na: 1) odrzuceniu oferty odwołującego 2) inne"
    refined = refine_appeal(payload, text)
    assert refined["OdwolanieKIO"]["czynnosc_powod_id"] == 1
    assert refined["OdwolanieKIO"]["czynnosc_dzien"] == "2026-01-01"


def test_refine_appeal_drops_bzp_and_name_without_evidence():
    refined = refine_appeal(_payload(), "polegających na: 1) odrzuceniu oferty odwołującego 2)")
    assert refined["ZamowieniePubliczne"]["numer_bzp"] is None
    assert refined["Odwolujacy"][0]["pelnomocnik"]["imie_nazwisko"] is None


def test_refine_appeal_prefers_subject_block_number_over_model_value():
    payload = _payload()
    payload["ZamowieniePubliczne"]["numer_bzp"] = "2025/BZP00998985"
    text = _TEKST + " poprzednio 2025/BZP00998985"
    assert refine_appeal(payload, text)["ZamowieniePubliczne"]["numer_bzp"] == "2026/BZP00999063"


def test_refine_appeal_handles_missing_sections_and_non_string_values():
    assert refine_appeal({}, _TEKST) == {}
    refined = refine_appeal(
        {
            "ZamowieniePubliczne": {"numer_bzp": 5},
            "Odwolujacy": [{"pelnomocnik": {"imie_nazwisko": 7}}],
        },
        "bez wartości",
    )
    assert refined["ZamowieniePubliczne"]["numer_bzp"] is None
    assert refined["Odwolujacy"][0]["pelnomocnik"]["imie_nazwisko"] is None


@pytest.mark.parametrize(
    "odwolujacy", [[], "tekst", [None], [{"pelnomocnik": None}], [{"pelnomocnik": "x"}], [{}]]
)
def test_refine_appeal_ignores_malformed_applicant_sections(odwolujacy):
    refined = refine_appeal({"Odwolujacy": odwolujacy}, _TEKST)
    assert refined["Odwolujacy"] == odwolujacy


def test_refine_appeal_sections_that_are_not_objects_are_left_alone():
    payload = {"OdwolanieKIO": "x", "ZamowieniePubliczne": None}
    assert refine_appeal(payload, _TEKST) == payload


def test_refine_appeal_does_not_touch_other_applicants():
    payload = {
        "Odwolujacy": [
            {"pelnomocnik": {"imie_nazwisko": "Dorota Siedlecki"}},
            {"pelnomocnik": {"imie_nazwisko": "Ktoś Obcy"}},
        ]
    }
    refined = refine_appeal(payload, _TEKST)
    assert refined["Odwolujacy"][1]["pelnomocnik"]["imie_nazwisko"] == "Ktoś Obcy"


# --- korpus rozwojowy (147 dokumentów) ---

_DOCS = dev_documents()


def _appeal_reference(doc, section):
    value = doc.reference[section]
    assert isinstance(value, dict)
    return value


def test_dev_corpus_has_147_documents_from_49_cases():
    assert len(_DOCS) == 147
    assert len({d.case_id for d in _DOCS}) == 49


def test_extract_act_matches_reference_on_all_49_dev_appeals():
    appeals = [d for d in _DOCS if d.document_class == "odwolanie"]
    assert len(appeals) == 49
    wrong = []
    for doc in appeals:
        ref = _appeal_reference(doc, "OdwolanieKIO")
        act = extract_act(doc.text)
        expected = Act(ref["czynnosc_powod_id"], ref["czynnosc_opis"], ref["czynnosc_dzien"])
        if act != expected:
            wrong.append(doc.case_id)
    assert wrong == []


def test_extract_act_finds_nothing_in_non_appeal_dev_documents():
    others = [d for d in _DOCS if d.document_class != "odwolanie"]
    assert len(others) == 98
    assert [d.case_id for d in others if extract_act(d.text).powod_id is not None] == []


def test_find_bzp_matches_reference_on_all_49_dev_appeals():
    appeals = [d for d in _DOCS if d.document_class == "odwolanie"]
    wrong = [
        d.case_id
        for d in appeals
        if find_bzp(d.text) != _appeal_reference(d, "ZamowieniePubliczne")["numer_bzp"]
    ]
    assert wrong == []


def test_validate_bzp_keeps_reference_value_in_every_dev_appeal_that_has_one():
    checked = 0
    for doc in (d for d in _DOCS if d.document_class == "odwolanie"):
        expected = _appeal_reference(doc, "ZamowieniePubliczne")["numer_bzp"]
        if expected is None:
            continue
        spaced = expected.replace("/BZP", "/BZP ")
        assert validate_bzp(spaced, doc.text) == expected
        assert validate_bzp(expected.replace("0", "1", 1), doc.text) is None
        checked += 1
    assert checked > 0


def test_representative_name_from_reference_has_evidence_in_every_dev_appeal():
    checked = 0
    for doc in (d for d in _DOCS if d.document_class == "odwolanie"):
        odwolujacy = doc.reference["Odwolujacy"]
        assert isinstance(odwolujacy, list)
        name = odwolujacy[0]["pelnomocnik"]["imie_nazwisko"]
        if name is None:
            continue
        assert validate_representative_name(f"{name}; Obca Osoba", doc.text) == name
        assert validate_representative_name("Obca Osoba", doc.text) is None
        checked += 1
    assert checked > 0


# --- luki SYNTETYCZNE (E20 g1, g2; 8 edycji tekstu na lukę) ---

_GAPS = synthetic_gap_documents()


def test_synthetic_gaps_have_eight_documents_each():
    assert {k: len(v) for k, v in _GAPS.items()} == {
        "missing_representative": 8,
        "reason_twelve": 8,
    }


def test_synthetic_reason_twelve_is_found_by_rules_in_all_eight_documents():
    for doc in _GAPS["reason_twelve"]:
        act = extract_act(doc.text)
        assert act.powod_id == 12
        assert act.opis == "Projektowane postanowienia umowy"


def test_synthetic_missing_representative_name_is_rejected_when_absent_from_text():
    for doc in _GAPS["missing_representative"]:
        assert doc.removed_name is not None
        assert validate_representative_name(doc.removed_name, doc.text) is None
