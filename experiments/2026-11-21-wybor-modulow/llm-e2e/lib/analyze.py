"""Wspólne funkcje analizy grupy C: wczytanie przebiegu, ograniczenie do wspólnych dokumentów/powtórzeń, tabela wariantu."""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path
from typing import Any

import score

LLM_E2E = Path(__file__).resolve().parent.parent
SEED = 20261122


def raw(exp: str, name: str) -> list[dict[str, Any]]:
    p = LLM_E2E / exp / "raw" / f"{name}.jsonl"
    if not p.is_file():
        return []
    best: dict[tuple[int, str], dict[str, Any]] = {}
    for r in score.read_jsonl(p):  # duplikaty (równoległe procesy tego samego wariantu): zostaje pierwszy wiersz bez błędu przejściowego
        k = (r["rep"], dkey(r))
        if k not in best or (_transient(best[k]) and not _transient(r)):
            best[k] = r
    # wiersze z błędem przejściowym (sieć/429/timeout) nie są wynikiem wariantu: czekają na ponowienie, więc nie wchodzą do F1
    return [r for r in best.values() if not _transient(r)]


def _transient(r: dict[str, Any]) -> bool:
    return r.get("outcome") == "client_error" or (r.get("outcome") == "technical_error" and any(c in ("llm_unavailable", "llm_rate_limit") for c in r.get("codes") or []))


def transient_pending(exp: str, name: str) -> int:
    p = LLM_E2E / exp / "raw" / f"{name}.jsonl"
    return sum(1 for r in score.read_jsonl(p) if _transient(r)) if p.is_file() else 0


def meta(exp: str, name: str) -> dict[str, Any]:
    p = LLM_E2E / exp / "raw" / f"{name}.meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def dkey(r: dict[str, Any]) -> str:
    return r["key"] + "|" + (r.get("variant") or "")


def restrict(recs: list[dict[str, Any]], keys: set[str] | None = None, max_rep: int | None = None,
             classes: set[str] | None = None, variants: set[str] | None = None) -> list[dict[str, Any]]:
    return [r for r in recs if (keys is None or dkey(r) in keys) and (max_rep is None or r["rep"] <= max_rep)
            and (classes is None or r["expected_class"] in classes) and (variants is None or (r.get("variant") or "") in variants)]


def common_reps(*runs: list[dict[str, Any]]) -> int:
    return min(max((r["rep"] for r in run), default=0) for run in runs)


def keyset(recs: list[dict[str, Any]]) -> set[str]:
    return {dkey(r) for r in recs}


def summary_line(recs: list[dict[str, Any]], resamples: int = 2000) -> dict[str, Any]:
    s = score.summarize_records(recs, seed=SEED, resamples=resamples)
    pr = score.per_rep(recs)
    vals = list(pr.values())
    s["per_rep_f1"] = pr
    s["rep_f1_sd"] = round(statistics.pstdev(vals), 4) if len(vals) > 1 else None
    s["rep_f1_range"] = [min(vals), max(vals)] if vals else None
    s["by_similarity"] = score.by_similarity(recs)
    s["legacy_leaf_f1"] = score.leaf_f1_legacy(recs)
    s["stability"] = score.stability(recs)
    s["llm"] = score.llm_stats(recs)
    return s


def pointer_to_path(ptr: str) -> str:
    """'/Odwolujacy/0/nazwa' → 'Odwolujacy[0].nazwa' (zapis ścieżek ewaluatora)."""
    out = ""
    for part in ptr.strip("/").split("/"):
        if part.isdigit():
            out += f"[{part}]"
        else:
            out += ("." if out else "") + part
    return out


def llm_field_pages(rec: dict[str, Any]) -> dict[str, int | None]:
    """ścieżka ewaluatora → strona z odpowiedzi LLM (z surowej odpowiedzi ostatniej próby)."""
    call = (rec.get("router") or {}).get("llm_call") or {}
    for a in reversed(call.get("attempts", [])):
        raw_txt = a.get("raw")
        if not raw_txt:
            continue
        try:
            d = json.loads(raw_txt[raw_txt.find("{"): raw_txt.rfind("}") + 1])
        except ValueError:
            continue
        return {pointer_to_path(f["field"]): (f.get("page") if isinstance(f.get("page"), int) else None)
                for f in d.get("fields") or [] if isinstance(f, dict) and isinstance(f.get("field"), str)}
    return {}


def fmt_ci(s: dict[str, Any]) -> str:
    ci = s.get("ci95")
    return f"{s['f1']:.3f} [{ci[0]:.3f}; {ci[1]:.3f}]" if ci else f"{s['f1']:.3f}"


def clean_text(x: str) -> str:
    return re.sub(r"\s+", " ", x)
