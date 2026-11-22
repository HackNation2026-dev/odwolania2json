"""Ekstrakcja regułowa grupy B: pola o stałym formacie, podmioty i role, zaskarżona czynność, router.

Wzorce regex leżą w słownikach `PAT` (łańcuchy), żeby `mutate.py` mógł je mutować. To ekstraktor eksperymentalny,
strojony na zbiorze rozwojowym (dane syntetyczne, szablonowe): jego wynik jest górną granicą, nie prognozą na zbiór testowy.
"""

from __future__ import annotations

import re
from typing import Any

import lib  # noqa: F401  (ustawia sys.path na backend)
from odwolania2json.domain import normalize as nz

# ---------- wzorce (mutowane w mutate.py) ----------
OCRD = r"[0-9OoIlSB]"   # cyfra lub typowa pomyłka OCR (O/0, I/l/1, S/5, B/8) — używane tylko w tokenach po etykiecie
PAT: dict[str, str] = {
    "nip": r"NIP\s*[:.]?\s*((?:PL\s?)?" + OCRD + r"{3}[\- ]?" + OCRD + r"{3}[\- ]?" + OCRD + r"{2}[\- ]?" + OCRD + r"{2})(?![0-9A-Za-z])",
    "regon": r"REGON\s*[:.]?\s*(" + OCRD + r"{14}|" + OCRD + r"{9})(?![0-9A-Za-z])",
    "krs": r"KRS\s*[:.]?\s*(" + OCRD + r"{10})(?![0-9A-Za-z])",
    "pesel": r"PESEL\s*[:.]?\s*(" + OCRD + r"{11})(?![0-9A-Za-z])",
    "account": r"(?<![0-9A-Za-z])((?:PL\s?)?" + OCRD + r"{2}(?:\s?" + OCRD + r"{4}){6})(?![0-9A-Za-z])",
    "amount": r"(\d{1,3}(?:[  ]\d{3})*,\d{2}|\d+,\d{2}|\d+\.\d{2})(?:\s*(?:PLN|zł|zl))?",
    "bzp": r"((?:19|20)\d{2}\s?/\s?BZP\s?" + OCRD + r"{8}(?:/\d{2})?)",
    "ted_new": r"(?<![0-9])(\d{6}\s?-\s?(?:19|20)\d{2})(?![0-9])",
    "ted_old": r"((?:19|20)\d{2}\s?/\s?S\s?\d{1,3}\s?-\s?\d{6})",
    "date_num": r"(?<![0-9])(\d{1,2}[.\-]\d{1,2}[.\-](?:19|20)\d{2}|(?:19|20)\d{2}-\d{2}-\d{2})(?![0-9])",
    "date_word": r"(\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)\s+(?:19|20)\d{2})",
    "ref_label": r"(?i:nr\.?\s*ref\.?|numer\s+referencyjny|numer\s+transakcji(?:\s+operacji)?|id\s+transakcji|nr\s+transakcji|identyfikator\s+operacji|numer\s+operacji|nr\s+operacji)\s*[:.\s]*([A-Z0-9][A-Z0-9\-/]{5,})",
    "label_sender": r"(?i)(obci[ąa]ż\w*|nadawc\w*|zleceniodaw\w*|płatnik\w*|platnik\w*|z\s+rachunku)",
    "label_receiver": r"(?i)(odbiorc\w*|beneficjent\w*|uznawan\w*|adresat\w*|na\s+rachunek)",
    "label_amount": r"(?i)(kwota|wartość|wartosc)\b[^\n\d]{0,25}",
    "label_opdate": r"(?i)data\s+(?:operacji|transakcji|wykonania|realizacji|księgowania|waluty)",
    "narr_date": r"(?i)w\s+dniu\s+",
    "narr_amount": r"(?i)w\s+kwocie\s+",
}
_RX = {k: re.compile(v) for k, v in PAT.items()}
_STATE: dict[str, bool] = {"fix": True}


def rx(name: str, table: dict[str, re.Pattern[str]] | None = None) -> re.Pattern[str]:
    return (table or _RX)[name]


import contextlib  # noqa: E402


