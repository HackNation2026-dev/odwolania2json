"""Przebieg dokumentu: odczyt → diagnoza → router → ekstraktor → kotwiczenie → wynik, dowody, raport, stan.

Katalog roboczy zgodny z architekturą §7 (uproszczony do jednego `run_id`):
work/<batch_id>/documents/<document_id>/{input.pdf, runs/r1/{raw,t1,t3,...}, state.json}.
Błędy techniczne są jawne (kody §6), a nieudany etap nigdy nie podmienia wyniku starym lub zmyślonym.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import common
from common import HarnessError, write_json_atomic
from config import HarnessConfig
from reading import PdfiumReader, make_ocr, read_document
from result_model import prune, set_pointer, template
from stages import build

PDFIUM_LOCK = threading.RLock()  # PDFium nie jest bezpieczny wątkowo (współbieżność E15)
VERSION = "harness-0.1"


class LockedReader:
    """Opakowanie PdfReader serializujące wywołania PDFium."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.name = inner.name

    def __getattr__(self, item: str) -> Any:
        fn = getattr(self.inner, item)
        if not callable(fn):
            return fn

        def locked(*a: Any, **kw: Any) -> Any:
            with PDFIUM_LOCK:
                return fn(*a, **kw)
        return locked


class Modules:
    """Zestaw modułów zbudowany raz z konfiguracji (silnik OCR ładuje się leniwie i raz)."""

    def __init__(self, cfg: HarnessConfig, llm: Any = None) -> None:
        from llm import LlmClient

        self.cfg = cfg
        self.llm = llm if llm is not None else (LlmClient(cfg.llm) if "llm" in (cfg.router, cfg.extractor) else None)
        self.reader = LockedReader(PdfiumReader())
        self.ocr = make_ocr(cfg.ocr)
        self.router = build("router", cfg, self.llm)
        self.extractor = build("extractor", cfg, self.llm)
        self.anchor = build("anchor", cfg, self.llm)

    def versions(self) -> dict[str, Any]:
        import importlib.metadata as md
        import sys

        v: dict[str, Any] = {"harness": VERSION, "python": sys.version.split()[0], "pypdfium2": md.version("pypdfium2"),
                             "ocr": self.ocr.info(), "router": self.router.name, "extractor": self.extractor.name,
                             "anchor": self.anchor.name}
        if self.llm is not None:
            v["llm"] = {"protocol": self.cfg.llm.protocol, "endpoint": self.cfg.llm.base_url, "model": self.cfg.llm.model,
                        "temperature": self.cfg.llm.temperature}
        return v


def _normalize_value(pointer: str, value: Any) -> tuple[Any, bool]:
    """Normalizacja według ostatniego segmentu ścieżki; zwraca (wartość, czy_wymaga_sprawdzenia)."""
    from odwolania2json.domain import normalize as nz

    key = pointer.rsplit("/", 1)[-1]
    fn = {"nip": nz.normalize_nip, "regon": nz.normalize_regon, "krs": nz.normalize_krs, "pesel": nz.normalize_pesel,
          "na_rachunek": nz.normalize_account, "z_rachunku": nz.normalize_account, "kwota": nz.normalize_amount,
          "numer_ted": nz.normalize_ted}.get(key)
    if key in ("data", "data_operacji", "czynnosc_dzien"):
        fn = nz.normalize_date
    if fn is None or value is None:
        return value, False
    if isinstance(value, float) and key == "kwota":
        return value, False
    out = fn(str(value))
    return (out, False) if out is not None else (value, True)


