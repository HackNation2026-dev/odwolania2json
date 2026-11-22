"""Eksperymentalny backend FastAPI (127.0.0.1, bez uwierzytelniania), trasy w kierunku OpenAPI v1.

Trasy: GET /health, GET /system, POST /batches, GET /batches/{id}, GET /documents/{id},
GET /documents/{id}/{result|evidence|report|diagnosis}.

To warstwa pomiarowa w `experiments/`, nie produkcja i nie kontrakt (docs/05…/plan §„Sposób
komunikacji”). Uruchomienie: `python server.py --port 8765 [--config wariant.json]`.
Błędy dokumentu nie wywracają procesu: każdy kończy się `done/technical_error` z kodem.
"""

from __future__ import annotations

import argparse
import os
import re
import secrets
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

import common  # noqa: F401 — ustawia sys.path
from common import HarnessError, read_json, write_json_atomic
from config import HarnessConfig, load_config
from pipeline import Modules, process_document
from stages import load_plugins

STARTED = time.time()


def _safe_name(name: str | None) -> str:
    base = Path((name or "plik.pdf").replace("\\", "/")).name
    return re.sub(r"[^\w.\- ]", "_", base)[:120] or "plik.pdf"


class Store:
    """Stan wsadów i dokumentów w pamięci + trwały `batch.json`/`state.json` w katalogu roboczym."""

    def __init__(self, cfg: HarnessConfig) -> None:
        self.cfg = cfg
        self.root = Path(cfg.work_dir)
        self.lock = threading.Lock()
        self.docs: dict[str, dict[str, Any]] = {}
        self.batches: dict[str, dict[str, Any]] = {}

    def doc_dir(self, doc: dict[str, Any]) -> Path:
        return self.root / doc["batch_id"] / "documents" / doc["document_id"]

    def update(self, document_id: str, **kw: Any) -> None:
        with self.lock:
            self.docs[document_id]["state"].update(kw)

    def public(self, doc: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            st = dict(doc["state"])
        return {"document_id": doc["document_id"], "batch_id": doc["batch_id"], "filename": doc["filename"],
                "sha256": doc["sha256"], **st}


def create_app(cfg: HarnessConfig | None = None, *, mods: Modules | None = None) -> FastAPI:
    cfg = cfg or load_config()
    load_plugins()
    modules = mods or Modules(cfg)
    store = Store(cfg)
    pool = ThreadPoolExecutor(max_workers=max(1, cfg.limits.max_workers), thread_name_prefix="doc")
    app = FastAPI(title="uzp-harness", version="0.1")
    app.state.store, app.state.mods, app.state.pool, app.state.cfg = store, modules, pool, cfg

    def run_doc(doc: dict[str, Any]) -> None:
        d = store.doc_dir(doc)
        if doc["state"].get("errors"):  # odrzucony już przy przyjęciu (np. upload_too_large)
            return
        final = process_document(d / "input.pdf", d, cfg, modules, doc["document_id"],
                                 set_state=lambda **kw: store.update(doc["document_id"], **kw))
        store.update(doc["document_id"], **final)

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "uptime_s": round(time.time() - STARTED, 1), "pid": os.getpid()}

    @app.get("/system")
    def system() -> dict[str, Any]:
        ocr = modules.ocr.info()
        llm = modules.llm.info() if modules.llm else None
        return {"harness_version": "0.1", "ocr": {"ready": bool(ocr["available"]), "provider": ocr},
                "llm": {"ready": bool(llm and llm["key_file_present"]), "provider": llm},
                "pdf_reader": modules.reader.name, "router": modules.router.name, "extractor": modules.extractor.name,
                "anchor": modules.anchor.name, "config": cfg.to_dict() | {"llm": {k: v for k, v in cfg.llm.__dict__.items() if k != "key_file"}},
                "limits": cfg.limits.__dict__, "python": sys.version.split()[0], "paid_call_performed": False}

    @app.post("/batches", status_code=201)
    async def create_batch(files: list[UploadFile] = File(...)) -> dict[str, Any]:  # noqa: B008
        if not files:
            raise HTTPException(422, {"code": "invalid_configuration", "description": "brak plików"})
        if len(files) > cfg.limits.max_batch_documents:
            raise HTTPException(413, {"code": "upload_too_large", "description": "za dużo dokumentów we wsadzie"})
        batch_id = "b" + secrets.token_hex(6)
        docs = []
        for i, f in enumerate(files, 1):
            document_id = f"{batch_id}-d{i:03d}"
            doc = {"document_id": document_id, "batch_id": batch_id, "filename": _safe_name(f.filename), "sha256": None,
                   "state": {"progress": "queued", "outcome": None, "stage": None, "class_id": None, "codes": [],
                             "result_file": None, "errors": []}}
            d = store.doc_dir(doc)
            d.mkdir(parents=True, exist_ok=True)
            size, over = 0, False
            h = __import__("hashlib").sha256()
            with (d / "input.pdf.part").open("wb") as out:
                while chunk := await f.read(1 << 20):
                    size += len(chunk)
                    if size > cfg.limits.max_upload_bytes:
                        over = True  # nadmiar odrzucamy, ale dalej czytamy strumień do końca (bez zapisu)
                        continue
                    h.update(chunk)
                    out.write(chunk)
            if over:
                (d / "input.pdf.part").unlink()
                doc["state"] = {"progress": "done", "outcome": "technical_error", "stage": "upload", "class_id": None,
                                "codes": ["upload_too_large"], "result_file": None,
                                "errors": [HarnessError("upload_too_large", f"plik przekracza limit {cfg.limits.max_upload_bytes} B", stage="upload").to_dict()]}
            else:
                os.replace(d / "input.pdf.part", d / "input.pdf")
                doc["sha256"] = h.hexdigest()
            store.docs[document_id] = doc
            docs.append(doc)
        store.batches[batch_id] = {"batch_id": batch_id, "document_ids": [d["document_id"] for d in docs], "created": time.time()}
        write_json_atomic(store.root / batch_id / "batch.json", {"batch_id": batch_id, "documents": [
            {"document_id": d["document_id"], "filename": d["filename"], "sha256": d["sha256"]} for d in docs]})
        for d in docs:
            if not d["state"]["errors"]:
                pool.submit(run_doc, d)
        return {"batch_id": batch_id, "document_id": docs[0]["document_id"], "document_ids": [d["document_id"] for d in docs],
                "documents": [store.public(d) for d in docs]}

    def _batch(batch_id: str) -> dict[str, Any]:
        b = store.batches.get(batch_id)
        if b is None:
            raise HTTPException(404, {"code": "not_found", "description": "nie ma takiego wsadu"})
        return b

    def _doc(document_id: str) -> dict[str, Any]:
        d = store.docs.get(document_id)
        if d is None:
            raise HTTPException(404, {"code": "not_found", "description": "nie ma takiego dokumentu"})
        return d

    @app.get("/batches/{batch_id}")
    def get_batch(batch_id: str) -> dict[str, Any]:
        b = _batch(batch_id)
        docs = [store.public(store.docs[i]) for i in b["document_ids"]]
        return {"batch_id": batch_id, "documents": docs, "done": all(d["progress"] == "done" for d in docs)}

    @app.get("/documents/{document_id}")
    def get_document(document_id: str) -> dict[str, Any]:
        return store.public(_doc(document_id))

    def _artifact(document_id: str, name: str, need_result: bool = False) -> JSONResponse:
        doc = _doc(document_id)
        st = store.public(doc)
        if st["progress"] != "done":
            raise HTTPException(409, {"code": "not_ready", "description": "dokument jeszcze się przetwarza", "progress": st["progress"]})
        path = store.doc_dir(doc) / "runs" / "r1" / name
        if need_result and st["outcome"] not in ("complete", "partial", "foreign"):
            raise HTTPException(409, {"code": "result_unavailable", "description": "eksport zablokowany dla tego wyniku",
                                      "outcome": st["outcome"], "codes": st["codes"], "errors": st["errors"]})
        if not path.is_file():
            raise HTTPException(404, {"code": "not_found", "description": f"brak artefaktu {name}"})
        return JSONResponse(read_json(path))

    @app.get("/documents/{document_id}/result")
    def result(document_id: str) -> JSONResponse:
        return _artifact(document_id, "result.json", need_result=True)

    @app.get("/documents/{document_id}/evidence")
    def evidence(document_id: str) -> JSONResponse:
        return _artifact(document_id, "evidence.json")

    @app.get("/documents/{document_id}/report")
    def report(document_id: str) -> JSONResponse:
        return _artifact(document_id, "report.json")

    @app.get("/documents/{document_id}/diagnosis")
    def diagnosis(document_id: str) -> JSONResponse:
        return _artifact(document_id, "diagnosis.json")

    @app.get("/documents/{document_id}/metrics")
    def metrics(document_id: str) -> JSONResponse:
        """Rozszerzenie harnessu: czasy etapów i liczniki (nie ma w OpenAPI)."""
        return _artifact(document_id, "metrics.json")

    @app.get("/documents/{document_id}/artifact/{name:path}")
    def raw_artifact(document_id: str, name: str) -> JSONResponse:
        """Rozszerzenie harnessu: dowolny artefakt JSON z katalogu przebiegu (np. raw/reading.json)."""
        doc = _doc(document_id)
        base = (store.doc_dir(doc) / "runs" / "r1").resolve()
        p = (base / name).resolve()
        if base not in p.parents or p.suffix != ".json" or not p.is_file():
            raise HTTPException(404, {"code": "not_found", "description": "brak artefaktu"})
        return JSONResponse(read_json(p))

    @app.exception_handler(HTTPException)
    async def _http_exc(_: Any, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "http_error", "description": str(exc.detail)}
        return JSONResponse(detail, status_code=exc.status_code)

    return app


def main(argv: list[str] | None = None) -> int:
    import uvicorn

    ap = argparse.ArgumentParser(description="Backend eksperymentalny (127.0.0.1, bez uwierzytelniania)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--config", default=None, help="plik JSON wariantu (HARNESS_* nadpisuje)")
    ns = ap.parse_args(argv)
    if ns.host != "127.0.0.1":
        print("odmowa: serwer bez uwierzytelniania słucha wyłącznie na 127.0.0.1", file=sys.stderr)
        return 2
    try:
        cfg = load_config(ns.config)
        app = create_app(cfg)
    except HarnessError as e:
        print(f"błąd konfiguracji: {e.code}: {e.description}", file=sys.stderr)
        return 2
    uvicorn.run(app, host=ns.host, port=ns.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
