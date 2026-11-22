"""Luki grupy C (E20): edycje tekstu prawdziwych dokumentów rozwojowych z wyprowadzoną referencją (syntetyczne, deterministyczne).

g1 brak pełnomocnika (odwołanie bez „reprezentowana przez/adres do korespondencji/tel.”, bez „w oparciu o załączone pełnomocnictwo”)
g2 powód 12 (pierwsza czynność = projektowane postanowienia umowy)
g3 brak BZP/TED (wartości usunięte, etykiety zostają jako przynęta)
g4 wpis 15 000,00 zł (kwota z separatorem tysięcy zamiast 200,00)
Referencja pochodzi z referencji oryginału zmodyfikowanej zgodnie z edycją; to małe próby (n podane w wynikach), nie reprezentują rozkładu.
"""
from __future__ import annotations

import copy
import re
from typing import Any

import lib

MONTHS = "stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia"


def g1(text: str, ref: dict) -> tuple[str, dict] | None:
    if "reprezentowan" not in text:
        return None
    t = re.sub(r"(?m)^reprezentowan\w* przez:.*\n", "", text)
    t = re.sub(r"(?ms)^adres do korespondencji:.*?\n(?=tel\.)", "", t)
    t = re.sub(r"(?m)^tel\..*\n", "", t)
    t = re.sub(r",?\s*w oparciu o\s+załączone\s+pełnomocnictwo,?", ",", t)
    t = re.sub(r"na podstawie\s+pełnomocnictwa załączonego do niniejszego odwołania,?", "", t)
    # podpis pod odwołaniem przez r. pr./adw. sugerowałby pełnomocnika: zastępujemy go podpisem odwołującego
    t = re.sub(r"(?m)^[a-z]\) pełnomocnictwo udzielone.*\n", "", t)
    t = re.sub(r"(?m)^\.{5,}\n[^\n]*, (?:r\. ?pr\.|adw\.)\n?", "", t)
    if "reprezentowan" in t or "adres do korespondencji" in t or re.search(r", (?:r\. ?pr\.|adw\.)\s*$", t, re.M):
        return None
    r = copy.deepcopy(ref)
    o = r["Odwolujacy"][0]
    o["przez-pelnomocnika"] = 0
    o["pelnomocnik"] = {"imie_nazwisko": None, "nazwa": None, "mail": None}
    return t, r


def g2(text: str, ref: dict) -> tuple[str, dict] | None:
    flat_m = re.search(r"Zamawiający w dniu \d{1,2} \w+ \d{4} (?:roku|r\.)\s+[^.]*\.", text)
    if not flat_m or "polegających na" in text:
        return None
    t = text.replace(flat_m.group(0), re.sub(r"(roku|r\.)\s+.*$", r"\1 udostępnił projektowane postanowienia umowy w sprawie zamówienia.", flat_m.group(0), flags=re.S))
    r = copy.deepcopy(ref)
    r["OdwolanieKIO"]["czynnosc_powod_id"] = 12
    r["OdwolanieKIO"]["czynnosc_opis"] = "Projektowane postanowienia umowy"
    return t, r


def g3(text: str, ref: dict) -> tuple[str, dict] | None:
    z = ref["ZamowieniePubliczne"]
    if not (z["numer_bzp"] and z["numer_ted"]):
        return None
    t = re.sub(r"\d{4}\s?/\s?BZP\s?\d{8}(?:/\d{2})?", "", text)
    t = re.sub(r"\d{4}\s?/\s?S\s?\d{1,3}\s?-\s?\d{6}|\d{6}-\d{4}", "", t)
    r = copy.deepcopy(ref)
    r["ZamowieniePubliczne"]["numer_bzp"] = None
    r["ZamowieniePubliczne"]["numer_ted"] = None
    return t, r


def g4(text: str, ref: dict) -> tuple[str, dict] | None:
    k = ref["przelew_bankowy"]["kwota"]
    forms = {f"{k:.2f}".replace(".", ","): "15 000,00", f"{k:.2f}": "15 000,00"}
    t = text
    hit = False
    for old, new in forms.items():
        if old in t:
            t = t.replace(old, new)
            hit = True
    if not hit:
        return None
    r = copy.deepcopy(ref)
    r["przelew_bankowy"]["kwota"] = 15000.0
    return t, r


GAPS = {"g1_brak_pelnomocnika": ("odwolanie", g1), "g2_powod_12": ("odwolanie", g2), "g3_brak_bzp_ted": ("odwolanie", g3), "g4_wpis_15000": ("przelew", g4)}


def build(per_gap: int = 8) -> list[dict[str, Any]]:
    t = lib.read_text_cache()
    out = []
    for name, (cls, fn) in GAPS.items():
        n = 0
        for it in lib.dev_items():
            if it.document_class != cls or n >= per_gap:
                continue
            ref = lib.reference_for(it)
            text = lib.plain_text(t[it.key])
            r = fn(text, ref)
            if r is None:
                continue
            out.append({"key": f"{name}/{it.key}", "gap": name, "class": cls, "text": r[0], "ref": r[1], "source": it.key})
            n += 1
    return out
