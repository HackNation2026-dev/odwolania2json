"""E08: pola o stałym formacie (regex) na tekście PDF, tekście OCR (rapidocr 150 dpi) i tekście z szumem OCR; mutacje wzorców.

Miara: F1 ewaluatorem produkcyjnym (TP/FP/FN) na polach o stałym formacie, po sprawach (bootstrap 95%). Warianty ekstraktora:
 strict   = tylko cyfry (bez poprawek O/0, l/1);  tolerant = tokeny z O/I/l/S/B + poprawka po etykiecie.
Szum syntetyczny: podmiana znaków w cyfrach (0→O, 1→l, 5→S, 8→B) i gubienie/wstawianie spacji, p=1%/2%/4% na znak cyfrowy, ziarno stałe.
Mutacje: mutate.py; zabity = zmiana liczników na PDF (dev) albo na sondach syntetycznych.
Uruchomienie: ../../../.venv-exp/bin/python e08_fixed_fields.py [--no-mutation]  → E08/wyniki.json
"""
from __future__ import annotations

import json
import random
import re
import sys
import time

import assemble
import lib
import mutate
import rules

FIXED = re.compile(r"(\.krs|\.nip|\.regon|\.pesel|numer_bzp|numer_ted|numer_postepowania|kwota|data_operacji|na_rachunek|z_rachunku|numer_transakcji|OdwolanieKIO\.data|czynnosc_dzien)$")
STRICT = {k: v.replace(rules.OCRD, r"\d") for k, v in rules.PAT.items()}
CONF = {"o": "0", "O": "0", "0": "O", "1": "l", "l": "1", "5": "S", "8": "B"}


def noise(text: str, p: float, seed: int) -> str:
    """Szum OCR na znakach cyfrowych (podmiana na mylący znak) i spacjach (usunięcie)."""
    rng = random.Random(seed)
    out = []
    for ch in text:
        r = rng.random()
        if ch in "0158" and r < p:
            out.append({"0": "O", "1": "l", "5": "S", "8": "B"}[ch])
        elif ch == " " and r < p / 2:
            continue
        else:
            out.append(ch)
    return "".join(out)


def run_source(texts: dict[str, str], pat: dict[str, str] | None, fix: bool) -> dict[str, list]:
    items = {i.key: i for i in lib.dev_items()}
    per: dict[str, list] = {}
    with rules.patched(pat, fix):
        for k, tx in texts.items():
            it = items[k]
            ref = lib.reference_for(it)
            pred = assemble.BY_CLASS[it.document_class](tx)
            per[k] = lib.outcomes(pred, ref, select=FIXED)
    return per


def main() -> None:
    t0 = time.time()
    pdf = lib.read_text_cache()
    ocr = json.loads((lib.CACHE / "texts_ocr150.json").read_text())
    keys = [k for k, v in pdf.items() if v["class"] != "obcy"]
    src = {"pdf": {k: lib.doc_text(pdf[k]) for k in keys}, "ocr150": {k: lib.doc_text(ocr[k]) for k in keys if k in ocr}}
    for p in (0.01, 0.02, 0.04):
        src[f"pdf_noise_{int(p * 100)}pct"] = {k: noise(lib.doc_text(pdf[k]), p, 20261122 + n) for n, k in enumerate(keys)}
    res: dict = {"versions": lib.versions(), "ocr": "rapidocr==3.10.0 150 dpi + jak_skan(szum=4), zestaw własny grupy B", "sources": {}, "docs": len(keys)}
    base: dict[str, dict] = {}
    for sname, texts in src.items():
        res["sources"][sname] = {}
        for vname, (pat, fix) in {"strict": (STRICT, False), "tolerant": (None, True)}.items():
            per = run_source(texts, pat, fix)
            base[(sname, vname)] = per  # type: ignore[index]
            res["sources"][sname][vname] = {"overall": lib.f1_report(per), "per_field": lib.per_field(per)}
    # sparowana różnica tolerant − strict na każdym źródle
    from odwolania2json.bootstrap import paired_bootstrap_delta
    res["paired_delta_tolerant_minus_strict"] = {}
    for sname in src:
        d = paired_bootstrap_delta(lib.case_counts(base[(sname, "strict")]), lib.case_counts(base[(sname, "tolerant")]), seed=7, resamples=2000)  # type: ignore[index]
        res["paired_delta_tolerant_minus_strict"][sname] = {"delta": round(d.delta, 4), "ci95": [round(d.low, 4), round(d.high, 4)], "cases": d.cases}
    pdf_t = res["sources"]["pdf"]["tolerant"]["overall"]["f1"]
    res["regression_vs_pdf_tolerant"] = {s: round(res["sources"][s]["tolerant"]["overall"]["f1"] - pdf_t, 4) for s in src}
    if "--no-mutation" not in sys.argv:
        res["mutation"] = mutate.run(src["pdf"], src["ocr150"], keys)
    res["wall_s"] = round(time.time() - t0, 1)
    (lib.HERE / "E08" / "wyniki.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for sname, v in res["sources"].items():
        print(sname, {k: (x["overall"]["f1"], x["overall"]["ci95"], x["overall"]["fp"], x["overall"]["fn"]) for k, x in v.items()})
    if "mutation" in res:
        print({k: v for k, v in res["mutation"].items() if k != "survivors" and k != "mutants"})


if __name__ == "__main__":
    main()
