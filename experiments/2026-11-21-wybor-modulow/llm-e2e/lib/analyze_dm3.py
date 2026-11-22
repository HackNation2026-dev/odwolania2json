"""E11/E18: M3 w wariancie D (DM3) vs D z modelem bazowym i vs A; replay zapisanych odpowiedzi, bez API. Wyjście: E11/wyniki-dm3.json."""
from __future__ import annotations
import json
from pathlib import Path
import analyze as A
import analyze_e11 as E

def main() -> None:
    out = {}
    dt = A.restrict(A.raw("E11", "e11-DM3-text"), max_rep=1)
    out["text_DM3"] = E.cell(dt)
    out["text_DM3_vs_A"] = E.pair(A.restrict(A.raw("E10", "e10-text-p2"), max_rep=1), dt)
    out["text_DM3_vs_Dbase"] = E.pair(A.restrict(A.raw("E10", "e10-textimg-p2"), max_rep=1), dt)
    ds = A.raw("E11", "e11-DM3-scan")
    for t in E.SCAN_TYPES:
        g = A.restrict(ds, variants={t})
        out[f"{t}_DM3"] = E.cell(g)
        out[f"{t}_DM3_vs_B"] = E.pair(A.restrict(A.raw("E11", "e11-scan-B"), variants={t}), g)
        out[f"{t}_DM3_vs_Dbase"] = E.pair(A.restrict(A.raw("E11", "e11-scan-D"), variants={t}), g)
    out["pending_transient_rows"] = {"DM3-text": A.transient_pending("E11", "e11-DM3-text"), "DM3-scan": A.transient_pending("E11", "e11-DM3-scan")}
    Path(A.LLM_E2E / "E11" / "wyniki-dm3.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in out.items():
        if isinstance(v, dict) and "f1" in v: print(k, round(v["f1"], 3), v["ci95"], "docs", v["docs"], "tech", v["technical_errors"], "tok", v["input_tokens_per_doc"], v["output_tokens_per_doc"])
        elif isinstance(v, dict) and "delta" in v: print(k, round(v["delta"], 3), v["ci95"], v["decision"], "docs", v["docs"])
        else: print(k, v if not isinstance(v, dict) or "status" in v else v)

if __name__ == "__main__":
    main()
