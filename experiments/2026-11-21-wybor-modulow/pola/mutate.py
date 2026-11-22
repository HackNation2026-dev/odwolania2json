"""Mutacje wzorców regex (cyfry, etykiety, formaty, typy) jako miara odporności zbioru testowego.

Operatory (na łańcuchach PAT): zmiana kwantyfikatora {n}→{n-1},{n+1}; zmiana etykiety (litera); usunięcie `?` / `\\s?`; zmiana klasy cyfr
(`0-9`→`1-9`, `\\d`→`[0-8]`); zamiana separatora (`-`→`_`, `,`→`.`, `/`→`\\\\`); usunięcie look-aroundów.
Mutant zabity = którykolwiek licznik TP/FP/FN pól stałych na tekście PDF zbioru rozwojowego różni się od bazowego; drugi etap:
sondy syntetyczne (PROBES). Mutanty niekompilowalne są raportowane osobno (nie liczą się jako zabite ani przeżyłe).
"""
from __future__ import annotations

import re
from collections import Counter

import assemble
import lib
import rules

PROBES: list[tuple[str, str, str]] = [
    ("odwolanie", "Odwołujący:\nAlfa S.A.\nul. A 1\nKRS: 000001234567, NIP: 123456321812, REGON: 1234567851\nZamawiający:\nBeta S.A.\nNIP: 525 224 84 81, REGON 123456785\ndotyczy: nr referencyjny sprawy: ZP.2.2026, 2026 / BZP 00123456, 123456 - 2026\nODWOŁANIE\n", "Odwolujacy[0].nip=None|Odwolujacy[0].krs=None|Odwolujacy[0].regon=None|Zamawiajacy[0].nip=5252248481|ZamowieniePubliczne.numer_bzp=2026/BZP00123456|ZamowieniePubliczne.numer_ted=123456-2026"),
    ("odwolanie", "Odwołujący:\nAlfa S.A.\nKRS: 0000012345, NIP: 1234563218, REGON: 123456785\nZamawiający:\nBeta S.A.\nNIP: 5252248481\ndotyczy: nr referencyjny sprawy: ZP.3.2026, ogłoszenie nr 2026/BZP00123456, 2026/S100-123456\nODWOŁANIE\n", "ZamowieniePubliczne.numer_bzp=2026/BZP00123456|ZamowieniePubliczne.numer_ted=123456-2026"),
    ("odwolanie", "Gdańsk 05.05.2026\nOdwołujący:\nAlfa S.A.\nZamawiający:\nBeta S.A.\ndotyczy: ...\nODWOŁANIE\n", "OdwolanieKIO.data=2026-05-05"),
    ("pelnomocnictwo", "PEŁNOMOCNICTWO\nMocodawca Alfa S.A.\nul. A 1\nKRS 0000012345, NIP 1234563218, REGON 123456785\nPełnomocnik adw. Jan Nowak, PESEL 440514013591\n", "pelnomocnicy[0].pesel=None"),
    ("przelew", "Rachunek obciążany\nPL 61 1090 1014 0000 0712 1981 2874\nRachunek odbiorcy\n271140200400003002013553871\nKwota przelewu: 2 500,75 zł\nData transakcji 01-04-2026\nNr ref. XYZ-12345/6\n", "przelew_bankowy.z_rachunku=61109010140000071219812874|przelew_bankowy.na_rachunek=None|przelew_bankowy.kwota=2500.75|przelew_bankowy.data_operacji=2026-04-01|przelew_bankowy.numer_transakcji=XYZ-12345/6"),
    ("przelew", "Rachunek nadawcy 61109010140000071219812874\nRachunek beneficjenta PL27114020040000300201355387\nKwota 99.90 zł\nData wykonania 2026-04-02\nData wydruku 2026-04-09\n", "przelew_bankowy.kwota=99.9|przelew_bankowy.data_operacji=2026-04-02|przelew_bankowy.na_rachunek=27114020040000300201355387"),
    ("przelew", "Kwota 17 PLN\nWartość: 1\u00a0234,50 PLN\nDate wykonania: 2026-04-02\n", "przelew_bankowy.kwota=17.0"),
    ("przelew", "Płatnik Alfa\nPL61109010140000071219812874\nOdbiorca Beta\nPL27114020040000300201355387\nWartość 5,00\n", "przelew_bankowy.z_rachunku=61109010140000071219812874|przelew_bankowy.na_rachunek=27114020040000300201355387"),
    # (klasa dokumentu, tekst, pole wynik → oczekiwana wartość jako "ścieżka=wartość")
    ("odwolanie", "Odwołujący:\nAlfa sp. z o.o.\nul. A 1, 00-001 Warszawa\nKRS: 0000012345, NIP: 123-456-32-18, REGON: 123456785\nZamawiający:\nBeta S.A.\nul. B 2\nNIP: 5252248481\ndotyczy: postępowania nr referencyjny sprawy: ZP.1.2026, ogłoszenie nr 2026/BZP 00123456/01, TED: 2026/S 100-123456\nODWOŁANIE\n", "Odwolujacy[0].nip=1234563218|Odwolujacy[0].regon=123456785|ZamowieniePubliczne.numer_bzp=2026/BZP00123456/01|ZamowieniePubliczne.numer_ted=123456-2026"),
    ("odwolanie", "Odwołujący:\nAlfa S.A.\nul. A 1\nKRS: 0000012345, NIP: 1234563218, REGON: 12345678512347\nZamawiający:\nBeta S.A.\nul. B 2\nNIP: 5252248481\ndotyczy: nr postępowania: AB/12/2026, numer ogłoszenia TED: 654321-2026\nODWOŁANIE\n", "Odwolujacy[0].regon=12345678512347|ZamowieniePubliczne.numer_ted=654321-2026|ZamowieniePubliczne.numer_postepowania=AB/12/2026"),
    ("odwolanie", "Warszawa, dnia 5 maja 2026 roku\nOdwołujący:\nAlfa S.A.\nKRS: 0000012345\nZamawiający:\nBeta S.A.\ndotyczy: ...\nODWOŁANIE\n", "OdwolanieKIO.data=2026-05-05|OdwolanieKIO.miejscowosc=Warszawa"),
    ("pelnomocnictwo", "PEŁNOMOCNICTWO\nMocodawca Alfa S.A.\nul. A 1\nKRS 0000012345, NIP 123-456-32-18, REGON 123456785\nPełnomocnik adw. Jan Nowak, PESEL 44051401359\n", "mocodawca[0].data.nip=1234563218|mocodawca[0].data.krs=0000012345|pelnomocnicy[0].pesel=44051401359"),
    ("przelew", "POTWIERDZENIE PRZELEWU\nRachunek obciążany\nPL61 1090 1014 0000 0712 1981 2874\nRachunek odbiorcy\n27 1140 2004 0000 3002 0135 5387\nKwota operacji\n1 234,50 PLN\nData operacji\n5 maja 2026\nNr ref.\nCEN2605001234567\nOpłata 0,00 PLN\n", "przelew_bankowy.z_rachunku=61109010140000071219812874|przelew_bankowy.na_rachunek=27114020040000300201355387|przelew_bankowy.kwota=1234.5|przelew_bankowy.data_operacji=2026-05-05|przelew_bankowy.numer_transakcji=CEN2605001234567"),
    ("przelew", "Bank potwierdza, że w dniu 09-07-2026 z rachunku PL61109010140000071219812874 wykonano przelew krajowy w kwocie 200.00 PLN na rachunek nr 27 1140 2004 0000 3002 0135 5387.\nIdentyfikator operacji: ABC1234567890\nData wydruku: 10.07.2026\n", "przelew_bankowy.kwota=200.0|przelew_bankowy.data_operacji=2026-07-09|przelew_bankowy.numer_transakcji=ABC1234567890|przelew_bankowy.z_rachunku=61109010140000071219812874"),
    ("przelew", "Płatnik\nAlfa S.A.\nWARTOŚĆ ..... 50,00\nDATA OPERACJI .... 26 września 2026\nZ RACHUNKU\nPL611090101400000712198128 74\n", "przelew_bankowy.kwota=50.0|przelew_bankowy.data_operacji=2026-09-26"),
]