@contextlib.contextmanager
def patched(pat: dict[str, str] | None = None, fix: bool = True):
    """Podmienia tabelę wzorców i tryb poprawek OCR na czas bloku (eksperymenty E08, mutacje)."""
    global _RX
    old, oldfix = _RX, _STATE["fix"]
    _RX = compile_table(pat) if pat is not None else _RX
    _STATE["fix"] = fix
    try:
        yield
    finally:
        _RX, _STATE["fix"] = old, oldfix


def compile_table(pat: dict[str, str]) -> dict[str, re.Pattern[str]]:
    return {k: re.compile(v) for k, v in pat.items()}


_OCR_DIGIT = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "B": "8"})


def fix_digits(s: str) -> str:
    """Pomyłki OCR w tokenie cyfrowym: O→0, I/l→1, S→5, B→8 (stosować tylko do wartości po etykiecie lub o sztywnym formacie)."""
    return s.translate(_OCR_DIGIT)


def _flat(text: str) -> str:
    return re.sub(r"[ \t ]+", " ", text)


def _first(rxc: re.Pattern[str], text: str) -> str | None:
    m = rxc.search(text)
    return m.group(1) if m else None


def to_iso(raw: str | None) -> str | None:
    return nz.normalize_date(raw) if raw else None


def acct(raw: str | None, fix: bool) -> str | None:
    if not raw:
        return None
    raw = re.sub(r"^PL\s?", "", raw.strip())
    return nz.normalize_account(fix_digits(raw) if fix else raw)


# ---------- identyfikatory (role w E07) ----------

def ids_in(text: str, table: dict[str, re.Pattern[str]] | None = None, ocr_fix: bool | None = None) -> dict[str, list[str]]:
    """Wszystkie NIP/REGON/KRS/PESEL po etykietach (kolejność w tekście), znormalizowane."""
    if ocr_fix is None:
        ocr_fix = _STATE["fix"]
    out: dict[str, list[str]] = {"nip": [], "regon": [], "krs": [], "pesel": []}
    for kind, norm in (("nip", nz.normalize_nip), ("regon", nz.normalize_regon), ("krs", nz.normalize_krs), ("pesel", nz.normalize_pesel)):
        for m in rx(kind, table).finditer(text):
            raw = re.sub(r"^PL\s?", "", m.group(1))
            raw = fix_digits(raw) if ocr_fix else raw
            v = norm(re.sub(r"[\- ]", "", raw)) if kind != "regon" else norm(re.sub(r"[\- ]", "", raw))
            if v:
                out[kind].append(v)
    return out


# ---------- przelew (E08) ----------

