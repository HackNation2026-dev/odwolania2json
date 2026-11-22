"""E07 (podmioty i role), E09 (zaskarżona czynność), E20 (obecność pola i luki grupy C): reguły vs LLM vs hybryda.

Wejście: cache/extraction_llm_r0.json (run_extraction.py), teksty PDF zbioru rozwojowego, luki z gaps.py.
Warianty: rules (rules.py), llm (MiniMax przez HTTP, 1 wywołanie/dok.), hybrid_verify (wartości LLM; identyfikatory zachowane tylko gdy
ich cyfry występują w tekście, inaczej wartość regułowa; pola listowe/rola z LLM).
F1: ewaluator produkcyjny (próg 0,8 dla 5 pól tekstowych), bootstrap po sprawach, różnice sparowane.
Uruchomienie: ../../../.venv-exp/bin/python e07_e09_e20.py  → E07/wyniki.json, E09/wyniki.json, E20/wyniki.json
"""
from __future__ import annotations

import collections
import copy
import json
import re
from typing import Any

import assemble
import gaps
import lib
from odwolania2json.bootstrap import paired_bootstrap_delta
from result_model import prune, template

ENT = re.compile(r"^(Odwolujacy\[\]|Zamawiajacy\[\]|mocodawca\[\]|pelnomocnicy\[\])\.")
ENT_EXCL = re.compile(r"(czynnosc|numer_|tytul)")
ACT = re.compile(r"^OdwolanieKIO\.(czynnosc_powod_id|czynnosc_dzien|czynnosc_opis)$")
ID_KEYS = ("nip", "regon", "krs", "pesel")


def ensure_shape(cls: str, data: Any) -> dict:
    """Wynik LLM → słownik w kształcie szablonu (brak/zły typ = pusty szablon); nie poprawia wartości."""
    if not isinstance(data, dict):
        return prune(template(cls))
    return data


def digits(v: Any) -> str:
    return re.sub(r"\D", "", str(v)) if v is not None else ""


def hybrid_verify(llm: dict, rules_pred: dict, text: str) -> dict:
    """Identyfikatory z LLM tylko gdy cyfry występują w tekście (po usunięciu spacji); inaczej wartość regułowa tej samej ścieżki."""
    flat_digits = re.sub(r"\D", "", text)
    out = copy.deepcopy(llm)
    rl = dict(lib.leaves(rules_pred))
    for path, v in lib.leaves(llm):
        if path.split(".")[-1] in ID_KEYS and v is not None:
            if digits(v) and digits(v) in flat_digits:
                continue
            repl = rl.get(path)
            _set(out, path, repl)
    return out


def _set(d: Any, path: str, val: Any) -> None:
    toks = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    cur = d
    for i, t in enumerate(toks):
        last = i == len(toks) - 1
        key: Any = int(t[1:-1]) if t.startswith("[") else t
        if last:
            try:
                cur[key] = val
            except (KeyError, IndexError, TypeError):
                pass
            return
        try:
            cur = cur[key]
        except (KeyError, IndexError, TypeError):
            return


def collect() -> tuple[dict, dict, dict]:
    t = lib.read_text_cache()
    llm = json.loads((lib.CACHE / "extraction_llm_r0.json").read_text())
    docs: dict[str, dict] = {}
    for it in lib.dev_items():
        if it.document_class == "obcy":
            continue
        text = lib.doc_text(t[it.key])
        docs[it.key] = {"cls": it.document_class, "text": text, "ref": lib.reference_for(it), "case": it.case_id, "gap": None}
    for g in gaps.build():
        docs[g["key"]] = {"cls": g["class"], "text": "[[strona 1]]\n" + g["text"], "ref": g["ref"], "case": g["key"].split("/")[1], "gap": g["gap"]}
    preds: dict[str, dict[str, dict]] = {"rules": {}, "llm": {}, "hybrid_verify": {}}
    fails = collections.Counter()
    for k, d in docs.items():
        cls = lib.CLASS_OF[d["cls"]]
        rp = assemble.BY_CLASS[d["cls"]](d["text"])
        preds["rules"][k] = rp
        rec = llm.get(k)
        if not rec or not rec["ok"]:
            fails[(rec or {}).get("error", "missing")] += 1
            lp = prune(template(cls))
        else:
            lp = ensure_shape(cls, rec["data"])
        preds["llm"][k] = lp
        preds["hybrid_verify"][k] = hybrid_verify(lp, rp, d["text"])
    return docs, preds, {"llm_failures": dict(fails), "llm_records": len(llm)}


