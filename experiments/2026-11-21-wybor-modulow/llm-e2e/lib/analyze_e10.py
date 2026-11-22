"""E10: tabela wariantów LLM (wejście, prompt, effort), porównania sparowane z bazą, test długiego dokumentu.

Uruchomienie: .venv-exp/bin/python llm-e2e/lib/analyze_e10.py  → E10/wyniki.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import analyze as A
import score

BASE = "e10-text-p2"
VARIANTS = ["e10-text-p2", "e10-textimg-p2", "e10-image-p2", "e10-text-p1", "e10-text-p3", "e10-effort-low", "e10-effort-high"]


def compare(base: list[dict[str, Any]], cand: list[dict[str, Any]]) -> dict[str, Any]:
    keys = A.keyset(cand)
    reps = A.common_reps(base, cand)
    b = A.restrict(base, keys, reps)
    c = A.restrict(cand, keys, reps)
    return score.paired(b, c, seed=A.SEED) | {"reps_used": reps, "docs": len(keys)}


def main() -> None:
    base = A.raw("E10", BASE)
    out: dict[str, Any] = {"base": BASE, "variants": {}}
    for name in VARIANTS:
        recs = A.raw("E10", name)
        if not recs:
            out["variants"][name] = {"status": "brak wyniku"}
            continue
        s = A.summary_line(recs)
        entry = {"summary": s, "meta": {k: A.meta("E10", name).get(k) for k in ("total_wall_s", "peak_rss_mb", "limit_method", "segments", "versions")}}
        if name != BASE and base:
            entry["paired_vs_base"] = compare(base, recs)
        out["variants"][name] = entry
    # test długiego dokumentu: pierwsze 2 strony vs pełny tekst na długich odwołaniach
    long_recs = A.raw("E10", "e10-long-2pages")
    if long_recs and base:
        keys = A.keyset(long_recs)
        reps = A.common_reps(base, long_recs)
        full = A.restrict(base, keys, reps)
        trunc = A.restrict(long_recs, keys, reps)
        fs, ts = A.summary_line(full, 1000), A.summary_line(trunc, 1000)
        pf = {k: v["f1"] for k, v in fs["per_field"].items()}
        pt = {k: v["f1"] for k, v in ts["per_field"].items()}
        lost = {k: [pf[k], pt.get(k, 0.0)] for k in pf if pf[k] - pt.get(k, 0.0) >= 0.2}
        pages: list[int] = []
        for r in full:
            for _, pg in A.llm_field_pages(r).items():
                if pg:
                    pages.append(pg)
        late = sum(1 for p in pages if p >= 3)
        out["long_document"] = {"docs": len(keys), "reps": reps, "full": {"f1": fs["f1"], "ci95": fs["ci95"]}, "first_2_pages": {"f1": ts["f1"], "ci95": ts["ci95"]},
                                "paired": score.paired(full, trunc, seed=A.SEED), "fields_lost_ge_0.2_f1": lost,
                                "share_of_returned_fields_from_page_ge_3": round(late / max(1, len(pages)), 4), "returned_fields": len(pages)}
    Path(A.LLM_E2E / "E10" / "wyniki.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for n, v in out["variants"].items():
        if "summary" in v:
            s = v["summary"]
            print(f"{n:18s} F1 {A.fmt_ci(s)} docs {s['docs']} reps-sd {s['rep_f1_sd']} paired {v.get('paired_vs_base')}")


if __name__ == "__main__":
    main()