def _probe_vec(table: dict[str, str] | None) -> tuple:
    out = []
    with rules.patched(table, True):
        for cls, tx, exp in PROBES:
            try:
                pred = assemble.BY_CLASS[cls](tx)
            except Exception as e:  # noqa: BLE001
                out.append(("ERR", type(e).__name__))
                continue
            flat = dict((lib.generic(p).replace("[]", "[0]") if False else p, v) for p, v in lib.leaves(pred))
            for item in exp.split("|"):
                path, val = item.split("=", 1)
                got = flat.get(path)
                out.append((path, str(got) == val))
    return tuple(out)


def _dev_vec(texts: dict[str, str], keys: list[str], table: dict[str, str] | None) -> tuple:
    items = {i.key: i for i in lib.dev_items()}
    c: Counter = Counter()
    import e08_fixed_fields as e8
    with rules.patched(table, True):
        for k in keys:
            it = items[k]
            try:
                pred = assemble.BY_CLASS[it.document_class](texts[k])
            except Exception:  # noqa: BLE001
                c["ERR"] += 1
                continue
            for p, v in lib.outcomes(pred, lib.reference_for(it), select=e8.FIXED):
                c[(lib.generic(p), v)] += 1
    return tuple(sorted(c.items(), key=str))


def mutants(pat: dict[str, str]) -> list[tuple[str, str, str, str]]:
    """(id, nazwa wzorca, operator, zmutowany łańcuch)."""
    out = []
    for name, s in pat.items():
        seen = set()

        def add(op: str, new: str) -> None:
            if new != s and (op, new) not in seen:
                seen.add((op, new))
                out.append((f"{name}#{len(out)}", name, op, new))
        for m in re.finditer(r"\{(\d+)\}", s):
            n = int(m.group(1))
            for d in (-1, 1):
                add(f"quant {n}->{n + d}", s[:m.start()] + "{" + str(n + d) + "}" + s[m.end():])
        for m in re.finditer(r"[A-Z]{3,}", s):  # etykiety
            w = m.group(0)
            for i in (0, len(w) - 1):
                add(f"label {w}[{i}]", s[:m.start() + i] + ("X" if w[i] != "X" else "Y") + s[m.start() + i + 1:])
        for m in re.finditer(r"\\s\?|(?<![\\(])\?", s):
            add(f"drop '?' @{m.start()}", s[:m.start()] + s[m.end():])
        for m in re.finditer(r"\\d(?!\{)|0-9", s):
            add(f"digitclass @{m.start()}", s[:m.start()] + ("1-9" if m.group(0) == "0-9" else "[0-8]") + s[m.end():])
        for ch, rep in (("-", "_"), (",", "."), ("/", "|")):
            for m in re.finditer(re.escape(ch), s):
                if ch == "-" and s[max(0, m.start() - 1):m.start() + 2] and re.match(r"[0-9A-Za-z]-[0-9A-Za-z]", s[max(0, m.start() - 1):m.start() + 2]):
                    continue  # myślnik zakresu w klasie znaków
                add(f"sep {ch}->{rep} @{m.start()}", s[:m.start()] + rep + s[m.end():])
        for m in re.finditer(r"\(\?<?[!=]", s):
            e = s.find(")", m.start())
            add(f"drop lookaround @{m.start()}", s[:m.start()] + s[e + 1:])
    return out


