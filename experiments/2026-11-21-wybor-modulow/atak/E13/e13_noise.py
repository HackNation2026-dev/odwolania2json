"""E13 (uzupełnienie): szum bazowy modelu — N czystych przebiegów tego samego dokumentu, żeby odróżnić zmianę od wstrzyknięcia od zwykłej wariancji MiniMax.
Uruchomienie: .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E13/e13_noise.py [N]
Wynik: atak/E13/wyniki-szum.json (prawdziwy LLM, mała próbka)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e13 import *  # noqa: F401,F403,E402
from data import reference_for  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
out = {"runs_per_doc": n, "docs": {}}
with running("e13noise", WORK / "noise", router="rules", extractor="llm", llm={"retries": 4, "timeout_s": 120}, limits={"max_workers": 1}) as (srv, c):
    for cls, idx in (("pelnomocnictwo", 0), ("przelew", 1)):
        item = dev_item(cls, idx)
        ref = reference_for(item)
        recs = [run_real_doc(c, item.source.read_bytes(), f"clean{i}.pdf") for i in range(n)]
        flats = [flat_leaves(r["result"]) if r.get("result") else None for r in recs]
        keys = sorted({k for f in flats if f for k in f})
        flips = {}
        for k in keys:
            vals = [json.dumps(f.get(k), ensure_ascii=False) for f in flats if f]
            if len(set(vals)) > 1:
                flips[k] = {"distinct_values": len(set(vals)), "null_in_runs": sum(1 for f in flats if f and f.get(k) is None), "runs": len([f for f in flats if f])}
        out["docs"][item.key] = {"outcomes": [(r["outcome"], r.get("codes")) for r in recs], "f1": [eval_counts(r["result"], ref)["f1"] for r in recs if r.get("result")], "unstable_fields": flips}
(ATAK / "E13" / "wyniki-szum.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False)[:1500])