def extract_transfer(text: str, table: dict[str, re.Pattern[str]] | None = None, ocr_fix: bool | None = None) -> dict[str, Any]:
    """Pola przelewu o stałym formacie: kwota, data operacji, rachunki, numer referencyjny. Etykieta rozstrzyga rolę rachunku."""
    if ocr_fix is None:
        ocr_fix = _STATE["fix"]
    t = text
    res: dict[str, Any] = {"kwota": None, "data_operacji": None, "na_rachunek": None, "z_rachunku": None, "numer_transakcji": None}
    # rachunki: rola z najbliższej etykiety w oknie 120 znaków przed numerem (łącznie z poprzednią linią)
    accts = []
    for m in rx("account", table).finditer(t):
        v = acct(m.group(1), ocr_fix)
        if not v:
            continue
        ctx = t[max(0, m.start() - 120):m.start()]
        s = [x.end() for x in rx("label_sender", table).finditer(ctx)]
        r = [x.end() for x in rx("label_receiver", table).finditer(ctx)]
        role = None
        if s or r:
            role = "z_rachunku" if (max(s) if s else -1) > (max(r) if r else -1) else "na_rachunek"
        accts.append((v, role))
    for v, role in accts:
        if role and res[role] is None:
            res[role] = v
    rest = [v for v, role in accts if role is None and v not in (res["na_rachunek"], res["z_rachunku"])]
    # bez etykiety: pierwszy to rachunek nadawcy, drugi odbiorcy (kolejność z dokumentu)
    for role in ("z_rachunku", "na_rachunek"):
        if res[role] is None and rest:
            res[role] = rest.pop(0)
    # kwota: po etykiecie, bez opłat; potem „w kwocie”; potem pierwsza kwota z walutą
    amt = None
    for m in rx("label_amount", table).finditer(t):
        head = t[max(0, m.start() - 12):m.start()].lower()
        if "opłat" in head or "prowiz" in head:
            continue
        mm = rx("amount", table).match(t, m.end()) or rx("amount", table).search(t[m.end():m.end() + 30])
        if mm:
            amt = mm.group(1)
            break
    if amt is None:
        for m in rx("narr_amount", table).finditer(t):
            mm = rx("amount", table).match(t, m.end())
            if mm:
                amt = mm.group(1)
                break
    if amt is None:
        for m in re.finditer(r"(\d[\d  ]*[,.]\d{2})\s*(?:PLN|zł|zl)", t):
            if "opłat" in t[max(0, m.start() - 25):m.start()].lower():
                continue
            amt = m.group(1)
            break
    res["kwota"] = nz.normalize_amount(amt) if amt else None
    # data operacji: po etykiecie operacji; „w dniu”; goła data (nie wydruk/miejscowość)
    d = None
    for m in rx("label_opdate", table).finditer(t):
        seg = t[m.end():m.end() + 45]
        mm = rx("date_word", table).search(seg) or rx("date_num", table).search(seg)
        if mm:
            d = mm.group(1)
            break
    if d is None:
        for m in rx("narr_date", table).finditer(t):
            seg = t[m.end():m.end() + 30]
            mm = re.match(r"(\d{1,2}[.\-]\d{1,2}[.\-]\d{4})", seg) or rx("date_word", table).match(seg)
            if mm:
                d = mm.group(1)
                break
    if d is None:
        for m in list(rx("date_word", table).finditer(t)) + list(rx("date_num", table).finditer(t)):
            pre = t[max(0, m.start() - 40):m.start()].lower()
            if any(w in pre for w in ("wydruk", "wygenerow", "sporządz", "godz")) or re.search(r"[A-ZŁŚŻ][a-ząęłńóśźż]+,\s*$", t[max(0, m.start() - 30):m.start()]):
                continue
            d = m.group(1)
            break
    res["data_operacji"] = to_iso(d)
    ref = _first(rx("ref_label", table), t)
    res["numer_transakcji"] = ref.strip() if ref else None
    return res


# ---------- odwołanie: pola stałe ----------

_SENT_DATE = r"(\d{1,2}\s+\w+\s+(?:19|20)\d{2}|\d{1,2}[.\-]\d{1,2}[.\-](?:19|20)\d{2})"
_PLACE = r"^\s*([A-ZŁŚŻŹĆ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\- ]{1,40}?)\s*,\s*(?:dnia\s+)?" + _SENT_DATE


