"""Wspólne narzędzia grupy B (pola): dane rozwojowe, cache odczytu, F1 ewaluatorem produkcyjnym, LLM przez HTTP.

Zasady: strojenie tylko na zbiorze rozwojowym (`data/podzial.json`), zbiór kontrolny nie jest tu ładowany.
Klucz LLM czyta wyłącznie `harness/llm.py` (nie logujemy ani nie zapisujemy go ani nagłówków).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
HARNESS = EXP / "harness"
sys.path.insert(0, str(HARNESS))

import common  # noqa: E402,F401  (ustawia sys.path na backend)
from data import DocItem, load_items, reference_for  # noqa: E402

CACHE = HERE / "cache"
CACHE.mkdir(exist_ok=True)
CLASS_OF = {"odwolanie": "appeal", "pelnomocnictwo": "power_of_attorney", "przelew": "bank_transfer", "obcy": "foreign"}


def dev_items() -> list[DocItem]:
    """Rozwojowy zbiór: 49 spraw (147 dokumentów) + 12 negatywów organizatora."""
    return load_items("dev")


def read_text_cache() -> dict[str, Any]:
    """Odczyt warstwy tekstowej pdfium dla wszystkich dokumentów rozwojowych (cache JSON)."""
    p = CACHE / "texts_pdf.json"
    if p.is_file():
        return json.loads(p.read_text())
    from reading import PdfiumReader, NoOcr, read_document

    out: dict[str, Any] = {}
    for it in dev_items():
        try:
            reading, diag, _ = read_document(it.source.read_bytes(), reader=PdfiumReader(), ocr=NoOcr(), ocr_policy="never",
                                             ocr_dpi=150, max_pages=200)
            out[it.key] = {"class": it.document_class, "split": it.split,
                           "pages": [{"number": pg["number"], "text": pg["text"], "source": pg["source"]} for pg in reading["pages"]],
                           "requires_ocr": diag.get("requires_ocr") if isinstance(diag, dict) else getattr(diag, "requires_ocr", None)}
        except Exception as e:  # noqa: BLE001
            out[it.key] = {"class": it.document_class, "split": it.split, "pages": [], "error": f"{type(e).__name__}: {e}"}
    p.write_text(json.dumps(out, ensure_ascii=False))
    return out


def doc_text(entry: dict[str, Any], max_chars: int | None = None) -> str:
    t = "\n".join(f"[[strona {p['number']}]]\n{p['text']}" for p in entry["pages"])
    return t if max_chars is None else t[:max_chars]


def plain_text(entry: dict[str, Any]) -> str:
    return "\n".join(p["text"] for p in entry["pages"])


def leaves(x: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(x, dict):
        r: list[tuple[str, Any]] = []
        for k, v in x.items():
            r += leaves(v, f"{prefix}.{k}" if prefix else k)
        return r
    if isinstance(x, list):
        r = []
        for i, v in enumerate(x):
            r += leaves(v, f"{prefix}[{i}]")
        return r
    return [(prefix, x)]


def sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


# ---------- ocena: ewaluator produkcyjny (PR #8/#9) + bootstrap po sprawach ----------
import re  # noqa: E402
from collections import Counter  # noqa: E402

from odwolania2json.bootstrap import bootstrap_f1, paired_bootstrap_delta  # noqa: E402
from odwolania2json.evaluator import DEFAULT_CONFIG, EvalConfig, compare_document  # noqa: E402
from odwolania2json.evaluator import ClassTotals  # noqa: E402


def generic(path: str) -> str:
    return re.sub(r"\[\d+\]", "[]", path)


def outcomes(pred: dict[str, Any], ref: dict[str, Any], cfg: EvalConfig = DEFAULT_CONFIG,
             select: "re.Pattern[str] | None" = None) -> list[tuple[str, str]]:
    return [(o.path, o.verdict) for o in compare_document(pred, ref, cfg) if select is None or select.search(generic(o.path))]


def case_counts(per_doc: dict[str, list[tuple[str, str]]]) -> dict[str, ClassTotals]:
    """Liczniki po sprawie (klucz `case/plik` → `case`); wejście do bootstrapu po sprawach."""
    acc: dict[str, Counter[str]] = {}
    for key, outs in per_doc.items():
        c = acc.setdefault(key.split("/")[0], Counter())
        c.update(v for _, v in outs)
    return {k: ClassTotals(tp=c["tp"], tn=c["tn"], fp=c["fp"], fn=c["fn"]) for k, c in acc.items()}


def f1_report(per_doc: dict[str, list[tuple[str, str]]], seed: int = 1, resamples: int = 2000) -> dict[str, Any]:
    tot = Counter(v for outs in per_doc.values() for _, v in outs)
    ct = case_counts(per_doc)
    bi = bootstrap_f1(ct, seed=seed, resamples=resamples)
    return {"tp": tot["tp"], "tn": tot["tn"], "fp": tot["fp"], "fn": tot["fn"], "f1": round(bi.f1, 4),
            "ci95": [round(bi.low, 4), round(bi.high, 4)], "cases": len(ct), "documents": len(per_doc)}


def per_field(per_doc: dict[str, list[tuple[str, str]]]) -> dict[str, dict[str, int]]:
    out: dict[str, Counter[str]] = {}
    for outs in per_doc.values():
        for p, v in outs:
            out.setdefault(generic(p), Counter())[v] += 1
    res = {}
    for p, c in sorted(out.items()):
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        res[p] = {"tp": tp, "fp": fp, "fn": fn, "tn": c["tn"], "f1": round(2 * tp / (2 * tp + fp + fn), 3) if tp + fp + fn else None}
    return res


def versions() -> dict[str, str]:
    import platform
    from importlib.metadata import version
    v = {"python": platform.python_version()}
    for p in ("pydantic", "rapidfuzz", "pypdfium2", "httpx", "rapidocr"):
        try:
            v[p] = version(p)
        except Exception:  # noqa: BLE001
            pass
    return v