def evaluate(docs, preds, select, keys=None, seed=1):
    keys = keys or list(docs)
    res, per = {}, {}
    for v, pk in preds.items():
        per[v] = {k: lib.outcomes(pk[k], docs[k]["ref"], select=select) for k in keys}
        res[v] = {"overall": lib.f1_report(per[v], seed=seed), "per_field": lib.per_field(per[v])}
    base = lib.case_counts(per["rules"])
    res["paired_delta_vs_rules"] = {}
    for v in preds:
        if v == "rules":
            continue
        cc = lib.case_counts(per[v])
        if cc.keys() == base.keys():
            d = paired_bootstrap_delta(base, cc, seed=3, resamples=2000)
            res["paired_delta_vs_rules"][v] = {"delta": round(d.delta, 4), "ci95": [round(d.low, 4), round(d.high, 4)], "cases": d.cases}
    return res, per


def swaps(docs, preds, keys) -> dict:
    """NIP/KRS/REGON przypisany niewłaściwemu podmiotowi: wartość trafiona w referencji innej roli niż wskazana."""
    out = {}
    for v, pk in preds.items():
        c = collections.Counter()
        for k in keys:
            ref = docs[k]["ref"]
            if docs[k]["cls"] != "odwolanie":
                continue
            rl = {"Odwolujacy": [x for _, x in lib.leaves(ref["Odwolujacy"]) if x], "Zamawiajacy": [x for _, x in lib.leaves(ref["Zamawiajacy"]) if x]}
            for role, other in (("Odwolujacy", "Zamawiajacy"), ("Zamawiajacy", "Odwolujacy")):
                for ent in pk[k].get(role) or []:
                    for idk in ID_KEYS:
                        val = (ent or {}).get(idk) if isinstance(ent, dict) else None
                        if val is None:
                            continue
                        refv = [lib.leaves(e) for e in ref[role]]
                        own = {str(x) for ls in refv for _, x in ls if x}
                        if str(val) not in own and str(val) in {str(x) for x in rl[other]}:
                            c["wrong_role_id"] += 1
                        c["ids_emitted"] += 1
        out[v] = dict(c)
    return out


