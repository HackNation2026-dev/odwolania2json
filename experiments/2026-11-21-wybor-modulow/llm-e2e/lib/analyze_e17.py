"""E17: polityka null/eksportu a F1, liczona offline z zapisanych przebiegów (bez nowych wywołań LLM). Wyjście: E17/wyniki.json.

Polityki (każda to przeróbka JSON-a oceniany dokument po dokumencie, reszta bez zmian):
- `default`: tak jak uprząż (architektura §4.5/§9): pole niezakotwiczone zostaje z wartością, `partial` jest eksportowane, awaria LLM = brak pliku ({}).
- `unanchored_null`: pole, którego cytat nie ma jednoznacznej kotwicy bbox, dostaje null (usuwamy je z wyniku).
- `no_export_partial`: dokument `partial` (wymaga sprawdzenia) nie jest eksportowany (ocena jak {}).
- `rules_fallback`: przy awarii LLM (technical_error llm_*) eksportujemy wynik reguł (e11-rules-*) zamiast {}.
- `ambiguous`: ile dokumentów kończy `ambiguous` (router LLM i regułowy) oraz trafność najlepszej klasy routera regułowego.
"""

from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

import analyze as A
import score


def drop_pointer(result: dict[str, Any], pointer: str) -> None:
    parts = pointer.strip("/").split("/")
    cur: Any = result
    for p in parts[:-1]:
        try:
            cur = cur[int(p)] if isinstance(cur, list) else cur[p]
        except (KeyError, IndexError, ValueError, TypeError):
            return
    last = parts[-1]
    try:
        if isinstance(cur, list):
            cur[int(last)] = None
        else:
            cur.pop(last, None)
    except (IndexError, ValueError):
        return


def p_unanchored_null(rec: dict[str, Any]) -> dict[str, Any]:
    r = copy.deepcopy(rec)
    if r.get("result") and r.get("candidates"):
        for c in r["candidates"]:
            if "evidence_unanchored" in (c.get("codes") or []):
                drop_pointer(r["result"], c["field"])
    return r


def p_no_partial(rec: dict[str, Any]) -> dict[str, Any]:
    if rec.get("outcome") == "partial":
        r = copy.deepcopy(rec)
        r["result"], r["outcome"] = None, "ambiguous"
        return r
    return rec


def p_rules_fallback(rec: dict[str, Any], rules_by_key: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if rec.get("outcome") == "technical_error" and any(str(c).startswith("llm_") for c in rec.get("codes") or []):
        fb = rules_by_key.get(A.dkey(rec))
        if fb and fb.get("outcome") in ("complete", "partial"):
            r = copy.deepcopy(rec)
            r.update(result=fb["result"], class_id=fb["class_id"], outcome=fb["outcome"])
            return r
    return rec


def evaluate(name: str, base: list[dict[str, Any]], fn: Any) -> dict[str, Any]:
    cand = [fn(r) for r in base]
    s0 = score.summarize_records(base, seed=A.SEED, resamples=1000, by_field=False)
    s1 = score.summarize_records(cand, seed=A.SEED, resamples=1000, by_field=False)
    changed = sum(1 for a, b in zip(base, cand, strict=True) if (a.get("result"), a.get("outcome")) != (b.get("result"), b.get("outcome")))
    return {"policy": name, "docs": len(base), "docs_changed": changed, "default": {"f1": s0["f1"], "ci95": s0["ci95"], "tp": s0["tp"], "fp": s0["fp"], "fn": s0["fn"]},
            "variant": {"f1": s1["f1"], "ci95": s1["ci95"], "tp": s1["tp"], "fp": s1["fp"], "fn": s1["fn"]}, "paired": score.paired(base, cand, seed=A.SEED)}


def main() -> None:
    out: dict[str, Any] = {}
    text = A.raw("E10", "e10-text-p2")
    rules_text = {A.dkey(r): r for r in A.raw("E11", "e11-rules-text")}
    scan_b = A.raw("E11", "e11-scan-B")
    rules_scan = {A.dkey(r): r for r in A.raw("E11", "e11-rules-scan")}
    sets = {"tekst, wariant A (5 powtórzeń)": (text, rules_text), "skan+mieszany+S2+S5, wariant B (OCR+LLM)": (scan_b, rules_scan)}
    for label, (recs, rules) in sets.items():
        if not recs:
            continue
        out[label] = {"unanchored_null": evaluate("unanchored_null", recs, p_unanchored_null), "no_export_partial": evaluate("no_export_partial", recs, p_no_partial),
                      "rules_fallback": evaluate("rules_fallback", recs, lambda r, rl=rules: p_rules_fallback(r, rl)),
                      "outcome_counts": dict(Counter(r["outcome"] for r in recs))}
        # F1 niezakotwiczonych pól: ile zawartych w wyniku jest trafnych (koszt reguły „null bez kotwicy”)
        un = [r for r in recs if r.get("candidates") and any("evidence_unanchored" in (c.get("codes") or []) for c in r["candidates"])]
        out[label]["docs_with_unanchored_field"] = len(un)
    # ambiguous: router regułowy i LLM
    rt = A.raw("E11", "e11-rules-text")
    amb = [r for r in rt if r["outcome"] == "ambiguous"]
    good = 0
    for r in amb:
        cands = (r.get("router") or {}).get("candidates") or []
        if cands:
            top = max(cands, key=lambda c: c["score"])
            exp = {"odwolanie": "appeal", "pelnomocnictwo": "power_of_attorney", "przelew": "bank_transfer"}.get(r["expected_class"])
            good += top["class_id"] == exp
    out["ambiguous"] = {"llm_router_ambiguous_docs_text_p2": sum(1 for r in text if r["outcome"] == "ambiguous"), "llm_router_docs": len(text),
                        "rules_router_ambiguous_docs": len(amb), "of_which_expected_foreign": sum(1 for r in amb if r["expected_class"] == "obcy"),
                        "rules_top_class_correct_among_ambiguous_positives": good, "rules_ambiguous_positives": sum(1 for r in amb if r["expected_class"] != "obcy"),
                        "uwaga": "klasa i pola z jednego wywołania LLM: gdy LLM zwraca ambiguous, nie ma pól do wyeksportowania; polityka 'najlepsza klasa' wymagałaby wymuszonego wyboru w prompcie (nie testowana osobno)"}
    Path(A.LLM_E2E / "E17" / "wyniki.json").parent.mkdir(exist_ok=True)
    Path(A.LLM_E2E / "E17" / "wyniki.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: ({p: (v[p]["default"]["f1"], v[p]["variant"]["f1"], v[p]["paired"]["ci95"], v[p]["docs_changed"]) for p in ("unanchored_null", "no_export_partial", "rules_fallback")} if k != "ambiguous" else v) for k, v in out.items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
