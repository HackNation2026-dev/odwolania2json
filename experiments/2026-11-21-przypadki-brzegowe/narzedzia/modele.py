"""Wysyła pierwsze strony dokumentów z próbki do modeli i zapisuje surowe wyniki.

Użycie: python modele.py <model> [--id ID ...] [--rownolegle N] [--ponow]
model: codex | claude | minimax
Surowe wyniki: RUN/_surowe/<model>/<id>.json (status, czas, wynik lub błąd, metadane wywołania).
Klucz MiniMax czytany z pliku wskazanego w MINIMAX_KEY_FILE (domyślnie ~/kluczMiniMaxKacper); nigdy nie jest zapisywany.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import jsonschema

from wspolne import FORMAT, MAKS_STRON_DO_MODELI, RUN, TAKSONOMIA, wczytaj_json, zapisz_json

SCHEMAT = wczytaj_json(FORMAT / "wynik_modelu.schema.json")
SCHEMAT_TXT = json.dumps(SCHEMAT, ensure_ascii=False)
SCHEMAT_CLI = json.dumps({k: v for k, v in SCHEMAT.items() if k != "$schema"}, ensure_ascii=False)
LIMIT_S = 420
WERSJA_POLECENIA = 2  # 1: przelew = tylko „wpis od odwołania” (błąd definicji, wyniki w _surowe_polecenie1)


def polecenie(n_stron: int, k: int) -> str:
    kody = "\n".join(f"- {kod}: {opis}" for kod, _, opis in TAKSONOMIA)
    return f"""Oceniasz jeden plik PDF przed automatycznym OCR, klasyfikacją i ekstrakcją danych.
Dostajesz obrazy stron 1–{k} (plik ma łącznie {n_stron} stron). Obrazy są ponumerowane w kolejności.

Kontekst: system przetwarza dokumenty sprawy odwoławczej do Krajowej Izby Odwoławczej (KIO). Klasy:
- odwolanie: odwołanie wnoszone do KIO,
- pelnomocnictwo: pełnomocnictwo do reprezentowania wykonawcy,
- przelew: potwierdzenie przelewu bankowego związanego ze sprawą (np. wpis od odwołania albo opłata skarbowa od pełnomocnictwa),
- inny: każdy inny dokument (także wyroki KIO, ogłoszenia o zamówieniu, pisma urzędowe).

Dla pliku:
1. klasa: jedna z odwolanie, pelnomocnictwo, przelew, inny, niepewne; uzasadnij krótko.
2. Dla każdej otrzymanej strony:
   - typ: tekst (wygląda na cyfrowo wygenerowany PDF), skan (zdjęcie lub skan), mieszana (oba na jednej stronie), pusta;
   - obrot_stopnie: o ile stopni zgodnie z ruchem wskazówek zegara jest obrócona treść względem normalnej orientacji (0, 90, 180, 270);
   - jakosc: dobra, srednia, slaba (czytelność dla OCR);
   - transkrypcja_poczatku: przepisz dosłownie pierwsze około 200 znaków treści strony w normalnej kolejności czytania, bez poprawiania; pusty tekst dla pustej strony;
   - problemy: przypadki brzegowe na tej stronie.
3. problemy_dokumentu: przypadki brzegowe całego pliku.

Kody problemów (pole kod musi być jednym z nich):
{kody}