def process_document(pdf_path: Path, doc_dir: Path, cfg: HarnessConfig, mods: Modules, document_id: str,
                     set_state: Any = lambda **kw: None) -> dict[str, Any]:
    """Przetwarza jeden dokument i zapisuje artefakty. Zwraca końcowy `DocumentState` (słownik)."""
    run = doc_dir / "runs" / "r1"
    t0 = time.monotonic()
    deadline = t0 + cfg.limits.document_timeout_s
    metrics: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    state: dict[str, Any] = {"progress": "done", "outcome": None, "stage": None, "class_id": None, "codes": [],
                             "result_file": None, "errors": errors}

    def finish(outcome: str, **kw: Any) -> dict[str, Any]:
        state.update(outcome=outcome, **kw)
        metrics["wall_s"] = round(time.monotonic() - t0, 4)
        write_json_atomic(run / "metrics.json", metrics | {"llm": mods.llm.stats.to_dict() if mods.llm else None})
        write_json_atomic(run / "state.json", state)
        return state

    def tech(e: HarnessError, stage: str) -> dict[str, Any]:
        e.stage = e.stage if e.stage != "?" else stage
        errors.append(e.to_dict())
        write_json_atomic(run / "report.json", {"schema_version": 1, "gaps": [], "processed_pages": [], "unprocessed_pages": [],
                                                "codes": [e.code]})
        return finish("technical_error", stage=e.stage, codes=[e.code])

    try:
        set_state(progress="running", stage="read")
        run.mkdir(parents=True, exist_ok=True)
        data = pdf_path.read_bytes()
        if not data.lstrip()[:1024].startswith(b"%PDF-") and b"%PDF-" not in data[:1024]:
            raise HarnessError("not_a_pdf", "plik nie zaczyna się od nagłówka PDF", stage="read")
        reading, diagnosis, rm = read_document(data, reader=mods.reader, ocr=mods.ocr, ocr_policy=cfg.ocr_policy,
                                               ocr_dpi=cfg.ocr_dpi, max_pages=cfg.limits.max_pages, deadline=deadline)
        metrics.update(rm)
        write_json_atomic(run / "raw" / "reading.json", reading)
        write_json_atomic(run / "raw" / "diagnosis.json", diagnosis)
        write_json_atomic(run / "diagnosis.json", diagnosis)
        write_json_atomic(run / "versions.json", mods.versions() | {"config": cfg.to_dict() | {"llm": _llm_public(cfg)}})
        unprocessed = sorted(set(rm.get("unprocessed_pages", [])))
        if time.monotonic() > deadline:
            raise HarnessError("time_limit", "przekroczono limit czasu dokumentu", stage="read")

        set_state(stage="route")
        t = time.monotonic()
        decision = mods.router.route(reading, diagnosis, document_id)
        metrics["route_s"] = round(time.monotonic() - t, 4)
        write_json_atomic(run / "t1" / "router.json", decision)
        if decision["decision"] == "technical_error":
            code = decision["codes"][0]
            return tech(HarnessError(code if code in common.ERROR_CODES else "internal_error", "router: brak wiarygodnego odczytu", stage="route"), "route")
        if decision["decision"] == "foreign":
            write_json_atomic(run / "result.json", {})
            write_json_atomic(run / "report.json", {"schema_version": 1, "gaps": [], "processed_pages": list(range(1, len(reading["pages"]) + 1)),
                                                    "unprocessed_pages": unprocessed, "codes": decision["codes"]})
            write_json_atomic(run / "evidence.json", [])
            return finish("foreign", stage="route", codes=decision["codes"], result_file="result.json")
        if decision["decision"] == "ambiguous":
            write_json_atomic(run / "report.json", {"schema_version": 1, "gaps": [], "processed_pages": [], "unprocessed_pages": unprocessed,
                                                    "codes": decision["codes"]})
            write_json_atomic(run / "evidence.json", [])
            return finish("ambiguous", stage="route", codes=decision["codes"])

        class_id = decision["class_id"]
        state["class_id"] = class_id
        set_state(stage="extract", class_id=class_id)
        t = time.monotonic()
        extraction = mods.extractor.extract(reading, class_id)
        metrics["extract_s"] = round(time.monotonic() - t, 4)
        if time.monotonic() > deadline:
            raise HarnessError("time_limit", "przekroczono limit czasu dokumentu", stage="extract")
        if extraction.ai_response is not None:
            write_json_atomic(run / "t3" / "ai-response.json", extraction.ai_response)

        set_state(stage="anchor")
        result = template(class_id)
        candidates, evidence, gaps = [], [], []
        review = False
        for i, f in enumerate(extraction.findings, 1):
            cid = f"c{i}"
            value, needs_check = _normalize_value(f.field, f.value)
            cand = {"id": cid, "field": f.field, "entity_id": None, "group_id": class_id, "raw_value": f.value, "method": f.method if f.method in ("regex", "ai", "rule") else "rule",
                    "presence": "present", "confidence": f.confidence, "conflict": False, "review_required": needs_check, "codes": [], "evidence_ids": []}
            anchored = {"status": "unanchored", "evidence": [], "candidates": 0}
            if f.quote:
                anchored = mods.anchor.resolve(reading, f.quote, f.page)
            if anchored["status"] == "anchored":
                for j, ev in enumerate(anchored["evidence"], 1):
                    eid = f"e{len(evidence) + 1}"
                    evidence.append({"id": eid, "document_sha256": reading["document_sha256"], "field": f.field, "entity_id": None,
                                     "group_id": class_id, **ev, "rule": None, "premise_ids": []})
                    cand["evidence_ids"].append(eid)
            else:
                cand["review_required"] = True
                cand["codes"].append("evidence_unanchored")
                cand["conflict"] = anchored["status"] == "ambiguous"
                gaps.append({"field": f.field, "review_required": True, "codes": ["evidence_unanchored"],
                             "reason": "conflicting" if anchored["status"] == "ambiguous" else "unprocessed",
                             "description": "Cytat bez jednoznacznej kotwicy bbox", "evidence_ids": [], "candidates": [cid]})
            review = review or cand["review_required"]
            candidates.append(cand)
            if not set_pointer(result, f.field, value):
                cand["review_required"] = True
                cand["codes"].append("result_validation_failed")
                review = True
        result = prune(result)
        for p in unprocessed:
            gaps.append({"field": "*", "review_required": False, "codes": ["ocr_unavailable"], "reason": "unprocessed",
                         "description": f"Strona {p} wymaga niedostępnego OCR", "evidence_ids": [], "candidates": []})
        n_pages = len(reading["pages"])
        report = {"schema_version": 1, "gaps": gaps, "processed_pages": [p for p in range(1, n_pages + 1) if p not in unprocessed],
                  "unprocessed_pages": unprocessed, "codes": sorted({c for g in gaps for c in g["codes"]})}
        write_json_atomic(run / "t3" / "candidates.json", candidates)
        write_json_atomic(run / "evidence.json", evidence)
        write_json_atomic(run / "report.json", report)
        write_json_atomic(run / "result.json", result)
        complete = extraction.notes == [] and not review and not unprocessed
        return finish("complete" if complete else "partial", stage="done", class_id=class_id, codes=report["codes"],
                      result_file="result.json")
    except HarnessError as e:
        return tech(e, state.get("stage") or "read")
    except OSError as e:
        return tech(HarnessError("write_failed", f"błąd zapisu: {type(e).__name__}", stage="write"), "write")
    except Exception as e:  # noqa: BLE001 — serwer ma przeżyć; błąd jawny, bez treści dokumentu
        return tech(HarnessError("internal_error", f"nieoczekiwany błąd: {type(e).__name__}", stage="internal"), "internal")


def _llm_public(cfg: HarnessConfig) -> dict[str, Any]:
    d = dict(cfg.llm.__dict__)
    d.pop("key_file", None)
    return d


