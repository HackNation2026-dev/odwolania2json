"""E11: warianty ścieżki pionowej per typ wejścia, ablacje, porównania sparowane. Wyjście: E11/wyniki.json.

Typy wejścia: tekst (oryginały), skan (cały dokument jako obraz), mieszany (str. 1 tekst + skan), S2 (dane tylko w obrazie na stronie tekstowej),
S5 (poprawny obraz + błędna niewidoczna warstwa tekstowa).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import analyze as A
import score

TEXT_RUNS = {"rules": ("E11", "e11-rules-text"), "A": ("E10", "e10-text-p2"), "C": ("E10", "e10-image-p2"), "D": ("E10", "e10-textimg-p2"),
             "A+regex_override": ("E11", "e11-abl-regex_override"), "A+regex_fill": ("E11", "e11-abl-regex_fill"), "A_replay": ("E11", "e11-abl-replay-none")}
SCAN_RUNS = {"rules+OCR": "e11-rules-scan", "A": "e11-scan-A", "B": "e11-scan-B", "B_ocr_always": "e11-scan-Balways", "C": "e11-scan-C", "D": "e11-scan-D"}
SCAN_TYPES = ["skan", "mieszany", "s2", "s5"]


def cell(recs: list[dict[str, Any]]) -> dict[str, Any]:
    if not recs:
        return {"status": "brak"}
    s = score.summarize_records(recs, seed=A.SEED, resamples=1000)
    L = score.llm_stats(recs)
    return {"docs": s["docs"], "cases": s["cases"], "f1": s["f1"], "ci95": s["ci95"], "tp": s["tp"], "fp": s["fp"], "fn": s["fn"],
            "per_class_f1": {k: v["f1"] for k, v in s["per_class"].items()}, "classification_acc": s["classification_acc"], "outcomes": s["outcomes"],
            "technical_errors": L["technical_errors"], "input_tokens_per_doc": L["input_tokens_per_doc"], "output_tokens_per_doc": L["output_tokens_per_doc"],
            "doc_wall_median_s_UNDER_LOAD": L["doc_wall_median_s"], "doc_wall_p95_s_UNDER_LOAD": L["doc_wall_p95_s"], "per_field_f1": {k: v["f1"] for k, v in s["per_field"].items()}}


def pair(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not a or not b:
        return None
    ka, kb = A.keyset(a), A.keyset(b)
    keys = ka & kb
    reps = A.common_reps(a, b)
    return score.paired(A.restrict(a, keys, reps), A.restrict(b, keys, reps), seed=A.SEED) | {"docs": len(keys), "reps_used": reps}


def main() -> None:
    out: dict[str, Any] = {"text": {}, "scan": {}, "paired": {}}
    text = {n: A.raw(*src) for n, src in TEXT_RUNS.items()}
    # tekst: pierwsze powtórzenie wszędzie (porównywalność z 1-powtórzeniowymi ablacjami); dla A,C,D także wszystkie powtórzenia
    for n, r in text.items():
        out["text"][n] = {"rep1": cell(A.restrict(r, max_rep=1)), "all_reps": cell(r) if n in ("A", "C", "D") else None}
    for t in SCAN_TYPES:
        out["scan"][t] = {}
        for n, name in SCAN_RUNS.items():
            out["scan"][t][n] = cell(A.restrict(A.raw("E11", name), variants={t}))
    P = out["paired"]
    P["text: A vs rules"] = pair(A.restrict(text["rules"]), A.restrict(text["A"], max_rep=1))
    for x in ("C", "D"):
        P[f"text: {x} vs A"] = pair(A.restrict(text["A"], max_rep=1), A.restrict(text[x]))
    for x in ("A+regex_override", "A+regex_fill"):
        P[f"text: {x} vs A_replay"] = pair(A.restrict(text["A_replay"]), A.restrict(text[x]))
    for t in SCAN_TYPES:
        g = lambda n: A.restrict(A.raw("E11", SCAN_RUNS[n]), variants={t})  # noqa: E731
        for a, b in (("A", "B"), ("B", "C"), ("B", "D"), ("C", "D"), ("rules+OCR", "B"), ("B", "B_ocr_always")):
            P[f"{t}: {b} vs {a}"] = pair(g(a), g(b))
    out["scan_all_nontext"] = {n: cell([r for t in ("skan", "mieszany", "s2", "s5") for r in A.restrict(A.raw("E11", name), variants={t})]) for n, name in SCAN_RUNS.items()}
    Path(A.LLM_E2E / "E11" / "wyniki.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("TEKST")
    for n, v in out["text"].items():
        c = v["rep1"]
        print(f"  {n:18s}", c if "status" in c else f"{c['f1']:.3f} {c['ci95']} docs {c['docs']}")
    for t in SCAN_TYPES:
        print(t.upper())
        for n, c in out["scan"][t].items():
            print(f"  {n:14s}", c if "status" in c else f"{c['f1']:.3f} {c['ci95']} docs {c['docs']} {c['outcomes']}")


if __name__ == "__main__":
    main()