def main() -> None:
    docs, preds, meta = collect()
    dev_keys = [k for k, d in docs.items() if d["gap"] is None]
    res_all: dict[str, Any] = {"versions": lib.versions(), "llm_model": "MiniMax-M3.1-Flash (alias z odpowiedzi API)", "llm_runs_per_doc": 1, **meta, "docs_dev": len(dev_keys)}
    # E07
    sel7 = type("S", (), {})  # placeholder
    rx7 = re.compile(r"^(Odwolujacy\[\]|Zamawiajacy\[\]|mocodawca\[\]|pelnomocnicy\[\])\.")
    r7, per7 = evaluate(docs, preds, rx7, dev_keys)
    by_cls = {}
    for cls in ("odwolanie", "pelnomocnictwo"):
        ks = [k for k in dev_keys if docs[k]["cls"] == cls]
        by_cls[cls], _ = evaluate(docs, preds, rx7, ks)
    r7["by_class"] = {c: {v: x[v]["overall"] for v in preds} for c, x in by_cls.items()}
    r7["wrong_role_identifier"] = swaps(docs, preds, dev_keys)
    (lib.HERE / "E07" / "wyniki.json").write_text(json.dumps(res_all | {"E07": r7}, ensure_ascii=False, indent=1))
    # E09
    act2 = json.loads((lib.CACHE / "act_llm_v2.json").read_text())
    preds9 = dict(preds)
    preds9["llm_act_v2"] = {}
    for k, p in preds["llm"].items():
        q = copy.deepcopy(p)
        rec = act2.get(k)
        if rec and rec["ok"] and isinstance(rec["data"], dict) and "OdwolanieKIO" in q:
            for f in ("czynnosc_powod_id", "czynnosc_dzien", "czynnosc_opis"):
                q["OdwolanieKIO"][f] = rec["data"].get(f)
        preds9["llm_act_v2"][k] = q
    r9, per9 = evaluate(docs, preds9, ACT, dev_keys)
    acc = {}
    for v, pk in preds9.items():
        ok = sum(1 for k in dev_keys if docs[k]["cls"] == "odwolanie" and pk[k]["OdwolanieKIO"].get("czynnosc_powod_id") == docs[k]["ref"]["OdwolanieKIO"]["czynnosc_powod_id"])
        okd = sum(1 for k in dev_keys if docs[k]["cls"] == "odwolanie" and pk[k]["OdwolanieKIO"].get("czynnosc_dzien") == docs[k]["ref"]["OdwolanieKIO"]["czynnosc_dzien"])
        n = sum(1 for k in dev_keys if docs[k]["cls"] == "odwolanie")
        acc[v] = {"powod_id_correct": ok, "dzien_correct": okd, "n": n}
    r9["accuracy"] = acc
    g2 = [k for k in docs if docs[k]["gap"] == "g2_powod_12"]
    r9["powod_12_synthetic"] = {v: {"id12_correct": sum(1 for k in g2 if preds9[v][k]["OdwolanieKIO"].get("czynnosc_powod_id") == 12), "n": len(g2)} for v in preds9}
    r9["confusions_llm_v1"] = collections.Counter(f"{docs[k]['ref']['OdwolanieKIO']['czynnosc_powod_id']}->{preds['llm'][k]['OdwolanieKIO'].get('czynnosc_powod_id')}" for k in dev_keys if docs[k]["cls"] == "odwolanie" and preds["llm"][k]["OdwolanieKIO"].get("czynnosc_powod_id") != docs[k]["ref"]["OdwolanieKIO"]["czynnosc_powod_id"])
    r9["confusions_llm_v2"] = collections.Counter(f"{docs[k]['ref']['OdwolanieKIO']['czynnosc_powod_id']}->{preds9['llm_act_v2'][k]['OdwolanieKIO'].get('czynnosc_powod_id')}" for k in dev_keys if docs[k]["cls"] == "odwolanie" and preds9["llm_act_v2"][k]["OdwolanieKIO"].get("czynnosc_powod_id") != docs[k]["ref"]["OdwolanieKIO"]["czynnosc_powod_id"])
    (lib.HERE / "E09" / "wyniki.json").write_text(json.dumps(res_all | {"E09": r9}, ensure_ascii=False, indent=1))
    # E20: FP na polach z referencją null (dev) + luki
    fp_null = {}
    for v in preds:
        c = collections.Counter()
        byf = collections.defaultdict(collections.Counter)
        for k in dev_keys:
            for path, verdict in lib.outcomes(preds[v][k], docs[k]["ref"]):
                refv = dict(lib.leaves(docs[k]["ref"])).get(path)
                if refv is None:
                    c["ref_null_fields"] += 1
                    if verdict == "fp":
                        c["fp_on_null"] += 1
                        byf[lib.generic(path)]["fp"] += 1
                else:
                    c["ref_value_fields"] += 1
                    if verdict == "fn":
                        c["missed_value(fn)"] += 1
        fp_null[v] = {**dict(c), "fp_by_field": {p: dict(x) for p, x in byf.items()}}
    gap_res: dict[str, Any] = {}
    sel_gap = {"g1_brak_pelnomocnika": re.compile(r"^Odwolujacy\[\]\.(przez-pelnomocnika|pelnomocnik\.)"), "g2_powod_12": ACT,
               "g3_brak_bzp_ted": re.compile(r"numer_(bzp|ted)$"), "g4_wpis_15000": re.compile(r"przelew_bankowy\.kwota$")}
    for gname, sel in sel_gap.items():
        ks = [k for k in docs if docs[k]["gap"] == gname]
        r, _ = evaluate(docs, preds, sel, ks)
        gap_res[gname] = {"n_docs": len(ks), **{v: {x: r[v]["overall"][x] for x in ("tp", "tn", "fp", "fn", "f1")} for v in preds}}
    res20 = {"fp_on_null_reference_fields_dev": fp_null, "gaps_small_samples": gap_res}
    (lib.HERE / "E20" / "wyniki.json").write_text(json.dumps(res_all | {"E20": res20}, ensure_ascii=False, indent=1))
    for v in preds:
        print(v, "E07", r7[v]["overall"]["f1"], r7[v]["overall"]["ci95"], "E09", r9[v]["overall"]["f1"], acc[v], "E20 fp_on_null", fp_null[v].get("fp_on_null"))
    print(r7["wrong_role_identifier"], r7["paired_delta_vs_rules"], res20["gaps_small_samples"])


if __name__ == "__main__":
    main()