Wymieniaj tylko problemy, które faktycznie widzisz. Gdy brak problemów, zwróć pustą listę. Opis po polsku, konkretny (gdzie, co).
Odpowiedz wyłącznie obiektem JSON zgodnym ze schematem:
{SCHEMAT_TXT}"""


def obrazy(dok: dict) -> list[Path]:
    return [RUN / s["obraz"] for s in dok["strony"][:MAKS_STRON_DO_MODELI]]


def wyciagnij_json(tekst: str) -> dict:
    tekst = tekst.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", tekst, re.S)
    if m:
        tekst = m.group(1)
    start, koniec = tekst.find("{"), tekst.rfind("}")
    return json.loads(tekst[start:koniec + 1])


def wywolaj_codex(dok: dict, pliki: list[Path], prompt: str) -> tuple[dict, dict]:
    out = RUN / "_surowe" / "codex" / f"{dok['id']}.ostatnia.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "--ephemeral", "-C", str(RUN),
           "--output-schema", str(FORMAT / "wynik_modelu.schema.json"), "-o", str(out)]
    for p in pliki:
        cmd += ["-i", str(p)]
    cmd += ["-"]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=LIMIT_S)
    if r.returncode != 0:
        raise RuntimeError(f"codex kod {r.returncode}: {r.stderr[-800:]}")
    return wyciagnij_json(out.read_text(encoding="utf-8")), {"stderr_ogon": r.stderr[-300:]}


def wywolaj_claude(dok: dict, pliki: list[Path], prompt: str) -> tuple[dict, dict]:
    lista = "\n".join(f"Strona {i}: {p}" for i, p in enumerate(pliki, 1))
    tresc = f"Najpierw obejrzyj narzędziem Read każdy z plików obrazów stron:\n{lista}\n\n{prompt}"
    cmd = ["claude", "-p", "--output-format", "json", "--json-schema", SCHEMAT_CLI, "--allowedTools", "Read",
           "--add-dir", str(RUN), "--no-session-persistence"]
    r = subprocess.run(cmd, input=tresc, capture_output=True, text=True, timeout=LIMIT_S, cwd=str(RUN))
    if r.returncode != 0:
        raise RuntimeError(f"claude kod {r.returncode}: {(r.stderr or r.stdout)[-800:]}")
    odp = json.loads(r.stdout)
    if odp.get("is_error"):
        raise RuntimeError(f"claude błąd: {str(odp.get('result'))[:800]}")
    wynik = odp.get("structured_output") or wyciagnij_json(odp.get("result", ""))
    meta = {"model": list((odp.get("modelUsage") or {}).keys()), "koszt_usd": odp.get("total_cost_usd"), "tury": odp.get("num_turns")}
    return wynik, meta


def wywolaj_minimax(dok: dict, pliki: list[Path], prompt: str) -> tuple[dict, dict]:
    klucz = Path(os.environ.get("MINIMAX_KEY_FILE", Path.home() / "kluczMiniMaxKacper")).read_text().strip()
    tresc = []
    for i, p in enumerate(pliki, 1):
        tresc.append({"type": "text", "text": f"Strona {i}:"})
        tresc.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(p.read_bytes()).decode()}})
    tresc.append({"type": "text", "text": prompt})
    cialo = {"model": "MiniMax-M3.1-Flash-Preview", "max_tokens": 40000, "temperature": 0.1,
             "output_config": {"effort": os.environ.get("MINIMAX_EFFORT", "medium")},
             "messages": [{"role": "user", "content": tresc}]}
    req = urllib.request.Request("https://api.minimax.io/anthropic/v1/messages", data=json.dumps(cialo).encode(),
                                 headers={"Content-Type": "application/json", "x-api-key": klucz, "Authorization": f"Bearer {klucz}",
                                          "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=LIMIT_S) as resp:
            odp = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"minimax HTTP {e.code}: {e.read()[:600]!r}") from None
    tekst = "".join(b.get("text", "") for b in odp.get("content", []) if b.get("type") == "text")
    meta = {"model": odp.get("model"), "uzycie": odp.get("usage"), "stop": odp.get("stop_reason"),
            "effort": cialo["output_config"]["effort"]}
    try:
        return wyciagnij_json(tekst), meta
    except ValueError:
        typy = [b.get("type") for b in odp.get("content", [])]
        raise RuntimeError(f"brak JSON; stop={meta['stop']}, bloki={typy}, uzycie={meta['uzycie']}, tekst={tekst[:300]!r}") from None


WYWOLANIA = {"codex": wywolaj_codex, "claude": wywolaj_claude, "minimax": wywolaj_minimax}


def przetworz(model: str, dok_id: str, ponow: bool) -> str:
    cel = RUN / "_surowe" / model / f"{dok_id}.json"
    if cel.exists() and not ponow and wczytaj_json(cel)["status"] == "ok":
        return f"{dok_id}: pominięto (jest)"
    dok = wczytaj_json(RUN / "dokumenty" / f"{dok_id}.json")
    pliki = obrazy(dok)
    t0 = time.monotonic()
    zapis = {"id": dok_id, "model": model, "wersja_polecenia": WERSJA_POLECENIA, "strony_przeslane": list(range(1, len(pliki) + 1))}
    try:
        wynik, meta = WYWOLANIA[model](dok, pliki, polecenie(len(dok["strony"]), len(pliki)))
        jsonschema.validate(wynik, SCHEMAT)
        zapis |= {"status": "ok", "wynik": wynik, "blad": None, "meta": meta}
    except Exception as e:  # noqa: BLE001 — eksperyment: każdy błąd zapisujemy jako wynik
        zapis |= {"status": "blad", "wynik": None, "blad": f"{type(e).__name__}: {str(e)[:900]}", "meta": {}}
    zapis["czas_s"] = round(time.monotonic() - t0, 1)
    zapisz_json(cel, zapis)
    return f"{dok_id}: {zapis['status']} ({zapis['czas_s']} s){'' if zapis['status'] == 'ok' else ' ' + zapis['blad'][:160]}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model", choices=list(WYWOLANIA))
    ap.add_argument("--id", nargs="*")
    ap.add_argument("--rownolegle", type=int, default=3)
    ap.add_argument("--ponow", action="store_true")
    a = ap.parse_args()
    manifest = wczytaj_json(RUN / "manifest.json")
    ids = a.id or [d["id"] for d in manifest["dokumenty"] if d["przeslany_do_modeli"]]
    with ThreadPoolExecutor(a.rownolegle) as ex:
        for linia in ex.map(lambda i: przetworz(a.model, i, a.ponow), ids):
            print(f"[{a.model}] {linia}", flush=True)


if __name__ == "__main__":
    main()