def extract_appeal_fixed(text: str, table: dict[str, re.Pattern[str]] | None = None, ocr_fix: bool | None = None) -> dict[str, Any]:
    """BZP, TED, numer postępowania, data i miejscowość pisma."""
    if ocr_fix is None:
        ocr_fix = _STATE["fix"]
    flat_all = re.sub(r"\s+", " ", text)
    # numery BZP/TED dotyczą postępowania z bloku „dotyczy: … ODWOŁANIE/Działając”; wzmianki o wcześniejszym postępowaniu pomijamy
    dm = re.search(r"dotyczy\s*:?(.{0,900}?)(?:ODWOŁANIE|O D W O Ł A N I E|Działając|Prezes Krajowej)", flat_all)
    flat = dm.group(1) if dm else ""
    res: dict[str, Any] = {}
    b = _first(rx("bzp", table), flat)
    if b:
        b = re.sub(r"\s+", "", b)
        b = re.sub(r"^((?:19|20)\d{2})/BZP([0-9OoIlSB]{8})", lambda m: f"{m.group(1)}/BZP{fix_digits(m.group(2)) if ocr_fix else m.group(2)}", b)
    res["numer_bzp"] = b
    ted = None
    mo = _first(rx("ted_old", table), flat)
    mn = _first(rx("ted_new", table), flat)
    cands = []
    for rxn in ("ted_old", "ted_new"):
        m = rx(rxn, table).search(flat)
        if m:
            cands.append((m.start(), nz.normalize_ted(re.sub(r"\s+", "", m.group(1)).replace("/S", "/S ") if rxn == "ted_old" else re.sub(r"\s+", "", m.group(1)))))
    ted = min(cands)[1] if cands else None
    res["numer_ted"] = ted
    _ = (mo, mn)
    # numer postępowania: po „nr referencyjny sprawy:” / „numer postępowania:” / „nr referencyjny:”
    m = re.search(r"(?i)(?:nr|numer)\s+(?:referencyjny(?:\s+sprawy)?|postępowania|sprawy)\s*:?\s*([^\s,;]+)", flat_all)
    nr = m.group(1).rstrip(".,;") if m else None
    res["numer_postepowania"] = nr
    # data pisma i miejscowość: w pierwszych 40 liniach pierwszej strony (nagłówek)
    place = date = None
    first_page = text.split("[[strona 2]]")[0]
    for ln in first_page.splitlines()[:45]:
        mm = re.match(_PLACE, ln) or re.match(r"^\s*([A-ZŁŚŻŹĆ][A-Za-ząćęłńóśźż\-]{1,30})\s+(\d{1,2}\.\d{2}\.\d{4})\s*$", ln)
        if mm:
            place, date = mm.group(1), to_iso(mm.group(2))
            break
    res["miejscowosc"] = place
    res["data"] = date
    return res


# ---------- zaskarżona czynność (E09) ----------

POWOD = {1: "Decyzja o odrzuceniu oferty", 2: "Ogłoszenie wyboru oferty", 3: "Decyzja o wykluczeniu wykonawcy", 4: "Publikacja specyfikacji warunków zamówienia (SWZ)",
         5: "Modyfikacja treści SWZ", 6: "Odpowiedzi/wyjaśnienia do SWZ", 7: "Zaniechanie odrzucenia oferty", 8: "Zaniechanie wykluczenia wykonawcy",
         9: "Decyzja o unieważnieniu postępowania", 10: "Zaniechanie unieważnienia postępowania", 11: "Opis przedmiotu zamówienia (OPZ)",
         12: "Projektowane postanowienia umowy"}


def first_act_text(text: str) -> str:
    """Tekst pierwszego zarzutu/czynności. Pierwszeństwo ma pozycja 1) po „polegających na:” (organizator: czynność ustala się
    WYŁĄCZNIE z pierwszego zarzutu), a zdanie narracyjne „Zamawiający w dniu … ” jest zapasowe (bywa o innej czynności)."""
    flat = re.sub(r"\s+", " ", text)
    flat = re.sub(r"Strona \d+ z \d+", " ", flat)
    m = re.search(r"polegając\w+ na:\s*1\)\s*(.{10,500}?)(?=\s2\)|\sZarzut|\sUzasadnienie|\sZamawiający w dniu|$)", flat)
    if m:
        return m.group(1)
    m = re.search(r"Zamawiający w dniu [^.]{0,40}?\s(?:roku|r\.)\s+(.{5,300}?\.)\s", flat)
    return m.group(0) if m else ""


def classify_powod(act: str) -> int | None:
    a = act.lower()
    neg = bool(re.search(r"zaniechani|zaniechał|nie (?:odrzuci|wyklucz|unieważni)|brak (?:odrzuc|wykluczen|unieważn)", a))
    if re.search(r"unieważni", a):
        return 10 if neg else 9
    if re.search(r"wykluczeni|wyklucz", a):
        return 8 if neg else 3
    if re.search(r"odrzuceni|odrzuci", a):
        return 7 if neg else 1
    if re.search(r"wybór|wyborze|wybrał", a):
        return 2
    if re.search(r"zmodyfikował|modyfikacj", a):
        return 5
    if re.search(r"odpowied|wyjaśnie", a):
        return 6
    if re.search(r"projektowan\w+ postanowie|wzor\w+ umowy|postanowień umowy|postanowienia umowy", a):
        return 12
    if re.search(r"opis\w* przedmiotu|\bopz\b", a):
        return 11
    if re.search(r"specyfikacj|\bswz\b", a):
        return 4
    return None


