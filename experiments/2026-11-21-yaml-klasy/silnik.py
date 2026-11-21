"""Eksperyment 2026-11-21: czy YAML v0 wystarcza do opisu klasy dokumentu.

Kod jednorazowy (spike). Buduje z YAML dynamiczny model pydantic (ścisłe typy,
stała kolejność kluczy, brak dodatkowych kluczy), JSON Schema dla LLM oraz
wylicza pola pochodne funkcjami z rejestru.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, create_model

# --- rejestr nazwanych funkcji: jedyne miejsce, gdzie klasa sięga do kodu ---
NORMALIZATORY = {"kwota", "rachunek", "krs", "nip", "regon", "pesel", "bzp", "ted"}
POCHODNE = {"ze_slownika", "obecnosc", "null_gdy_lista_jednoelementowa"}
TYPY = {"tekst", "data", "liczba", "liczba_calkowita", "enum", "obiekt", "lista"}
KLUCZE_POLA = {
    "typ", "nullable", "opis", "format", "normalizator", "metoda", "dopasowanie",
    "dopasowanie_listy", "pola", "element", "wartosci", "klucz", "pochodne",
    "min", "max", "zakres", "rola",
}


class BladKonfiguracji(ValueError):
    pass


def wczytaj_slownik(sciezka: Path) -> dict[int, str]:
    wynik = {}
    for linia in sciezka.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*(\d+)=(.+?)[\s,.\"]*$", linia)
        if m:
            wynik[int(m.group(1))] = m.group(2).strip()
    return wynik


class Klasa:
    def __init__(self, sciezka: Path):
        self.sciezka = sciezka
        self.cfg = yaml.safe_load(sciezka.read_text(encoding="utf-8"))
        self.nazwa = self.cfg["klasa"]
        self.slowniki = {
            k: wczytaj_slownik((sciezka.parent / v).resolve())
            for k, v in (self.cfg.get("slowniki") or {}).items()
        }
        self._sprawdz(self.cfg["pola"], self.nazwa)
        self.model = self._model(self.cfg["pola"], self.nazwa)

    # walidacja samej konfiguracji: błąd w YAML ma wyjść przy starcie, nie w trakcie
    def _sprawdz(self, pola: dict, sciezka: str) -> None:
        for nazwa, p in pola.items():
            gdzie = f"{sciezka}.{nazwa}"
            nieznane = set(p) - KLUCZE_POLA
            if nieznane:
                raise BladKonfiguracji(f"{gdzie}: nieznane klucze {sorted(nieznane)}")
            if p.get("typ") not in TYPY:
                raise BladKonfiguracji(f"{gdzie}: nieznany typ {p.get('typ')!r}")
            if p.get("normalizator") and p["normalizator"] not in NORMALIZATORY:
                raise BladKonfiguracji(f"{gdzie}: brak normalizatora {p['normalizator']!r} w rejestrze")
            if p.get("pochodne") and p["pochodne"]["funkcja"] not in POCHODNE:
                raise BladKonfiguracji(f"{gdzie}: brak funkcji {p['pochodne']['funkcja']!r} w rejestrze")
            if p.get("format"):
                re.compile(p["format"])
            if p["typ"] == "obiekt":
                self._sprawdz(p["pola"], gdzie)
            if p["typ"] == "lista":
                self._sprawdz({"[]": p["element"]}, gdzie)

    def _typ(self, p: dict, nazwa: str) -> Any:
        t = p["typ"]
        if t in ("tekst", "data"):
            typ = str
        elif t == "liczba":
            typ = float
        elif t == "liczba_calkowita":
            typ = int
        elif t == "enum":
            typ = Literal[tuple(p["wartosci"])]
        elif t == "obiekt":
            typ = self._model(p["pola"], nazwa)
        elif t == "lista":
            typ = list[self._typ(p["element"], nazwa + "_el")]
        return Optional[typ] if p.get("nullable") else typ

    def _model(self, pola: dict, nazwa: str) -> type[BaseModel]:
        definicje = {}
        for n, p in pola.items():
            kw: dict[str, Any] = {"description": p.get("opis")}
            if p.get("klucz"):
                kw["alias"] = p["klucz"]
            if p.get("format") and p["typ"] in ("tekst", "data"):
                kw["pattern"] = p["format"]
            if p["typ"] == "data":
                kw["pattern"] = r"^\d{4}-\d{2}-\d{2}$"
            if "min" in p:
                kw["ge"] = p["min"]
            if "max" in p:
                kw["le"] = p["max"]
            definicje[n] = (self._typ(p, f"{nazwa}_{n}"), Field(**kw))
        return create_model(
            re.sub(r"\W", "_", nazwa),
            __config__=ConfigDict(strict=True, extra="forbid", populate_by_name=False),
            **definicje,
        )

    def waliduj(self, dane: dict) -> BaseModel:
        return self.model.model_validate(dane)

    def serializuj(self, obiekt: BaseModel) -> dict:
        return obiekt.model_dump(by_alias=True, mode="json")

    # --- pola pochodne ---
    def pochodne(self, dane: dict) -> list[tuple[str, Any, Any]]:
        """Zwraca (ścieżka, wartość w danych, wartość wyliczona) dla każdego pola pochodnego."""
        wyniki: list[tuple[str, Any, Any]] = []
        self._pochodne(self.cfg["pola"], dane, "", None, wyniki)
        return wyniki

    def _pochodne(self, pola, dane, sciezka, lista_rodzica, wyniki):
        for n, p in pola.items():
            klucz = p.get("klucz", n)
            wartosc = dane.get(klucz)
            if p.get("pochodne"):
                f = p["pochodne"]
                if f["funkcja"] == "ze_slownika":
                    wyl = self.slowniki[f["slownik"]].get(dane.get(f["z"]))
                elif f["funkcja"] == "obecnosc":
                    o = dane
                    for czesc in f["z"].split("."):
                        o = (o or {}).get(czesc)
                    wyl = 1 if o else 0
                elif f["funkcja"] == "null_gdy_lista_jednoelementowa":
                    wyl = None if len(lista_rodzica) == 1 else wartosc
                wyniki.append((sciezka + "." + klucz, wartosc, wyl))
            if p["typ"] == "obiekt" and isinstance(wartosc, dict):
                self._pochodne(p["pola"], wartosc, sciezka + "." + klucz, None, wyniki)
            if p["typ"] == "lista" and isinstance(wartosc, list) and p["element"]["typ"] == "obiekt":
                for el in wartosc:
                    self._pochodne(p["element"]["pola"], el, sciezka + "." + klucz + "[]", wartosc, wyniki)

    # --- formaty ---
    def formaty(self, dane: dict) -> list[tuple[str, Any, str]]:
        """Zwraca naruszenia `format` (ścieżka, wartość, wzorzec)."""
        bledy: list[tuple[str, Any, str]] = []
        self._formaty(self.cfg["pola"], dane, "", bledy)
        return bledy

    def _formaty(self, pola, dane, sciezka, bledy):
        for n, p in pola.items():
            klucz = p.get("klucz", n)
            v = dane.get(klucz)
            if p.get("format") and v is not None and not re.fullmatch(p["format"], str(v)):
                bledy.append((sciezka + "." + klucz, v, p["format"]))
            if p["typ"] == "obiekt" and isinstance(v, dict):
                self._formaty(p["pola"], v, sciezka + "." + klucz, bledy)
            if p["typ"] == "lista" and isinstance(v, list) and p["element"]["typ"] == "obiekt":
                for el in v:
                    self._formaty(p["element"]["pola"], el, sciezka + "." + klucz + "[]", bledy)

    # --- schemat dla LLM: tylko pola z metoda: llm, bez pochodnych ---
    def schemat_llm(self) -> dict:
        def zbuduj(pola):
            props, req = {}, []
            for n, p in pola.items():
                if p.get("pochodne") and p.get("metoda") != "llm":
                    continue
                if p["typ"] == "obiekt":
                    s = zbuduj(p["pola"])
                    if not s["properties"]:
                        continue
                elif p["typ"] == "lista":
                    el = p["element"]
                    s = {"type": "array", "items": zbuduj(el["pola"]) if el["typ"] == "obiekt" else {"type": "string"}}
                    if el["typ"] == "obiekt" and not s["items"]["properties"]:
                        continue
                elif p.get("metoda") != "llm":
                    continue
                else:
                    t = {"tekst": "string", "data": "string", "liczba": "number",
                         "liczba_calkowita": "integer", "enum": "string"}[p["typ"]]
                    s = {"type": [t, "null"] if p.get("nullable") else t}
                    if p["typ"] == "enum":
                        s["enum"] = list(p["wartosci"]) + ([None] if p.get("nullable") else [])
                    if p.get("opis"):
                        s["description"] = p["opis"]
                k = p.get("klucz", n)
                props[k] = s
                req.append(k)
            return {"type": "object", "properties": props, "required": req, "additionalProperties": False}
        return zbuduj(self.cfg["pola"])
