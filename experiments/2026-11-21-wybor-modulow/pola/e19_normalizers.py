"""E19: normalizatory (apps/backend/odwolania2json/domain/normalize.py) kontra referencje; bez LLM i OCR.

Trzy części: (A) wartości referencyjne odnajdywane w tekście PDF i normalizowane z surowego zapisu; (B) test obiegowy formatów
(syntetyczne warianty zapisu wartości referencyjnych); (C) sumy kontrolne wartości referencyjnych (czy suma może być filtrem).
Uruchomienie: ../../../.venv-exp/bin/python e19_normalizers.py   → E19/wyniki.json
"""
from __future__ import annotations

import collections
import json
import re
from typing import Any

import lib
from odwolania2json.domain import normalize as nz

MONTHS = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]


def digits_rx(d: str) -> re.Pattern[str]:
    return re.compile(r"(?<!\d)" + r"\s?".join(re.escape(c) for c in d) + r"(?!\d)")


def all_dates(text: str) -> list[str]:
    rx = re.compile(r"\d{1,2}\s+(?:%s)\s+\d{4}|\d{1,2}[.\-]\d{1,2}[.\-]\d{4}|\d{4}-\d{2}-\d{2}" % "|".join(MONTHS))
    return [m.group(0) for m in rx.finditer(re.sub(r"[ \t]+", " ", text).replace("\n", " "))]


def all_amounts(text: str) -> list[str]:
    return [m.group(0) for m in re.finditer(r"\d{1,3}(?:[  ]\d{3})*[,.]\d{2}(?:\s*(?:PLN|zł))?|\d+[,.]\d{2}(?:\s*(?:PLN|zł))?", text)]


def part_a() -> dict[str, Any]:
    t = lib.read_text_cache()
    res: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    fails: dict[str, list] = collections.defaultdict(list)
    for it in lib.dev_items():
        if it.document_class == "obcy":
            continue
        ref = lib.reference_for(it)
        text = lib.plain_text(t[it.key])
        for path, v in lib.leaves(ref):
            g = lib.generic(path)
            if v is None:
                continue
            kind = None
            if g.endswith((".nip",)):
                kind, norm = "nip", nz.normalize_nip
            elif g.endswith(".regon"):
                kind, norm = "regon", nz.normalize_regon
            elif g.endswith(".krs"):
                kind, norm = "krs", nz.normalize_krs
            elif g.endswith((".na_rachunek", ".z_rachunku")):
                kind, norm = "account", nz.normalize_account
            elif g.endswith(".pesel"):
                kind, norm = "pesel", nz.normalize_pesel
            if kind:
                m = digits_rx(str(v)).search(text)
                if not m:
                    res[kind]["ref_not_found_in_text"] += 1
                    fails[kind].append((it.key, "not_found"))
                    continue
                s, e = m.span()
                raw = text[max(0, s - 3):e + 3] if kind == "account" else text[s:e]
                raw = re.sub(r"^.*?(?=PL\s?\d|\d)", "", raw, count=1, flags=re.S) if kind == "account" else raw
                got = norm(raw)
                res[kind]["match" if got == str(v) else "mismatch"] += 1
                if got != str(v):
                    fails[kind].append((it.key, raw, got))
            elif g.endswith(("data_operacji", "czynnosc_dzien", ".data")) and g != "mocodawca[].data":
                ds = [nz.normalize_date(x) for x in all_dates(text)]
                bad = sum(1 for x in ds if x is None)
                res["date"]["ref_in_normalized_set" if v in ds else "ref_missing_from_set"] += 1
                res["date"]["unparsed_date_strings"] += bad
                res["date"]["date_strings_total"] += len(ds)
                if v not in ds:
                    fails["date"].append((it.key, g, v, all_dates(text)[:6]))
            elif g.endswith("kwota"):
                am = [nz.normalize_amount(x) for x in all_amounts(text)]
                res["amount"]["ref_in_normalized_set" if float(v) in am else "ref_missing_from_set"] += 1
                if float(v) not in am:
                    fails["amount"].append((it.key, v, all_amounts(text)[:6]))
            elif g.endswith("numer_bzp"):
                found = re.search(r"((?:19|20)\d{2}\s?/\s?BZP\s?\d{8}(?:/\d{2})?)", re.sub(r"\s+", " ", text))
                got = re.sub(r"\s+", "", found.group(1)) if found else None
                res["bzp"]["match" if got == v else "mismatch"] += 1
                if got != v:
                    fails["bzp"].append((it.key, v, got))
            elif g.endswith("numer_ted"):
                got = nz.normalize_ted(text)
                res["ted"]["match" if got == v else "mismatch"] += 1
                if got != v:
                    fails["ted"].append((it.key, v, got))
            elif g.endswith(("nazwa",)) and "pelnomocnik" not in g:
                res["name_case"]["exact_substring" if str(v) in re.sub(r"\s+", " ", text) else ("ci_substring" if str(v).lower() in re.sub(r"\s+", " ", text).lower() else "absent_or_wrapped")] += 1
    return {"counts": {k: dict(c) for k, c in res.items()}, "failures_sample": {k: v[:8] for k, v in fails.items()}}


