"""Uruchomienie eksperymentu YAML v0 na 60 sprawach organizatora.

python eksperyment.py  (Python 3.13, pydantic 2, PyYAML)
Wynik: wyniki.json obok skryptu + podsumowanie na stdout.
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from silnik import BladKonfiguracji, Klasa

TU = Path(__file__).resolve().parent
MAT = TU.parents[1] / "docs" / "02-materialy"
BAZA = MAT / "organizator-uzp" / "dane"
AKT = MAT / "organizator-uzp-aktualizacje" / "main-7590db8" / "dane"


def referencja(sprawa: str, plik: str) -> tuple[dict, str]:
    poprawka = AKT / sprawa / plik
    zrodlo = poprawka if poprawka.exists() else BAZA / sprawa / plik
    return json.loads(zrodlo.read_text(encoding="utf-8")), str(zrodlo.relative_to(MAT))


def mutacje(dane: dict):
    """Mutanty referencji, które walidator MUSI odrzucić (nazwa, dane)."""
    def liscie(o, sciezka=()):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from liscie(v, sciezka + (k,))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from liscie(v, sciezka + (i,))
        else:
            yield sciezka, o

    def ustaw(o, sciezka, wartosc):
        for s in sciezka[:-1]:
            o = o[s]
        o[sciezka[-1]] = wartosc

    def usun(o, sciezka):
        for s in sciezka[:-1]:
            o = o[s]
        del o[sciezka[-1]]

    for sciezka, v in liscie(dane):
        if isinstance(sciezka[-1], int):
            continue
        m = copy.deepcopy(dane); usun(m, sciezka); yield f"brak_klucza:{sciezka}", m
        if isinstance(v, str):
            m = copy.deepcopy(dane); ustaw(m, sciezka, 12345); yield f"str->int:{sciezka}", m
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            m = copy.deepcopy(dane); ustaw(m, sciezka, str(v)); yield f"liczba->str:{sciezka}", m
    m = copy.deepcopy(dane); m["dodatkowy_klucz"] = 1; yield "dodatkowy_klucz", m


def main() -> int:
    wyniki: dict = {"klasy": {}}
    klasy = {k: Klasa(TU / "klasy" / f"{k}.yaml") for k in ("odwolanie", "pelnomocnictwo", "przelew")}
    pliki = {"odwolanie": "odwolanie.json", "pelnomocnictwo": "pelnomocnictwo.json", "przelew": "przelew.json"}
    sprawy = sorted(p.name for p in BAZA.glob("przyklad_*"))

    for nazwa, klasa in klasy.items():
        r = {"spraw": 0, "walidacja_ok": 0, "bledy_walidacji": [], "roundtrip_identyczny": 0,
             "roznice_roundtrip": [], "naruszenia_formatu": [], "pochodne_zgodne": 0,
             "pochodne_niezgodne": [], "mutanty": 0, "mutanty_przezyly": []}
        for sprawa in sprawy:
            dane, zrodlo = referencja(sprawa, pliki[nazwa])
            r["spraw"] += 1
            try:
                obj = klasa.waliduj(dane)
                r["walidacja_ok"] += 1
                wynik = klasa.serializuj(obj)
                if json.dumps(wynik, ensure_ascii=False) == json.dumps(dane, ensure_ascii=False):
                    r["roundtrip_identyczny"] += 1
                else:
                    r["roznice_roundtrip"].append(zrodlo)
            except ValidationError as e:
                r["bledy_walidacji"].append({"plik": zrodlo, "bledy": [
                    {"loc": list(map(str, x["loc"])), "typ": x["type"], "wartosc": repr(x.get("input"))[:60]}
                    for x in e.errors()]})
            for sc, v, wz in klasa.formaty(dane):
                r["naruszenia_formatu"].append({"plik": zrodlo, "pole": sc, "wartosc": v, "wzorzec": wz})
            for sc, v, wyl in klasa.pochodne(dane):
                if v == wyl:
                    r["pochodne_zgodne"] += 1
                else:
                    r["pochodne_niezgodne"].append({"plik": zrodlo, "pole": sc, "w_danych": v, "wyliczone": wyl})
            for opis, m in mutacje(dane):
                r["mutanty"] += 1
                try:
                    klasa.waliduj(m)
                    r["mutanty_przezyly"].append({"plik": zrodlo, "mutant": opis})
                except ValidationError:
                    pass
        r["schemat_llm"] = klasa.schemat_llm()
        r["json_schema_pelny"] = klasa.model.model_json_schema(by_alias=True)
        wyniki["klasy"][nazwa] = r

    # rozszerzalność: nowa klasa samym YAML, bez zmian w silniku
    nowa = Klasa(TU / "klasy_nowe" / "zawiadomienie_o_wniesieniu.yaml")
    probka = {"Zawiadomienie": {"data": "2025-10-20", "sygnatura_kio": "KIO 1234/25", "tryb_doreczenia": None,
                                "liczba_wykonawcow": 3, "wezwani_wykonawcy": ["A sp. z o.o.", "B S.A."]},
              "Zamawiajacy": {"nazwa": "Gmina X", "nip": "1234567890"}}
    zla = copy.deepcopy(probka); zla["Zawiadomienie"]["tryb_doreczenia"] = "fax"
    zla2 = copy.deepcopy(probka); zla2["Zawiadomienie"]["liczba_wykonawcow"] = -1
    nowa_wynik = {"probka_ok": False, "enum_spoza_listy_odrzucony": False, "zakres_odrzucony": False}
    try:
        nowa.waliduj(probka); nowa_wynik["probka_ok"] = True
    except ValidationError as e:
        nowa_wynik["blad"] = str(e)
    for klucz, dane in (("enum_spoza_listy_odrzucony", zla), ("zakres_odrzucony", zla2)):
        try:
            nowa.waliduj(dane)
        except ValidationError:
            nowa_wynik[klucz] = True
    nowa_wynik["schemat_llm"] = nowa.schemat_llm()
    # błędna konfiguracja ma wyjść przy wczytaniu
    zly_yaml = TU / "klasy_nowe" / "_zly.yaml.tmp"
    zly_yaml.write_text("klasa: zla\npola:\n  x: {typ: tekst, normalizator: nieistniejacy}\n", encoding="utf-8")
    try:
        Klasa(zly_yaml); nowa_wynik["zly_normalizator_wykryty"] = False
    except BladKonfiguracji as e:
        nowa_wynik["zly_normalizator_wykryty"] = str(e)
    finally:
        zly_yaml.unlink()
    wyniki["nowa_klasa"] = nowa_wynik

    (TU / "wyniki.json").write_text(json.dumps(wyniki, ensure_ascii=False, indent=1), encoding="utf-8")

    for nazwa, r in wyniki["klasy"].items():
        print(f"== {nazwa}: walidacja {r['walidacja_ok']}/{r['spraw']}, roundtrip {r['roundtrip_identyczny']}/{r['spraw']}, "
              f"formaty: {len(r['naruszenia_formatu'])} naruszeń, pochodne {r['pochodne_zgodne']} zgodnych / "
              f"{len(r['pochodne_niezgodne'])} niezgodnych, mutanty {r['mutanty'] - len(r['mutanty_przezyly'])}/{r['mutanty']} zabite")
        for b in r["bledy_walidacji"][:3]:
            print("   walidacja:", b["plik"], b["bledy"][:2])
        print("   typy błędów walidacji:", Counter((tuple(x["loc"]), x["typ"]) for b in r["bledy_walidacji"] for x in b["bledy"]).most_common(6))
        print("   formaty:", Counter(x["pole"] for x in r["naruszenia_formatu"]).most_common(5), [x["wartosc"] for x in r["naruszenia_formatu"]][:5])
        print("   pochodne niezgodne:", Counter(x["pole"] for x in r["pochodne_niezgodne"]).most_common(5), r["pochodne_niezgodne"][:3])
        print("   mutanty przeżyły:", Counter(x["mutant"].split(":")[0] for x in r["mutanty_przezyly"]), r["mutanty_przezyly"][:3])
    print("== nowa klasa:", {k: v for k, v in nowa_wynik.items() if k != "schemat_llm"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
