"""E-czynnosc: replay zapisanych odpowiedzi LLM (E10, tekst + prompt p2) przed i po regułach Z05.

Bez nowych wywołań API i bez zbioru kontrolnego: 25 spraw z `llm-e2e/subset_dev.json`, odpowiedzi z
`llm-e2e/E10/raw/e10-text-p2.jsonl` (do 5 powtórzeń na dokument), tekst dokumentów z `pola/cache/texts_pdf.json`.
„Po” = `odwolania2json.domain.czynnosc.refine_appeal` zastosowane do zapisanego wyniku odwołania.

Uruchomienie (z korzenia repozytorium):
  PYTHONPATH=apps/backend:packages/contracts .venv-exp/bin/python \
      experiments/2026-11-21-wybor-modulow/produkt/e_czynnosc_replay.py
"""

from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

EXP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXP / "llm-e2e" / "lib"))
sys.path.insert(0, str(EXP / "harness"))

import analyze as A  # noqa: E402
import score  # noqa: E402
from odwolania2json.bootstrap import paired_bootstrap_delta  # noqa: E402
from odwolania2json.domain.czynnosc import refine_appeal  # noqa: E402
from odwolania2json.evaluator import ClassTotals  # noqa: E402

FIELDS = {
    "czynnosc_powod_id": "OdwolanieKIO.czynnosc_powod_id",
    "czynnosc_opis": "OdwolanieKIO.czynnosc_opis",
    "czynnosc_dzien": "OdwolanieKIO.czynnosc_dzien",
    "numer_bzp": "ZamowieniePubliczne.numer_bzp",
    "pelnomocnik.imie_nazwisko": "Odwolujacy[].pelnomocnik.imie_nazwisko",
}
ABLATIONS = {
    "tylko czynność": ("OdwolanieKIO",),
    "tylko numer_bzp": ("ZamowieniePubliczne",),
    "tylko imię pełnomocnika": ("Odwolujacy",),
    "wszystko": ("OdwolanieKIO", "ZamowieniePubliczne", "Odwolujacy"),
}


def load() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases = set(json.loads((EXP / "llm-e2e" / "subset_dev.json").read_text())["cases"])
    recs = [r for r in A.raw("E10", "e10-text-p2") if r["case_id"] in cases]
    texts = json.loads((EXP / "pola" / "cache" / "texts_pdf.json").read_text())
    return recs, texts


def doc_text(texts: dict[str, Any], key: str) -> str:
    return "\n".join(f"[[strona {p['number']}]]\n{p['text']}" for p in texts[key]["pages"])


def after(
    recs: list[dict[str, Any]], texts: dict[str, Any], sections: tuple[str, ...]
) -> list[dict[str, Any]]:
    out = []
    for r in recs:
        r2 = copy.deepcopy(r)
        if r.get("result") and r.get("class_id") == "appeal":
            refined = refine_appeal(r["result"], doc_text(texts, r["key"]))
            for s in sections:
                if s in refined:
                    r2["result"][s] = refined[s]
        out.append(r2)
    return out


def field_counts(recs: list[dict[str, Any]], field: str) -> dict[str, ClassTotals]:
    per_case: dict[str, Counter[str]] = {}
    for r in recs:
        c = per_case.setdefault(r["case_id"], Counter())
        for o in score.doc_metrics(r).outcomes:
            if score.field_key(o.path) == field:
                c[o.verdict] += 1
    return {
        k: ClassTotals(tp=c["tp"], tn=c["tn"], fp=c["fp"], fn=c["fn"]) for k, c in per_case.items()
    }


def f1_of(counts: dict[str, ClassTotals]) -> float:
    tp = sum(v.tp for v in counts.values())
    fp = sum(v.fp for v in counts.values())
    fn = sum(v.fn for v in counts.values())
    return 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else float("nan")


def delta(a: dict[str, ClassTotals], b: dict[str, ClassTotals]) -> dict[str, Any]:
    d = paired_bootstrap_delta(a, b, seed=A.SEED, resamples=2000)
    return {
        "delta": round(d.delta, 4),
        "ci95": [round(d.low, 4), round(d.high, 4)],
        "cases": d.cases,
    }


def main() -> None:
    recs, texts = load()
    appeals = [r for r in recs if r["expected_class"] == "odwolanie"]
    out: dict[str, Any] = {
        "docs": len(recs),
        "appeal_rows": len(appeals),
        "cases": len({r["case_id"] for r in recs}),
    }
    base_all = score.summarize_records(recs, seed=A.SEED)
    out["before"] = {"f1": base_all["f1"], "ci95": base_all["ci95"]}
    for name, sections in ABLATIONS.items():
        new = after(recs, texts, sections)
        s = score.summarize_records(new, seed=A.SEED)
        out[name] = {
            "f1_all": s["f1"],
            "ci95_all": s["ci95"],
            "paired_all": score.paired(recs, new, seed=A.SEED),
        }
        per = {}
        for label, field in FIELDS.items():
            a, b = field_counts(recs, field), field_counts(new, field)
            per[label] = {
                "f1_before": round(f1_of(a), 4),
                "f1_after": round(f1_of(b), 4),
                **delta(a, b),
            }
        out[name]["per_field"] = per
    (Path(__file__).parent / "e_czynnosc_wyniki.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1)
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
