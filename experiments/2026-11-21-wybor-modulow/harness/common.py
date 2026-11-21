"""Wspólne drobiazgi harnessu: ścieżki, zapis atomowy, kody błędów technicznych, skróty.

Dlaczego osobny moduł: serwer, klient i CLI eksperymentów muszą zgadzać się co do
kodów błędów (architektura §6) i sposobu zapisu plików (§7), a nie wolno im
importować się nawzajem w kółko.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

HARNESS_DIR = Path(__file__).resolve().parent
EXP_DIR = HARNESS_DIR.parent
REPO = EXP_DIR.parents[1]
BACKEND_DIR = REPO / "apps" / "backend"
MATERIALS = REPO / "docs" / "02-materialy" / "organizator-uzp"
WORK_ROOT = HARNESS_DIR / "work"
RESULTS_ROOT = EXP_DIR / "wyniki"

if str(BACKEND_DIR) not in sys.path:  # backend produkcyjny: tylko import loader/dataset/normalize
    sys.path.insert(0, str(BACKEND_DIR))

# Kody wykonawcze z architektury §6 (proponowane mapowanie na angielskie kody API).
ERROR_CODES = frozenset(
    {
        "ocr_unavailable", "ocr_error", "pdf_corrupted", "pdf_encrypted", "llm_unavailable",
        "llm_authorization", "llm_rate_limit", "llm_invalid_response", "invalid_configuration",
        "time_limit", "context_limit", "write_failed", "result_validation_failed",
        "class_ambiguous", "scan", "mixed_page", "mixed_document", "low_quality",
        "invalid_ocr_layer", "clipped_text", "foreign_document", "information_not_explicit",
        "data_after_page_3", "class_lookalike", "multiple_documents", "evidence_unanchored",
        # kody wejścia/limitów uploadu (nie są w katalogu; jawnie oznaczone jako rozszerzenie harnessu)
        "upload_too_large", "page_limit", "not_a_pdf", "empty_document", "internal_error",
    }
)


class HarnessError(Exception):
    """Jawny błąd techniczny z kodem; nigdy nie niesie klucza ani treści dokumentu."""

    def __init__(self, code: str, description: str, *, stage: str = "?", retryable: bool = False,
                 page: int | None = None) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"nieznany kod błędu: {code}")
        super().__init__(f"{code}: {description}")
        self.code = code
        self.description = description
        self.stage = stage
        self.retryable = retryable
        self.page = page

    def to_dict(self, attempt: int = 1) -> dict[str, Any]:
        return {"stage": self.stage, "code": self.code, "description": self.description,
                "retryable": self.retryable, "attempt": attempt, "page": self.page}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_bytes_atomic(path: Path, data: bytes) -> None:
    """Plik tymczasowy w tym samym katalogu, fsync, os.replace (architektura §7)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(OSError):
            Path(tmp).unlink()


def write_json_atomic(path: Path, payload: Any) -> None:
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    write_bytes_atomic(path, data)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def redact(text: str, secrets: list[str]) -> str:
    """Usuwa sekrety z tekstu przed zapisem w błędzie lub logu."""
    for s in secrets:
        if s:
            text = text.replace(s, "***")
    return text