def part_b() -> dict[str, Any]:
    tests: list[tuple[str, str, Any, Any, str]] = []

    def add(kind, raw, expected, fn, note=""):
        tests.append((kind, raw, expected, fn(raw), note))
    for raw in ["9999284065", "999-928-40-65", "999 928 40 65", "NIP: 9999284065", "PL 9999284065", "NIP 999-92-84-065", "9999284065.", "99992840650"]:
        add("nip", raw, None if raw.endswith("50") and len(raw) == 11 else "9999284065", nz.normalize_nip, "11 cyfr nie jest NIP" if len(raw) == 11 else "")
    for raw in ["999642785", "999 642 785", "99964278500123", "REGON: 999642785", "9996427850012"]:
        add("regon", raw, {"9996427850012": None}.get(raw, "99964278500123" if raw.startswith("999642785001") and len(raw) == 14 else "999642785"), nz.normalize_regon)
    for raw in ["0009405188", "KRS 9999405188", "9999 405 188", "99994051881"]:
        add("krs", raw, None if len(raw.replace(" ", "")) == 11 else raw.replace(" ", "").replace("KRS", ""), nz.normalize_krs)
    acc = "68438223049992295262834736"
    grp = " ".join([acc[:2]] + [acc[i:i + 4] for i in range(2, 26, 4)])
    for raw, exp in [(acc, acc), ("PL" + acc, acc), ("PL " + grp, acc), (grp, acc), ("PL68-4382-2304-9992-2952-6283-4736", None), (acc[:25], None), (acc + "1", None)]:
        add("account", raw, exp, nz.normalize_account, "myślniki w rachunku" if "-" in raw else "")
    for raw, exp in [("10 000,00 zł", 10000.0), ("10000.00", 10000.0), ("10 000,00 PLN", 10000.0), ("200,00", 200.0), ("10 000,00 zł", 10000.0), ("1.000,50", 1000.5),
                     ("1 000,50", 1000.5), ("17 PLN", 17.0), ("kwota: 34,00 PLN", 34.0), ("−50,00", 50.0), ("10 000,00 zł słownie: dziesięć tysięcy", 10000.0), ("1,000.50", 1000.5)]:
        add("amount", raw, exp, nz.normalize_amount, "separator tysięcy z kropką/przecinkiem" if raw in ("1.000,50", "1,000.50") else "")
    for raw, exp in [("1 kwietnia 2026", "2026-04-01"), ("1 KWIETNIA 2026 r.", "2026-04-01"), ("01.04.2026", "2026-04-01"), ("01-04-2026", "2026-04-01"), ("2026-04-01", "2026-04-01"),
                     ("1.4.2026", "2026-04-01"), ("31 lutego 2026", None), ("01.04.26", "2026-04-01"), ("1 IV 2026", "2026-04-01"), ("29 lutego 2026", None), ("5 października 2026 roku", "2026-10-05"),
                     ("1 kwietnia 2026 14:36", "2026-04-01"), ("2026/04/01", "2026-04-01"), ("pierwszego kwietnia 2026", "2026-04-01")]:
        add("date", raw, exp, nz.normalize_date)
    for raw, exp in [("2026/S224-999211", "999211-2026"), ("2026/S 224-999211", "999211-2026"), ("999211-2026", "999211-2026"), ("2026/S 224 - 999211", "999211-2026"), ("TED: 999211-2026", "999211-2026")]:
        add("ted", raw, exp, nz.normalize_ted)
    pass_ = collections.Counter(); rows = []
    for kind, raw, exp, got, note in tests:
        ok = got == exp
        pass_[(kind, ok)] += 1
        rows.append({"kind": kind, "raw": raw, "expected": exp, "got": got, "ok": ok, "note": note})
    summary = {k: {"ok": pass_[(k, True)], "fail": pass_[(k, False)]} for k in sorted({r["kind"] for r in rows})}
    return {"summary": summary, "failures": [r for r in rows if not r["ok"]], "rows": rows}


def part_c() -> dict[str, Any]:
    c: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for it in lib.dev_items():
        if it.document_class == "obcy":
            continue
        for path, v in lib.leaves(lib.reference_for(it)):
            g = lib.generic(path)
            for suf, kind in ((".nip", "nip"), (".regon", "regon"), (".na_rachunek", "iban"), (".z_rachunku", "iban"), (".pesel", "pesel")):
                if g.endswith(suf) and v is not None:
                    c[kind]["valid" if nz.checksum_valid(kind, str(v)) else "invalid"] += 1
    return {k: dict(v) for k, v in c.items()}


def main() -> None:
    res = {"versions": lib.versions(), "n_dev_docs": len([i for i in lib.dev_items() if i.document_class != "obcy"]),
           "A_real_documents": part_a(), "B_roundtrip": part_b(), "C_checksums_of_references": part_c()}
    (lib.HERE / "E19" / "wyniki.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res["A_real_documents"]["counts"], ensure_ascii=False, indent=0))
    print(res["B_roundtrip"]["summary"])
    print(json.dumps(res["B_roundtrip"]["failures"], ensure_ascii=False))
    print(res["C_checksums_of_references"])


if __name__ == "__main__":
    main()
