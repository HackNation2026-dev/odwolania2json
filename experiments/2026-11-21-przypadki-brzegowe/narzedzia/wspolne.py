"""Wspólne definicje eksperymentu przypadków brzegowych (kod jednorazowy)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
REPO = EXP.parents[1]
MAT = REPO / "docs" / "02-materialy" / "organizator-uzp"
FORMAT = EXP / "format"
PRZEBIEG = os.environ.get("PRZEBIEG", "2026-11-21-v1")
RUN = EXP / "wyniki" / PRZEBIEG
DPI = 100
MAKS_STRON_DO_MODELI = 3

KATALOG = REPO / "docs/05-weryfikacja/przypadki-brzegowe.json"
TAKSONOMIA = [
    (p["kod"], p["nazwa"], p["definicja"])
    for p in json.loads(KATALOG.read_text(encoding="utf-8"))["przypadki"]
]
if len({k for k, _, _ in TAKSONOMIA}) != len(TAKSONOMIA):
    raise ValueError("Powtórzony kod w kanonicznym katalogu")

KODY = [k for k, _, _ in TAKSONOMIA]


def slug(tekst: str, maks: int = 50) -> str:
    t = unicodedata.normalize("NFKD", tekst.replace("ł", "l").replace("Ł", "L"))
    t = t.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")[:maks].strip("_")


def zapisz_json(sciezka: Path, dane) -> None:
    sciezka.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=sciezka.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=1)
    os.replace(tmp, sciezka)


def wczytaj_json(sciezka: Path):
    return json.loads(sciezka.read_text(encoding="utf-8"))


def uruchom(cmd: list[str], **kw) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def pdfinfo(pdf: Path) -> dict:
    out = uruchom(["pdfinfo", str(pdf)])
    info = {}
    for linia in out.splitlines():
        if ":" in linia:
            k, v = linia.split(":", 1)
            info[k.strip()] = v.strip()
    n = int(info.get("Pages", "0"))
    strony = {}
    if n:
        out2 = uruchom(["pdfinfo", "-f", "1", "-l", str(n), str(pdf)])
        for linia in out2.splitlines():
            m = re.match(r"Page\s+(\d+)\s+size:\s+([\d.]+) x ([\d.]+)", linia)
            if m:
                strony.setdefault(int(m.group(1)), {})["rozmiar"] = (float(m.group(2)), float(m.group(3)))
            m = re.match(r"Page\s+(\d+)\s+rot:\s+(-?\d+)", linia)
            if m:
                strony.setdefault(int(m.group(1)), {})["rot"] = int(m.group(2))
    return {"info": info, "n": n, "strony": strony}


def tekst_strony(pdf: Path, nr: int) -> str:
    return uruchom(["pdftotext", "-f", str(nr), "-l", str(nr), "-layout", str(pdf), "-"])


def obrazy_strony(pdf: Path, nr: int, w_pt: float, h_pt: float) -> tuple[int, float, float | None]:
    """(liczba obrazów, pokrycie strony 0-1, dpi największego obrazu)."""
    out = uruchom(["pdfimages", "-list", "-f", str(nr), "-l", str(nr), str(pdf)])
    liczba, pole, najw, dpi = 0, 0.0, 0.0, None
    for linia in out.splitlines()[2:]:
        k = linia.split()
        if len(k) < 14 or k[2] not in ("image", "stencil"):
            continue
        szer, wys, xppi, yppi = int(k[3]), int(k[4]), float(k[12]), float(k[13])
        if xppi <= 0 or yppi <= 0:
            continue
        p = (szer / xppi * 72) * (wys / yppi * 72)
        liczba += 1
        pole += p
        if p > najw:
            najw, dpi = p, round((xppi + yppi) / 2, 1)
    return liczba, min(1.0, pole / (w_pt * h_pt)) if w_pt * h_pt else 0.0, dpi


def typ_strony(znaki: int, pokrycie: float) -> str:
    if znaki > 50 and pokrycie >= 0.8:
        return "skan_z_ocr"
    if znaki <= 50 and pokrycie >= 0.5:
        return "skan"
    if znaki > 50 and pokrycie > 0.05:
        return "mieszana"
    if znaki <= 50:
        return "pusta"
    return "tekst"


def typ_dokumentu(typy: list[str]) -> str:
    s = set(typy) - {"pusta"}
    if not s:
        return "pusty"
    if s <= {"tekst"}:
        return "tekst"
    if s <= {"skan", "skan_z_ocr"}:
        return "skan"
    return "mieszany"


def normalizuj(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()
