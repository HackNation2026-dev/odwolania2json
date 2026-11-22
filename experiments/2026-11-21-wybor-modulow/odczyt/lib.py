"""Wspólne narzędzia grupy A: odnajdywalność wartości referencyjnych w tekście, pomiar czasu i RSS."""
from __future__ import annotations

import json
import re
import resource
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
for p in (EXP / "harness", HERE / "zestaw"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import common  # noqa: E402,F401
from rapidfuzz import fuzz  # noqa: E402

MONTHS = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "wrzesnia", "pazdziernika", "listopada", "grudnia"]
ID_FIELDS = ("krs", "nip", "regon", "na_rachunek", "z_rachunku", "pesel")
SKIP_FIELDS = ("czynnosc_powod_id", "przez-pelnomocnika", "typ", "czynnosc_opis")  # kody i opis interpretacyjny (nie literalny w tekście; to zadanie E09)


def fold(s: str) -> str:
    s = s.replace("ł", "l").replace("Ł", "L")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().casefold()


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9@]", "", fold(s))


def leaves(x: Any, p: str = "") -> list[tuple[str, Any]]:
    if isinstance(x, dict):
        return [t for k, v in x.items() for t in leaves(v, f"{p}.{k}")]
    if isinstance(x, list):
        return [t for v in x for t in leaves(v, p + "[]")]
    return [(p, x)]


def _date_forms(iso: str) -> list[str]:
    y, m, d = (int(v) for v in iso.split("-"))
    return [f"{d:02d}.{m:02d}.{y}", f"{d}.{m:02d}.{y}", f"{d:02d}-{m:02d}-{y}", iso, f"{d} {MONTHS[m - 1]} {y}", f"{d:02d} {MONTHS[m - 1]} {y}"]


def find_value(path: str, value: Any, text: str, tsq: str, tfold: str) -> str | None:
    """Zwraca 'exact' (po normalizacji), 'fuzzy' (podobieństwo ≥ 0,8) albo None. `tsq` = squash(text), `tfold` = fold(text)."""
    key = path.rsplit(".", 1)[-1]
    if isinstance(value, bool) or key in SKIP_FIELDS or value is None:
        return None
    if key == "kwota":
        v = float(value)
        forms = {f"{v:.2f}".replace(".", ","), f"{v:.2f}", f"{int(v)}" if v == int(v) else f"{v}"}
        ts = re.sub(r"[  ]", "", text)
        return "exact" if any(re.search(rf"(?<![\d,]){re.escape(f)}(?![\d])", ts) for f in forms) else None
    s = str(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        tt = fold(text)
        return "exact" if any(f in tt for f in _date_forms(s)) else None
    if key in ID_FIELDS:
        return "exact" if re.sub(r"\D", "", s) in re.sub(r"[^\d]", "", text) or re.sub(r"\D", "", s) in tsq else None
    if key == "numer_ted":  # referencja „999073-2026”, tekst „2026/S086-999073”: porównujemy części liczbowe
        a, y = s.split("-")
        return "exact" if (a in tsq and y in tsq) else None
    q = squash(s)
    if q and q in tsq:
        return "exact"
    if len(s) >= 8 and fuzz.partial_ratio(fold(s), tfold) >= 80:
        return "fuzzy"
    return None


def findability(ref: dict, text: str) -> dict[str, Any]:
    tsq, tf = squash(text), fold(text)
    per: dict[str, list[int]] = {}
    miss: list[str] = []
    for path, v in leaves(ref):
        if v is None or path.rsplit(".", 1)[-1] in SKIP_FIELDS:
            continue
        r = find_value(path, v, text, tsq, tf)
        b = per.setdefault(path, [0, 0, 0])  # exact, fuzzy, total
        b[2] += 1
        if r == "exact":
            b[0] += 1
        elif r == "fuzzy":
            b[1] += 1
        else:
            miss.append(f"{path}={str(v)[:40]}")
    return {"per_path": per, "missed": miss}


def merge_find(acc: dict[str, list[int]], one: dict[str, Any]) -> None:
    for p, b in one["per_path"].items():
        a = acc.setdefault(p, [0, 0, 0])
        for i in range(3):
            a[i] += b[i]


def totals(acc: dict[str, list[int]]) -> dict[str, Any]:
    e = sum(b[0] for b in acc.values()); f = sum(b[1] for b in acc.values()); n = sum(b[2] for b in acc.values())
    return {"exact": e, "fuzzy_only": f, "total": n, "exact_rate": round(e / n, 4) if n else None,
            "exact_or_fuzzy_rate": round((e + f) / n, 4) if n else None}


def pctl(xs: list[float], q: float) -> float:
    s = sorted(xs)
    if not s:
        return float("nan")
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 4)


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)


def versions() -> dict[str, Any]:
    import importlib.metadata as md
    import platform
    v = {"python": sys.version.split()[0], "cpu_count": __import__("os").cpu_count(), "machine": platform.machine()}
    for pkg in ("pypdfium2", "pypdf", "rapidocr", "onnxruntime", "numpy", "pillow", "opencv-python-headless", "pdfminer.six", "pymupdf"):
        try:
            v[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            pass
    return v


def dump(path: Path, obj: Any) -> None:
    common.write_json_atomic(path, obj)