def extract_act(text: str) -> dict[str, Any]:
    act = first_act_text(text)
    pid = classify_powod(act) if act else None
    dm = re.search(r"(\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)\s+(?:19|20)\d{2}|\d{1,2}[.\-]\d{1,2}[.\-](?:19|20)\d{2})", act)
    return {"czynnosc_powod_id": pid, "czynnosc_opis": POWOD.get(pid) if pid else None, "czynnosc_dzien": to_iso(dm.group(1)) if dm else None}


# ---------- odwołanie: podmioty i role (E07) ----------

_TITLES = r"(?:r\.\s?pr\.|adw\.|radca prawny|radczyni prawna|adwokat|adwokatka)"
_NAME = r"[A-ZŁŚŻŹĆ][a-ząćęłńóśźż]+(?:-[A-ZŁŚŻŹĆ][a-ząćęłńóśźż]+)?\s+[A-ZŁŚŻŹĆ][a-ząćęłńóśźż]+(?:-[A-ZŁŚŻŹĆ][a-ząćęłńóśźż]+)?"


def _block_ids(block: str) -> dict[str, str | None]:
    ids = ids_in(block)
    return {k: (v[0] if v else None) for k, v in ids.items()}


_STOP = re.compile(r"^(reprezentowan|adres do korespondencji|tel\.|\d\)\s|Zamawiając|Odwołując|dotyczy|ODWOŁANIE|O\s?D\s?W\s?O|Prezes Krajowej|Krajowa Izba)", re.I)


