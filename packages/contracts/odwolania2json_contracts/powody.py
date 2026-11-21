"""Słownik przyczyn odwołania organizatora UZP.

Źródło: ``docs/02-materialy/organizator-uzp-aktualizacje/main-7590db8/oczekiwane-json/czynnosc_powod_id_dict.md``
(rewizja ``main-7590db8``). Zmiana pliku organizatora musi odzwierciedlać się
w teście ``tests/contract/test_powody.py``.
"""

APPEAL_REASONS: dict[int, str] = {
    1: "Decyzja o odrzuceniu oferty",
    2: "Ogłoszenie wyboru oferty",
    3: "Decyzja o wykluczeniu wykonawcy",
    4: "Publikacja specyfikacji warunków zamówienia (SWZ)",
    5: "Modyfikacja treści SWZ",
    6: "Odpowiedzi/wyjaśnienia do SWZ",
    7: "Zaniechanie odrzucenia oferty",
    8: "Zaniechanie wykluczenia wykonawcy",
    9: "Decyzja o unieważnieniu postępowania",
    10: "Zaniechanie unieważnienia postępowania",
    11: "Opis przedmiotu zamówienia (OPZ)",
    12: "Projektowane postanowienia umowy",
}
