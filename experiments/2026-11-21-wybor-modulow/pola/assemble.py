"""Składanie wyniku w kluczach organizatora z ekstraktora regułowego (wspólne dla E07/E08/E09/E20 i mutacji)."""
from __future__ import annotations

from typing import Any

import rules


def appeal(tx: str) -> dict[str, Any]:
    fx = rules.extract_appeal_fixed(tx)
    act = rules.extract_act(tx)
    pa = rules.extract_parties(tx)
    return {"OdwolanieKIO": {"data": fx["data"], "czynnosc_dzien": act["czynnosc_dzien"], "czynnosc_powod_id": act["czynnosc_powod_id"],
                             "czynnosc_opis": act["czynnosc_opis"], "miejscowosc": fx["miejscowosc"]},
            "Odwolujacy": pa["Odwolujacy"] or [{}], "Zamawiajacy": pa["Zamawiajacy"] or [{}],
            "ZamowieniePubliczne": {"numer_bzp": fx["numer_bzp"], "numer_postepowania": fx["numer_postepowania"], "numer_ted": fx["numer_ted"], "tytul": pa["tytul"]}}


def poa(tx: str) -> dict[str, Any]:
    p = rules.extract_poa(tx)
    mm = [{"data": {"imie_nazwisko": None, "krs": m["krs"], "nazwa": m["nazwa"], "nip": m["nip"], "typ": "osoba_prawna"}, "podpisujacy": []} for m in p["mocodawcy"]]
    mm = mm or [{"data": {"imie_nazwisko": p["imie_nazwisko"], "krs": p["krs"], "nazwa": p["nazwa"], "nip": p["nip"], "typ": p["typ"]}, "podpisujacy": []}]
    mm[0]["podpisujacy"] = [{"imie_nazwisko": n} for n in p["podpisujacy"]]
    pes = p["pesele"]
    return {"mocodawca": mm, "pelnomocnicy": [{"imie_nazwisko": n, "pesel": (pes[i] if i < len(pes) else None)} for i, n in enumerate(p["pelnomocnicy"])]}


def transfer(tx: str) -> dict[str, Any]:
    return {"przelew_bankowy": {**rules.extract_transfer(tx), "tytul": None}}


BY_CLASS = {"odwolanie": appeal, "pelnomocnictwo": poa, "przelew": transfer}
