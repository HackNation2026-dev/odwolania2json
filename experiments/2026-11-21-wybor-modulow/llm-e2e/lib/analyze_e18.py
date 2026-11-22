"""E18: wybór modelu LLM (ten sam prompt p2, wejście tekst, dane i sprawy), plus ustawienie effort. Wyjście: E18/wyniki.json.

Reguła z PREREJESTRACJA.md (pkt 6): model zastępuje bazę, gdy dolna granica 95% przedziału ΔF1 (model − baza) > −0,02 oraz tokeny wyjściowe
na dokument i mediana czasu wywołania nie są większe od bazy; w przeciwnym razie zostaje baza (MiniMax-M3.1-Flash-Preview).
"""
from __future__ import annotations

import json
from pathlib import Path

import analyze as A
import score

MODELS = {"M3": "e18-M3", "M2.7": "e18-M2.7", "M2.5": "e18-M2.5"}
EFFORT = {"effort-low": "e10-effort-low", "effort-high": "e10-effort-high"}


def row(recs, base):
    s = A.summary_line(recs, 1000)
    keys, reps = A.keyset(recs), A.common_reps(base, recs)
    b, c = A.restrict(base, keys, reps), A.restrict(recs, keys, reps)
    p = score.paired(b, c, seed=A.SEED)
    bl, cl = score.llm_stats(b), s["llm"]
    rule = (p["ci95"][0] > -0.02 and cl["output_tokens_per_doc"] <= bl["output_tokens_per_doc"] and (cl["latency_median_s"] or 1e9) <= (bl["latency_median_s"] or 0))
    return {"docs": s["docs"], "docs_planned_note": "patrz README", "reps_used": reps, "f1": s["f1"], "ci95": s["ci95"], "per_class": {k: v["f1"] for k, v in s["per_class"].items()},
            "by_similarity": s["by_similarity"], "rep_f1": s["per_rep_f1"], "stability": s["stability"], "paired_vs_base": p, "base_same_docs": {"f1": score.summarize_records(b, resamples=1000, by_field=False)["f1"]},
            "tokens_in_per_doc": cl["input_tokens_per_doc"], "tokens_out_per_doc": cl["output_tokens_per_doc"], "base_tokens_out_per_doc": bl["output_tokens_per_doc"],
            "latency_median_s_UNDER_LOAD": cl["latency_median_s"], "base_latency_median_s_UNDER_LOAD": bl["latency_median_s"], "schema_first_bad_rate": cl["schema_first_bad_rate"],
            "models_returned": cl["models_returned"], "technical_errors": cl["technical_errors"], "rule_replaces_base": rule}


def main():
    base_all = A.raw("E10", "e10-text-p2")
    out = {"base": "MiniMax-M3.1-Flash-Preview (e10-text-p2)", "models": {}, "effort": {}}
    base_pos = A.restrict(base_all, classes={"odwolanie", "pelnomocnictwo", "przelew"})
    for tag, name in MODELS.items():
        r = A.raw("E18", name)
        out["models"][tag] = row(r, base_pos) if r else {"status": "brak"}
    base_scr = A.restrict(base_all, keys=A.keyset(A.raw("E10", "e10-text-p1")) | A.keyset(A.raw("E10", "e10-text-p3")))
    for tag, name in EFFORT.items():
        r = A.raw("E10", name)
        out["effort"][tag] = row(r, base_scr) if r else {"status": "brak"}
    Path(A.LLM_E2E / "E18" / "wyniki.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for g in ("models", "effort"):
        for k, v in out[g].items():
            print(g, k, v if "status" in v else (v["f1"], v["ci95"], v["paired_vs_base"], v["tokens_out_per_doc"], v["base_tokens_out_per_doc"], v["latency_median_s_UNDER_LOAD"], v["rule_replaces_base"]))


if __name__ == "__main__":
    main()
