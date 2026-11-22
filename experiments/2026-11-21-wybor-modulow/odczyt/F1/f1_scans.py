"""F1 pól na skanach z zestawu: przez HTTP (backend uprzęży: rapidocr + router regułowy + ekstraktor regułowy), ewaluator produkcyjny po naprawie (PR #8/#9).

Polecenie: python F1/f1_scans.py [--variants skan mieszany s2 s5] [--ocr-dpi 72]   (wynik: F1/f1-<ocr_dpi>.json)
`ocr_dpi` to parametr uprzęży (scale = ocr_dpi/72 względem MediaBox 1240×1754 pt skanów zestawu): 72 ≈ 150 dpi A4, 96 ≈ 200 dpi A4 (BLOKERY.md pkt 1).
Porównania: oryginał (warstwa tekstu, bez OCR) vs wariant skanu, na tych samych sprawach (podzbiór 12 spraw jak w E02). Przedział: bootstrap po sprawach (apps/…/bootstrap.py).
To nie jest oficjalne F1; ekstraktor regułowy jest wąską linią bazową (pokrywa tylko pola o stałym formacie), więc ważna jest RÓŻNICA oryginał → skan, nie poziom bezwzględny.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import lib  # noqa: E402
from api import load_zestaw  # noqa: E402

import common  # noqa: E402
import data  # noqa: E402
from client import HarnessClient, ManagedServer  # noqa: E402
from odwolania2json.bootstrap import bootstrap_f1, case_totals, paired_bootstrap_delta  # noqa: E402
from odwolania2json.evaluator import evaluate_document, summarize  # noqa: E402
from odwolania2json.loader import CaseReference  # noqa: E402

sys.path.insert(0, str(HERE.parent / "E02"))
from e02_quality import subset_cases  # noqa: E402
from stages import ORGANIZER_CLASS  # noqa: E402


def predicted(state: dict, expected: str) -> tuple[str, bool]:
    if state["outcome"] in ("complete", "partial"):
        return ORGANIZER_CLASS[state["class_id"]], True
    if state["outcome"] == "foreign":
        return "obcy", True
    return ("odwolanie" if expected == "obcy" else "obcy"), False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="*", default=["skan", "mieszany", "s2", "s5"])
    ap.add_argument("--ocr-dpi", type=int, default=72)
    ns = ap.parse_args()
    cases = set(subset_cases())
    ds = {(i.case_id, i.document_class): i for i in data.load_items("cases-dev")}
    jobs = [("oryginal", ds[(c, k)].source, ds[(c, k)]) for (c, k) in sorted(ds) if c in cases and k in ("odwolanie", "pelnomocnictwo", "przelew")]
    for it in load_zestaw(ns.variants):
        if it.case_id in cases:
            jobs.append((it.variant, it.pdf, ds[(it.case_id, it.document_class)]))
    work = HERE / "work" / f"dpi{ns.ocr_dpi}"
    work.mkdir(parents=True, exist_ok=True)
    cfg = {"pdf_reader": "pdfium", "ocr": "rapidocr", "ocr_dpi": ns.ocr_dpi, "ocr_policy": "if_needed", "router": "rules", "extractor": "rules",
           "work_dir": str(work / "srv"), "seed": 20261122, "name": f"A-F1-dpi{ns.ocr_dpi}", "limits": {"max_pages": 60, "document_timeout_s": 1500}}
    common.write_json_atomic(work / "server-config.json", cfg)
    metrics: dict[str, list] = {}
    recs = []
    if True:  # pomiar jakości: bez flock (czas niewiążący, maszyna obciążona; OMP_NUM_THREADS=2)
        t0 = time.time()
        with ManagedServer(work / "server-config.json", log_path=work / "server.log") as srv:
            with HarnessClient(srv.url, server=srv) as c:
                for variant, path, item in jobs:
                    run = c.run_document(path, timeout=1500)
                    st = run["state"]
                    res = run["artifacts"]["result"]["body"] if run["artifacts"]["result"]["http"] == 200 else None
                    pred, decided = predicted(st, item.document_class)
                    ref = data.reference_for(item)
                    case = CaseReference(case_id=item.case_id, input_name=item.input_name, document_class=item.document_class,
                                         reference_name=item.reference_name)
                    m = evaluate_document(case, res or {}, ref, pred)
                    if not decided:
                        m = m.model_copy(update={"classification": "fn"})
                    metrics.setdefault(variant, []).append(m)
                    recs.append({"variant": variant, "key": item.key, "outcome": st["outcome"], "codes": st["codes"], "wall_s": run["timing"]["wall_s"]})
                    print(f"{variant:9s} {item.key:45s} {st['outcome']:10s} {run['timing']['wall_s']:6.1f}s", flush=True)
            peak = srv.sample_rss()
        wall = time.time() - t0
    out: dict = {"experiment": "F1-skany", "ocr_dpi_param": ns.ocr_dpi, "cases": sorted(cases), "config": cfg, "wall_s": round(wall, 1),
                 "peak_rss_server_mb": round((peak or 0) / 1024, 1), "loadavg_end": os.getloadavg(), "variants": {}}
    base = case_totals(metrics["oryginal"])
    for v, ms in metrics.items():
        tot = case_totals(ms)
        bi = bootstrap_f1(tot, seed=20261122)
        row = {"documents": len(ms), "f1_fields": bi.model_dump(), "totals": summarize(ms)["totals"], "per_class": {k: x["f1"] if isinstance(x, dict) and "f1" in x else x for k, x in summarize(ms)["per_class"].items()},
               "classification": summarize(ms)["classification"],
               "outcomes": dict(Counter(r["outcome"] for r in recs if r["variant"] == v)),
               "wall_s_mean_per_doc": round(sum(r["wall_s"] for r in recs if r["variant"] == v) / len(ms), 2)}
        if v != "oryginal":
            row["delta_vs_original"] = paired_bootstrap_delta(base, tot, seed=20261122).model_dump()
        out["variants"][v] = row
    out["versions"] = lib.versions()
    lib.dump(HERE / f"f1-{ns.ocr_dpi}.json", out)
    lib.dump(HERE / f"f1-{ns.ocr_dpi}-dokumenty.json", recs)
    print(json.dumps({v: (r["f1_fields"]["f1"], r.get("delta_vs_original", {}).get("delta")) for v, r in out["variants"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
