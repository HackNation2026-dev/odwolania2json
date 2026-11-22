"""Ocena przebiegów grupy C ewaluatorem produkcyjnym (po naprawie PR #8/#9) + bootstrap po sprawach (bootstrap.py).

Różnice względem `leaf_f1` uprzęży: (1) TP liczy ewaluator produkcyjny; błędna wartość to tylko FP (ADR-005),
(2) pięć pól tekstowych porównywanych progiem podobieństwa 80% (domyślna miara z `similarity.py`; rozrzut pokazuje `by_similarity`),
(3) listy dopasowane element do elementu (algorytm węgierski), (4) klasa dokumentu wchodzi osobno do `classification`.
Wynik NIE jest oficjalnym F1.

Polityka eksportu (domyślna = architektura §4.5/§9: `ambiguous`, `foreign`, `technical_error` ⇒ brak pliku ⇒ ocena jak `{}`):
parametr `policy` zmienia ocenę dokumentu bez ponownego wołania LLM (E17); patrz `apply_policy`.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXP = HERE.parent.parent
for p in (EXP / "harness",):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import data  # noqa: E402
from odwolania2json.bootstrap import bootstrap_f1, case_totals, paired_bootstrap_delta  # noqa: E402
from odwolania2json.evaluator import (  # noqa: E402
    DEFAULT_CONFIG,
    ClassTotals,
    DocumentMetrics,
    EvalConfig,
    compare_document,
)
from odwolania2json.loader import CaseReference  # noqa: E402
from odwolania2json.similarity import SIMILARITY_METHODS  # noqa: E402

ORG_CLASS = {"appeal": "odwolanie", "power_of_attorney": "pelnomocnictwo", "bank_transfer": "przelew"}
CLASSES = ("odwolanie", "pelnomocnictwo", "przelew", "obcy")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def reference_of(rec: dict[str, Any]) -> dict[str, Any]:
    if rec.get("ref"):
        return json.loads(Path(rec["ref"]).read_text(encoding="utf-8"))
    cls = rec["expected_class"]
    if cls in ("obcy", "szablon"):
        return {}
    item = next(i for i in data.load_items("all") if i.key == rec["key"])
    return data.reference_for(item)


_REF_CACHE: dict[str, dict[str, Any]] = {}


def cached_reference(rec: dict[str, Any]) -> dict[str, Any]:
    k = (rec.get("ref") or "") + "|" + rec["key"]
    if k not in _REF_CACHE:
        _REF_CACHE[k] = reference_of(rec)
    return _REF_CACHE[k]


def predicted_of(rec: dict[str, Any], policy: str = "default") -> tuple[dict[str, Any], str, bool]:
    """(JSON wyniku, klasa przewidziana, czy decyzja). Brak decyzji nie liczy się jako trafienie klasy."""
    outcome = rec.get("outcome")
    result = rec.get("result") or {}
    if outcome in ("complete", "partial") and rec.get("class_id") in ORG_CLASS:
        return result, ORG_CLASS[rec["class_id"]], True
    if outcome == "foreign":
        return {}, "obcy", True
    if policy == "best_class" and outcome == "ambiguous":
        cls = _best_class(rec)
        if cls:
            return result, cls, True
    return {}, "obcy" if rec["expected_class"] != "obcy" else "odwolanie", False


def _best_class(rec: dict[str, Any]) -> str | None:
    llm = (rec.get("router") or {}).get("llm_call") or {}
    for a in llm.get("attempts", []):
        raw = a.get("raw")
        if raw:
            m = re.search(r'"class"\s*:\s*"(\w+)"', raw)
            if m and m.group(1) in ORG_CLASS:
                return ORG_CLASS[m.group(1)]
    return None


def doc_metrics(rec: dict[str, Any], config: EvalConfig = DEFAULT_CONFIG, policy: str = "default") -> DocumentMetrics:
    pred, pcls, decided = predicted_of(rec, policy)
    ref = cached_reference(rec)
    outcomes = compare_document(pred, ref, config)
    return DocumentMetrics(case_id=rec["case_id"], input_name=rec["input_name"], document_class=rec["expected_class"],
                           outcomes=outcomes, classification="tp" if decided and pcls == rec["expected_class"] else "fn")


def totals_of(ms: list[DocumentMetrics]) -> ClassTotals:
    c: Counter[str] = Counter()
    for m in ms:
        c.update(o.verdict for o in m.outcomes)
    return ClassTotals(tp=c["tp"], tn=c["tn"], fp=c["fp"], fn=c["fn"])


def field_key(path: str) -> str:
    return re.sub(r"\[\d+\]", "[]", path)


def summarize_records(recs: list[dict[str, Any]], *, seed: int = 20261122, resamples: int = 2000, policy: str = "default",
                      config: EvalConfig = DEFAULT_CONFIG, by_field: bool = True) -> dict[str, Any]:
    """F1 z przedziałem (bootstrap po sprawach, powtórzenia sumowane w obrębie sprawy), podział na klasę i pole."""
    ms = [(r, doc_metrics(r, config, policy)) for r in recs]
    allm = [m for _, m in ms]
    tot = totals_of(allm)
    ct = case_totals(allm)
    iv = bootstrap_f1(ct, seed=seed, resamples=resamples) if ct else None
    per_class = {}
    for cls in CLASSES:
        sub = [m for _, m in ms if m.document_class == cls]
        if sub:
            t = totals_of(sub)
            sct = case_totals(sub)
            civ = bootstrap_f1(sct, seed=seed, resamples=resamples) if t.tp + t.fp + t.fn else None
            per_class[cls] = {"docs": len(sub), "tp": t.tp, "fp": t.fp, "fn": t.fn, "f1": round(t.f1, 4),
                              "ci": [round(civ.low, 4), round(civ.high, 4)] if civ else None}
    out: dict[str, Any] = {"docs": len(recs), "cases": len(ct), "tp": tot.tp, "fp": tot.fp, "fn": tot.fn, "tn": tot.tn, "f1": round(tot.f1, 4),
                           "ci95": [round(iv.low, 4), round(iv.high, 4)] if iv else None, "per_class": per_class,
                           "classification_acc": round(sum(m.classification == "tp" for m in allm) / max(1, len(allm)), 4),
                           "outcomes": dict(Counter(r.get("outcome") for r in recs)), "policy": policy}
    if by_field:
        fc: dict[str, Counter[str]] = defaultdict(Counter)
        for _, m in ms:
            for o in m.outcomes:
                fc[field_key(o.path)][o.verdict] += 1
        out["per_field"] = {k: {"tp": c["tp"], "fp": c["fp"], "fn": c["fn"], "f1": round(ClassTotals(tp=c["tp"], tn=0, fp=c["fp"], fn=c["fn"]).f1, 4)}
                            for k, c in sorted(fc.items())}
    return out


def by_similarity(recs: list[dict[str, Any]], policy: str = "default") -> dict[str, float]:
    """Rozrzut F1 przy wymiennych miarach podobieństwa (U-Q01)."""
    return {m: round(totals_of([doc_metrics(r, EvalConfig(similarity=m), policy) for r in recs]).f1, 4) for m in SIMILARITY_METHODS}


def case_totals_of(recs: list[dict[str, Any]], policy: str = "default") -> dict[str, ClassTotals]:
    return case_totals([doc_metrics(r, DEFAULT_CONFIG, policy) for r in recs])


def paired(base: list[dict[str, Any]], cand: list[dict[str, Any]], *, seed: int = 20261122, resamples: int = 2000,
           pol_a: str = "default", pol_b: str = "default") -> dict[str, Any]:
    """ΔF1 = cand − base na wspólnych sprawach (para: te same sprawy; powtórzenia sumowane)."""
    a, b = case_totals_of(base, pol_a), case_totals_of(cand, pol_b)
    keys = sorted(a.keys() & b.keys())
    d = paired_bootstrap_delta({k: a[k] for k in keys}, {k: b[k] for k in keys}, seed=seed, resamples=resamples)
    return {"delta": round(d.delta, 4), "ci95": [round(d.low, 4), round(d.high, 4)], "cases": d.cases,
            "decision": "cand>base" if d.low > 0 else "base>cand" if d.high < 0 else "nierozstrzygnięte"}


def per_rep(recs: list[dict[str, Any]], policy: str = "default") -> dict[int, float]:
    reps = sorted({r["rep"] for r in recs})
    return {k: round(totals_of([doc_metrics(r, DEFAULT_CONFIG, policy) for r in recs if r["rep"] == k]).f1, 4) for k in reps}


def llm_stats(recs: list[dict[str, Any]]) -> dict[str, Any]:
    """Tokeny, czas wywołań, odsetek odpowiedzi poza schematem (przy 1. próbie i po ponowieniu), rewizje modelu."""
    calls = [((r.get("router") or {}).get("llm_call")) for r in recs]
    calls = [c for c in calls if c]
    first_bad = sum(1 for c in calls if c.get("schema_first_ok") is False)
    final_bad = sum(1 for c in calls if c.get("schema_final_ok") is False)
    fail_docs = sum(1 for r in recs if not (r.get("router") or {}).get("llm_call"))
    toks_in = sum(a.get("input_tokens") or 0 for c in calls for a in c["attempts"])
    toks_out = sum(a.get("output_tokens") or 0 for c in calls for a in c["attempts"])
    lat = sorted(a["latency_s"] for c in calls for a in c["attempts"] if a.get("latency_s") is not None)
    models = Counter(a.get("model") for c in calls for a in c["attempts"] if a.get("model"))
    n = max(1, len(recs))
    walls = sorted(r["wall_s"] for r in recs if r.get("wall_s") is not None)
    q = lambda xs, p: round(xs[min(len(xs) - 1, int(p * len(xs)))], 2) if xs else None  # noqa: E731
    return {"docs": len(recs), "llm_calls_ok": len(calls), "docs_without_llm_record": fail_docs, "schema_first_bad": first_bad,
            "schema_first_bad_rate": round(first_bad / max(1, len(calls) + fail_docs), 4), "schema_final_bad": final_bad,
            "input_tokens_total": toks_in, "output_tokens_total": toks_out, "input_tokens_per_doc": round(toks_in / n),
            "output_tokens_per_doc": round(toks_out / n), "latency_median_s": q(lat, 0.5), "latency_p95_s": q(lat, 0.95),
            "doc_wall_median_s": q(walls, 0.5), "doc_wall_p95_s": q(walls, 0.95), "models_returned": dict(models),
            "technical_errors": dict(Counter(c for r in recs if r.get("outcome") == "technical_error" for c in r.get("codes") or [])),
            "evidence_unanchored_docs": sum(1 for r in recs if "evidence_unanchored" in (r.get("codes") or []))}


def stability(recs: list[dict[str, Any]]) -> dict[str, Any]:
    """Zgodność między powtórzeniami: odsetek dokumentów z identycznym JSON wyniku we wszystkich powtórzeniach i średnia zgodność liści."""
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in recs:
        by[r["key"] + "|" + (r.get("variant") or "")].append(r)
    ident = 0
    n = 0
    leaf_agree = []
    for rs in by.values():
        if len(rs) < 2:
            continue
        n += 1
        js = [json.dumps(r.get("result"), sort_keys=True, ensure_ascii=False) for r in rs]
        ident += len(set(js)) == 1
        leaves = [set(_leaves(r.get("result") or {})) for r in rs]
        union = set().union(*leaves)
        if union:
            inter = set.intersection(*leaves)
            leaf_agree.append(len(inter) / len(union))
    return {"docs_with_reps": n, "identical_json_rate": round(ident / n, 4) if n else None,
            "mean_leaf_agreement": round(sum(leaf_agree) / len(leaf_agree), 4) if leaf_agree else None}


def _leaves(x: Any, path: str = "") -> list[str]:
    if isinstance(x, dict):
        return [p for k, v in x.items() for p in _leaves(v, f"{path}.{k}")]
    if isinstance(x, list):
        return [p for i, v in enumerate(x) for p in _leaves(v, f"{path}.{i}")]
    return [] if x is None else [f"{path}={json.dumps(x, ensure_ascii=False)}"]


def leaf_f1_legacy(recs: list[dict[str, Any]]) -> float:
    """`leaf_f1` uprzęży (multizbiór niepustych liści, bez progu 80%) — do opisu różnic względem ewaluatora produkcyjnego."""
    sys.path.insert(0, str(EXP / "harness"))
    from run_experiment import leaf_counts, leaf_f1

    tot = {"tp": 0, "fp": 0, "fn": 0}
    for r in recs:
        c = leaf_counts(predicted_of(r)[0], cached_reference(r))
        for k in tot:
            tot[k] += c[k]
    return leaf_f1(tot)


def leak_check(paths: list[Path], needles: list[str]) -> list[str]:
    hits = []
    for p in paths:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for n in needles:
            if n and n in txt:
                hits.append(str(p))
    return hits