def _merge_headers(lines: list[str]) -> list[str]:
    """Nagłówek „Zamawiający (… art. 38 ust.” zawinięty na dwie linie scala się do jednej."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^(Zamawiając|\d\)\s*Zamawiając|Odwołując)", ln) and "(" in ln and not ln.rstrip().endswith(":") and i + 1 < len(lines):
            ln = ln + " " + lines[i + 1]
            i += 1
        out.append(ln)
        i += 1
    return out


def _entity(lines: list[str], pos: int) -> tuple[str | None, dict[str, str | None]]:
    name = lines[pos] if pos < len(lines) else None
    blk = []
    k = pos + 1
    while k < len(lines) and not _STOP.match(lines[k]) and k < pos + 6:
        blk.append(lines[k])
        k += 1
    return name, _block_ids("\n".join(blk))


def extract_parties(text: str) -> dict[str, Any]:
    """Odwołujący (lider konsorcjum), pełnomocnik i Zamawiający(-cy) z bloków nagłówka pierwszej strony."""
    first = text.split("[[strona 2]]")[0]
    lines = _merge_headers([ln.strip() for ln in first.splitlines() if ln.strip()])
    out: dict[str, Any] = {"Odwolujacy": [], "Zamawiajacy": []}
    idx = next((i for i, ln in enumerate(lines) if re.match(r"^Odwołując\w*\s*:", ln)), None)
    if idx is not None:
        rest = re.sub(r"^Odwołując\w*\s*:\s*", "", lines[idx])
        pos = idx + 1
        if re.search(r"konsorcjum", rest, re.I):
            pos = None
            for j in range(idx + 1, min(idx + 14, len(lines))):
                if re.match(r"^\d\)\s*Lider", lines[j]):
                    pos = j + 1
                    break
            if pos is None:
                pos = idx + 2
        name, ids = _entity(lines, pos)
        end = pos
        while end < len(lines) and not re.match(r"^(reprezentowan|dotyczy|ODWOŁANIE|O\s?D\s?W\s?O|Zamawiając)", lines[end], re.I) and end < pos + 16:
            end += 1
        tail = []
        k = end
        while k < len(lines) and not re.match(r"^(dotyczy|ODWOŁANIE|O\s?D\s?W\s?O|Zamawiając|Prezes Krajowej)", lines[k], re.I) and k < end + 6:
            tail.append(lines[k]); k += 1
        btxt = "\n".join(tail)
        rep = re.search(r"reprezentowan\w*\s+przez\s*:\s*(.+?)(?:\nadres do korespondencji|\ntel\.|$)", btxt, re.S)
        pel: dict[str, Any] = {"imie_nazwisko": None, "nazwa": None, "mail": None}
        przez = 0
        if rep:
            przez = 1
            names = re.findall(_TITLES + r"\s+(" + _NAME + ")", rep.group(1))
            pel["imie_nazwisko"] = names[0] if names else None
        corr = re.search(r"adres do korespondencji\s*:\s*(.+?)(?:\ntel\.|\n[Ee]-?mail|$)", btxt, re.S)
        if corr:
            c = re.sub(r"\s+", " ", corr.group(1))
            pel["nazwa"] = re.split(r",\s*(?:ul\.|al\.|pl\.|os\.|ulica)\s", c)[0].strip(" ,") or None
        mm = re.search(r"[\w.\-+]+@[\w\-]+(?:\.[\w\-]+)+", btxt[btxt.find("tel."):]) if "tel." in btxt else None
        pel["mail"] = mm.group(0) if mm else None
        out["Odwolujacy"].append({"krs": ids["krs"], "nazwa": name, "nip": ids["nip"], "regon": ids["regon"], "przez-pelnomocnika": przez, "pelnomocnik": pel})
    zh = next((i for i, ln in enumerate(lines) if re.match(r"^Zamawiając\w*\b.*:\s*$", ln) and not re.match(r"^\d\)", ln)), None)
    items: list[tuple[int, str]] = []
    if zh is not None:
        numbered = [i for i in range(zh + 1, min(zh + 30, len(lines))) if re.match(r"^\d\)\s*Zamawiając", lines[i])]
        items = [(i + 1, lines[i]) for i in numbered] if numbered else [(zh + 1, lines[zh])]
    for pos, hdr in items:
        name, ids = _entity(lines, pos)
        lead = (1 if re.search(r"lider|prowadząc", hdr, re.I) else 0) if len(items) > 1 else None
        out["Zamawiajacy"].append({"krs": ids["krs"], "nazwa": name, "nip": ids["nip"], "regon": ids["regon"], "prowadzacy_postepowanie": lead})
    flat = re.sub(r"\s+", " ", first)
    m = re.search(r"pn\.\s*[„\"“]([^”\"“]{5,300})[”\"“]", flat)
    out["tytul"] = m.group(1).strip() if m else None
    return out


# ---------- pełnomocnictwo (E07) ----------

_ROLE = r"(?:Prezes(?: Zarządu)?|Wiceprezes(?: Zarządu)?|Członek Zarządu|Dyrektor|Prokurent|Wspólnik|Komplementariusz|Burmistrz|Wójt|Kierownik)"


def extract_poa(text: str) -> dict[str, Any]:
    flat = re.sub(r"\s+", " ", text)
    flat = re.sub(r"\[\[strona \d+\]\]", " ", flat).strip()
    ids = ids_in(flat)
    nat = re.search(r"Ja,\s+niżej podpisan\w*(?:\(a\))?\s+(" + _NAME + r"),\s*prowadząc", flat)
    # mocodawca: „Mocodawcą jest NAME, ul.” | „NAME z siedzibą” | „w imieniu NAME (dalej”
    name = None
    for pat in (r"Mocodawc\w*\s*:?\s+(?:jest\s+)?([A-ZŁŚŻŹĆ][^,]{3,80}?)(?:,\s*(?:ul\.|al\.|pl\.)|\s+ul\.|\s+z siedzibą)", r"reprezentacji\s+(.+?)\s*\(", r"prowadzący działalność gospodarczą pod firmą\s+(.+?),\s*(?:ul\.|al\.)", r"Mocodawc\w*\s+jest\s+(.+?),\s*(?:ul\.|al\.|pl\.|os\.)", r"(?:Działając|działając) w imieniu\s+(.+?)\s*\(dalej", r"(?:^|\. |§ \d+\. Mocodawca )([A-ZŁŚŻŹĆ][^.]{3,80}?)\s+z siedzibą", r"Mocodawc\w*\s*:\s*(.+?),\s*(?:ul\.|al\.|pl\.)"):
        m = re.search(pat, flat)
        if m:
            name = m.group(1).strip()
            name = re.sub(r"^(?:PEŁNOMOCNICTWO(?: PROCESOWE)?|P E Ł N O M O C N I C T W O)\s+(?:[A-ZŁŚŻŹ][a-zą-ź]+,\s*\d.*?\d{4}\s+)?", "", name)
            name = re.sub(r"^[A-ZŁŚŻŹĆ][a-ząćęłńóśźż]+,\s*\d{1,2}[. ]\S+\s+\d{4}\s+", "", name)
            break
    name = re.sub(r"^Mocodawc\w*\s+(?:jest\s+)?", "", name) if name else name
    ls0 = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i0, ln in enumerate(ls0[:12]):
        if re.fullmatch(r"(?i)mocodawc\w*\s*:?", ln) and i0 + 1 < len(ls0):
            name = ls0[i0 + 1]
            break
    else:
        m0 = re.search(r"^(?:P\s?E\s?Ł\s?N\s?O\s?M\s?O\s?C\s?N\s?I\s?C\s?T\s?W\s?O(?:\s+PROCESOWE)?)\s+(.+?)\s+z siedzibą", flat) or re.match(r"(?:Pełnomocnictwo(?: procesowe)?)\s+(.+?)\s+z siedzibą", flat)
        if m0:
            name = m0.group(1).strip()
    members: list[dict[str, Any]] = []
    cm = re.search(r"\(Konsorcjum\)\s*:\s*(.+?)(?=\s(?:udziel|ustanaw|upoważ|niniejszym)|$)", flat)
    if cm:
        for part in re.split(r";\s*(?=\d\))", cm.group(1)):
            pm = re.match(r"\s*\d\)\s*(.+?),\s*(?:ul\.|al\.|pl\.)", part)
            pid = ids_in(part)
            members.append({"nazwa": pm.group(1).strip() if pm else None, "krs": pid["krs"][0] if pid["krs"] else None,
                            "nip": pid["nip"][0] if pid["nip"] else None})
        if members:
            name = members[0]["nazwa"]
    if name is None:
        m1 = re.match(r"(?:P\s?E\s?Ł\s?N\s?O\s?M\s?O\s?C\s?N\s?I\s?C\s?T\s?W\s?O|Pełnomocnictwo)(?:\s+PROCESOWE)?\s+(?:[A-ZŁŚŻŹ][a-ząćęłńóśźż]+,\s*\S+\s+\S+\s+\d{4}\s*r?\.?\s+)?(.+?),\s*(?:ul\.|al\.|pl\.)", flat)
        if m1:
            name = m1.group(1).strip()
    # pełnomocnicy: z tytułem przed nazwiskiem w zdaniu udzielenia; unikalni, w kolejności
    seen: list[str] = []
    for m in re.finditer(_TITLES + r"\s+(" + _NAME + r")", flat):
        n = m.group(1)
        if n not in seen:
            seen.append(n)
    # podpisujący: linia z imieniem i nazwiskiem tuż przed linią ze stanowiskiem
    sig: list[str] = []
    ls = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i in range(1, len(ls)):
        if re.fullmatch(_ROLE, ls[i]) and re.fullmatch(_NAME, ls[i - 1]) and ls[i - 1] not in sig:
            sig.append(ls[i - 1])
    typ = "osoba_fizyczna" if nat else "osoba_prawna"
    return {"imie_nazwisko": nat.group(1) if nat else None, "nazwa": name, "krs": ids["krs"][0] if ids["krs"] else None, "nip": ids["nip"][0] if ids["nip"] else None, "typ": typ,
            "pelnomocnicy": seen, "podpisujacy": sig, "pesele": ids["pesel"], "mocodawcy": members}


# ---------- router regułowy (E06): ulepszony względem harness.RulesRouter ----------

def despace(line: str) -> str:
    return re.sub(r"(?:(?<=\s)|^)(?:\S ){3,}\S(?=\s|$)", lambda m: m.group(0).replace(" ", ""), line)


def nfold(t: str) -> str:
    return nz.fold(t)


def router_signals(text_pages: list[str]) -> dict[str, Any]:
    """Sygnały dla routera: tytuł, adresat, etykiety pól, funkcje. Zwraca wyniki trzech klas i flagi przeciwne."""
    first = text_pages[0] if text_pages else ""
    lines = [nfold(despace(ln)) for ln in first.splitlines() if ln.strip()][:30]
    full = nfold(" ".join(text_pages))
    head = " ".join(lines)
    s = {"appeal": 0.0, "power_of_attorney": 0.0, "bank_transfer": 0.0}
    flags: list[str] = []
    title_odw = any(re.fullmatch(r"odwolanie\s*:?", ln.strip(" .:")) for ln in lines)
    if title_odw:
        s["appeal"] += 0.4
    if "prezes krajowej izby odwolawczej" in head:
        s["appeal"] += 0.3
    if re.search(r"odwolujac\w*\s*:", head):
        s["appeal"] += 0.2
    if re.search(r"wnosz\w* odwolanie|wnosim odwolanie|odwoluje sie|wnosze odwolanie|wnoszac odwolanie", full):
        s["appeal"] += 0.2
    if re.search(r"zarzut(?:y)? nr \d|zarzut\w* naruszeni", full):
        s["appeal"] += 0.1
    if any(ln.startswith(("wyrok", "postanowienie", "uchwala", "decyzja")) for ln in lines[:8]) and ("orzeka" in full or "w imieniu rzeczypospolitej" in full or "decyduje" in full):
        s["appeal"] -= 0.8
        flags.append("rozstrzygniecie")
    if re.search(r"(odpowiedz\w* na odwolanie|wnosze? o oddalenie odwolania|przystapienie do postepowania odwolawczego|sprzeciw)", head) and not title_odw:
        s["appeal"] -= 0.4
        flags.append("pismo_w_sprawie_odwolania")
    if any("pelnomocnictw" in ln and len(ln) < 40 for ln in lines[:8]):
        s["power_of_attorney"] += 0.5
    if re.search(r"udzielam|ustanawiam|umocowan|upowazniam|upowaznia", full):
        s["power_of_attorney"] += 0.3
    if "mocodaw" in full or "pelnomocnik" in full:
        s["power_of_attorney"] += 0.2
    if any("przelew" in ln and len(ln) < 80 for ln in lines[:8]) or "potwierdzenie" in head and "przelew" in head:
        s["bank_transfer"] += 0.4
    if "rachunek" in full:
        s["bank_transfer"] += 0.2
    if "kwota" in full or "wartosc" in full:
        s["bank_transfer"] += 0.2
    if re.search(r"(\d{2}\s?){1}(\d{4}\s?){6}", full):
        s["bank_transfer"] += 0.1
    if re.search(r"niezrealizowan|odrzucon\w* (?:przelew|polecenie)|zlecenie (?:odrzucone|anulowane)|wyciag z rachunku|saldo (?:poczatkowe|koncowe)|historia rachunku", full):
        s["bank_transfer"] -= 0.5
        flags.append("wyciag_lub_niezrealizowany")
    return {"scores": {k: round(max(0.0, min(1.0, v)), 3) for k, v in s.items()}, "flags": flags, "has_text": bool(full)}


def rules_route(text_pages: list[str], threshold: float = 0.7, margin: float = 0.2, foreign_below: float = 0.3) -> dict[str, Any]:
    sig = router_signals(text_pages)
    if not sig["has_text"]:
        return {"decision": "technical_error", "class": None, **sig}
    items = sorted(sig["scores"].items(), key=lambda kv: -kv[1])
    (c1, s1), (_, s2) = items[0], items[1]
    if s1 >= threshold and s1 - s2 >= margin:
        return {"decision": "classified", "class": c1, **sig}
    if s1 < foreign_below:
        return {"decision": "foreign", "class": None, **sig}
    return {"decision": "ambiguous", "class": None, **sig}