def run(pdf_texts: dict[str, str], ocr_texts: dict[str, str], keys: list[str]) -> dict:
    base_dev = _dev_vec(pdf_texts, keys, None)
    base_ocr = _dev_vec(ocr_texts, [k for k in keys if k in ocr_texts], None)
    base_probe = _probe_vec(None)
    ms = mutants(rules.PAT)
    res = {"mutants_total": 0, "invalid_regex": 0, "killed_by_dev_pdf": 0, "killed_by_dev_or_ocr": 0, "killed_by_dev_or_probes": 0, "survived_all": 0, "by_pattern": {}, "survivors": []}
    for mid, name, op, new in ms:
        pat = dict(rules.PAT)
        pat[name] = new
        try:
            re.compile(new)
        except re.error:
            res["invalid_regex"] += 1
            continue
        res["mutants_total"] += 1
        kd = _dev_vec(pdf_texts, keys, pat) != base_dev
        ko = kd or _dev_vec(ocr_texts, [k for k in keys if k in ocr_texts], pat) != base_ocr
        kp = kd or _probe_vec(pat) != base_probe
        bp = res["by_pattern"].setdefault(name, {"total": 0, "killed_dev": 0, "killed_dev_or_probes": 0})
        bp["total"] += 1
        bp["killed_dev"] += kd
        bp["killed_dev_or_probes"] += kp
        res["killed_by_dev_pdf"] += kd
        res["killed_by_dev_or_ocr"] += ko
        res["killed_by_dev_or_probes"] += kp
        if not (kd or kp or ko):
            res["survived_all"] += 1
            res["survivors"].append({"pattern": name, "operator": op})
    for key in ("killed_by_dev_pdf", "killed_by_dev_or_ocr", "killed_by_dev_or_probes"):
        res[key + "_pct"] = round(100 * res[key] / max(1, res["mutants_total"]), 1)
    return res
