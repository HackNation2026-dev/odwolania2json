"""Dokumenty zbioru rozwojowego (147 PDF-ów) z tekstem i referencją, do testów reguł.

Zbiór kontrolny nie jest tu nigdy ładowany: lista spraw pochodzi z `data/podzial.json`
(`rozwojowy`). Tekst czyta czytnik produktu, w układzie jak w pomiarach E09/E19
(znaczniki `[[strona N]]`).
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from functools import cache

from odwolania2json.dataset import load_split
from odwolania2json.extract.pipeline import PageText, document_text
from odwolania2json.loader import (
    MATERIALS_DIR,
    DocumentClass,
    load_case_references,
    load_reference_json,
)
from odwolania2json.pdf.reader import PdfDocument

__all__ = ["DevDocument", "GapDocument", "dev_documents", "synthetic_gap_documents"]


@dataclass(frozen=True)
class DevDocument:
    case_id: str
    input_name: str
    document_class: DocumentClass
    text: str
    reference: dict[str, object]


@cache
def dev_documents() -> tuple[DevDocument, ...]:
    """Wszystkie dokumenty spraw rozwojowych (bez negatywów organizatora)."""
    rozwojowe = load_split().rozwojowy
    documents = []
    for ref in load_case_references():
        if ref.case_id not in rozwojowe:
            continue
        data = (MATERIALS_DIR / "dane" / ref.case_id / ref.input_name).read_bytes()
        with PdfDocument(data) as pdf:
            pages = [PageText(i + 1, pdf.read_page(i).text) for i in range(pdf.page_count)]
        documents.append(
            DevDocument(
                case_id=ref.case_id,
                input_name=ref.input_name,
                document_class=ref.document_class,
                text=document_text(pages),
                reference=load_reference_json(ref),
            )
        )
    return tuple(documents)


# --- luki SYNTETYCZNE (E20, `pola/gaps.py`): edycje tekstu prawdziwych dokumentów ---
# To nie są dokumenty z rozkładu organizatora, tylko deterministyczne edycje tekstu
# rozwojowych odwołań z referencją wyprowadzoną z oryginału (n = 8 na lukę).


def _gap_missing_representative(text: str, ref: dict[str, object]) -> tuple[str, str] | None:
    """g1: odwołanie bez pełnomocnika; zwraca (tekst, nazwisko usunięte z tekstu)."""
    if "reprezentowan" not in text:
        return None
    edited = re.sub(r"(?m)^reprezentowan\w* przez:.*\n", "", text)
    edited = re.sub(r"(?ms)^adres do korespondencji:.*?\n(?=tel\.)", "", edited)
    edited = re.sub(r"(?m)^tel\..*\n", "", edited)
    edited = re.sub(r",?\s*w oparciu o\s+załączone\s+pełnomocnictwo,?", ",", edited)
    edited = re.sub(
        r"na podstawie\s+pełnomocnictwa załączonego do niniejszego odwołania,?", "", edited
    )
    edited = re.sub(r"(?m)^[a-z]\) pełnomocnictwo udzielone.*\n", "", edited)
    edited = re.sub(r"(?m)^\.{5,}\n[^\n]*, (?:r\. ?pr\.|adw\.)\n?", "", edited)
    if (
        "reprezentowan" in edited
        or "adres do korespondencji" in edited
        or re.search(r", (?:r\. ?pr\.|adw\.)\s*$", edited, re.M)
    ):
        return None
    odwolujacy = ref["Odwolujacy"]
    assert isinstance(odwolujacy, list)
    first = odwolujacy[0]
    assert isinstance(first, dict)
    pelnomocnik = first["pelnomocnik"]
    assert isinstance(pelnomocnik, dict)
    name = pelnomocnik["imie_nazwisko"]
    assert isinstance(name, str)
    return edited, name


def _gap_reason_twelve(text: str) -> str | None:
    """g2: pierwsza czynność to projektowane postanowienia umowy (powód 12)."""
    sentence = re.search(r"Zamawiający w dniu \d{1,2} \w+ \d{4} (?:roku|r\.)\s+[^.]*\.", text)
    if not sentence or "polegających na" in text:
        return None
    return text.replace(
        sentence.group(0),
        re.sub(
            r"(roku|r\.)\s+.*$",
            r"\1 udostępnił projektowane postanowienia umowy w sprawie zamówienia.",
            sentence.group(0),
            flags=re.S,
        ),
    )


@dataclass(frozen=True)
class GapDocument:
    case_id: str
    text: str
    removed_name: str | None


def synthetic_gap_documents(limit: int = 8) -> dict[str, tuple[GapDocument, ...]]:
    """Osiem edycji na lukę (SYNTETYCZNE): `missing_representative` i `reason_twelve`."""
    appeals = [d for d in dev_documents() if d.document_class == "odwolanie"]
    missing: list[GapDocument] = []
    twelve: list[GapDocument] = []
    for doc in appeals:
        if len(missing) < limit:
            edit = _gap_missing_representative(doc.text, copy.deepcopy(doc.reference))
            if edit is not None:
                missing.append(GapDocument(doc.case_id, edit[0], edit[1]))
        if len(twelve) < limit:
            edited = _gap_reason_twelve(doc.text)
            if edited is not None:
                twelve.append(GapDocument(doc.case_id, edited, None))
    return {"missing_representative": tuple(missing), "reason_twelve": tuple(twelve)}
