"""Inwentarz wszystkich PDF-ów UZP: metryki stron, obrazy stron, manifest przebiegu.

Zachowuje istniejące wyniki modeli w dokumenty/<id>.json. Nie dotyka adnotacje/.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from wspolne import (DPI, MAT, PRZEBIEG, REPO, RUN, TAKSONOMIA, normalizuj, obrazy_strony, pdfinfo, slug,
                     tekst_strony, typ_dokumentu, typ_strony, uruchom, wczytaj_json, zapisz_json)

MODELE = [
    {"id": "codex", "nazwa": "Codex CLI", "model": "gpt-6.1-sol", "uwagi": "codex exec, tryb tylko do odczytu, --output-schema"},
    {"id": "claude", "nazwa": "Claude Code CLI", "model": "domyślny model CLI (zapisany w wynikach surowych)", "uwagi": "claude -p, --json-schema, narzędzie Read do obrazów"},
    {"id": "minimax", "nazwa": "MiniMax", "model": "MiniMax-M3.1-Flash-Preview", "uwagi": "API zgodne z Anthropic, https://api.minimax.io/anthropic (serwery poza UE; tylko eksperyment)"},
]
KLASA_PLIKU = {"odwolanie.pdf": "odwolanie", "pelnomocnictwo.pdf": "pelnomocnictwo", "potwierdzenie_przelewu.pdf": "przelew"}


def zrodla() -> list[dict]:
    wynik = []
    for sprawa in sorted((MAT / "dane").glob("przyklad_*")):
        for plik, klasa in KLASA_PLIKU.items():
            p = sprawa / plik
            if p.exists():
                wynik.append({"id": f"p{sprawa.name[-2:]}_{klasa}", "pdf": p, "zrodlo": "pozytywny", "klasa": klasa, "sprawa": sprawa.name})
    for p in sorted((MAT / "dane" / "negatywne").glob("*.pdf")):
        wynik.append({"id": f"n_{slug(p.stem, 40)}", "pdf": p, "zrodlo": "negatywny", "klasa": "obcy", "sprawa": None})
    for p in sorted((MAT / "szablon-aplikacja").rglob("*.pdf")):
        klasa = "obcy" if "negatyw" in p.name else "odwolanie"
        wynik.append({"id": f"s_{slug(p.stem, 40)}", "pdf": p, "zrodlo": "szablon", "klasa": klasa, "sprawa": None})
    synt = RUN / "syntetyczne" / "syntetyczne.json"
    if synt.exists():
        for d in wczytaj_json(synt)["dokumenty"]:
            wynik.append({"id": d["id"], "pdf": RUN / d["plik"], "zrodlo": "syntetyczny", "klasa": d["klasa"],
                          "sprawa": d["sprawa"], "wstrzykniete": d["wstrzykniete"]})
    ids = [w["id"] for w in wynik]
    assert len(ids) == len(set(ids)), "zduplikowane id"
    return wynik


def proba_pozytywnych() -> set[str]:
    """Sprawy wysyłane do modeli: źródła syntetyków + sprawy z wieloma zamawiającymi/mocodawcami."""
    synt = RUN / "syntetyczne" / "syntetyczne.json"
    sprawy = set(wczytaj_json(synt)["sprawy_zrodlowe"].values()) if synt.exists() else set()
    for s in sorted((MAT / "dane").glob("przyklad_*")):
        o = json.loads((s / "odwolanie.json").read_text(encoding="utf-8"))
        p = json.loads((s / "pelnomocnictwo.json").read_text(encoding="utf-8"))
        if len(o["Zamawiajacy"]) > 1 and not any("zam" in x for x in sprawy):
            sprawy.add(s.name); sprawy.add("zam")
        if len(p["mocodawca"]) > 1 and not any("moc" in x for x in sprawy):
            sprawy.add(s.name); sprawy.add("moc")
    return sprawy - {"zam", "moc"}


def renderuj(pdf: Path, katalog: Path, n: int) -> None:
    katalog.mkdir(parents=True, exist_ok=True)
    if len(list(katalog.glob("p*.jpg"))) == n:
        return
    with tempfile.TemporaryDirectory() as d:
        uruchom(["pdftoppm", "-r", str(DPI), "-jpeg", "-jpegopt", "quality=80", str(pdf), f"{d}/s"])
        pliki = sorted(Path(d).glob("s-*.jpg"), key=lambda x: int(x.stem.split("-")[-1]))
        for i, f in enumerate(pliki, 1):
            shutil.move(str(f), katalog / f"p{i:03d}.jpg")


def main() -> None:
    proba = proba_pozytywnych()
    dokumenty_manifest = []
    for z in zrodla():
        pdf: Path = z["pdf"]
        info = pdfinfo(pdf)
        strony = []
        for nr in range(1, info["n"] + 1):
            w, h = info["strony"].get(nr, {}).get("rozmiar", (595.0, 842.0))
            tekst = tekst_strony(pdf, nr)
            znaki = len("".join(tekst.split()))
            liczba, pokrycie, dpi = obrazy_strony(pdf, nr, w, h)
            strony.append({"nr": nr, "obraz": f"strony/{z['id']}/p{nr:03d}.jpg", "szerokosc_pt": w, "wysokosc_pt": h,
                           "obrot_pdf": info["strony"].get(nr, {}).get("rot", 0), "znaki_tekstu": znaki, "obrazy": liczba,
                           "pokrycie_obrazami": round(pokrycie, 3), "dpi_obrazow": dpi, "typ_auto": typ_strony(znaki, pokrycie),
                           "probka_tekstu": normalizuj(tekst)[:400]})
        renderuj(pdf, RUN / "strony" / z["id"], info["n"])
        sciezka = RUN / "dokumenty" / f"{z['id']}.json"
        poprzednie = wczytaj_json(sciezka).get("modele", {}) if sciezka.exists() else {}
        rel = pdf.relative_to(REPO).as_posix()
        dok = {"id": z["id"], "plik_zrodlowy": rel, "zrodlo": z["zrodlo"], "klasa_oczekiwana": z["klasa"], "sprawa": z["sprawa"],
               "metadane": {"producent": info["info"].get("Producer"), "kreator": info["info"].get("Creator"),
                            "rozmiar_bajtow": pdf.stat().st_size, "zaszyfrowany": info["info"].get("Encrypted", "no").startswith("yes"),
                            "wersja_pdf": info["info"].get("PDF version")},
               "strony": strony, "wstrzykniete": z.get("wstrzykniete", []), "modele": poprzednie}
        zapisz_json(sciezka, dok)
        do_modeli = z["zrodlo"] != "pozytywny" or z["sprawa"] in proba
        dokumenty_manifest.append({"id": z["id"], "plik_zrodlowy": rel, "zrodlo": z["zrodlo"], "klasa_oczekiwana": z["klasa"],
                                   "sprawa": z["sprawa"], "liczba_stron": info["n"], "plik_wynikow": f"dokumenty/{z['id']}.json",
                                   "typ_auto": typ_dokumentu([s["typ_auto"] for s in strony]), "przeslany_do_modeli": do_modeli})
    manifest = {"format": "uzp-przypadki-brzegowe", "wersja": 1, "przebieg": PRZEBIEG,
                "utworzono": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                "opis": "Przegląd typów plików i przypadków brzegowych UZP: metryki stron (poppler), syntetyczne skany, ocena przez modele.",
                "taksonomia": [{"kod": k, "nazwa": n, "opis": o} for k, n, o in TAKSONOMIA],
                "modele": MODELE, "dokumenty": dokumenty_manifest}
    zapisz_json(RUN / "manifest.json", manifest)
    from collections import Counter
    print("dokumentów:", len(dokumenty_manifest), "| stron:", sum(d["liczba_stron"] for d in dokumenty_manifest),
          "| do modeli:", sum(d["przeslany_do_modeli"] for d in dokumenty_manifest))
    print(Counter((d["zrodlo"], d["typ_auto"]) for d in dokumenty_manifest))
    print("sprawy pozytywne w próbie:", sorted(proba))


if __name__ == "__main__":
    main()
