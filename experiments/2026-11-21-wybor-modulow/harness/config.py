"""Konfiguracja wariantu modułów: plik JSON i/lub zmienne środowiskowe.

Eksperyment zmienia wariant bez zmiany kodu: `HARNESS_CONFIG=wariant.json` albo
pojedyncze `HARNESS_<POLE>=...`. Zmienne mają pierwszeństwo przed plikiem
(jak w architekturze §9.1). Klucza API tu nie ma: LLM czyta go z pliku w chwili wywołania.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from common import HarnessError, WORK_ROOT


@dataclass
class LlmSettings:
    protocol: str = "anthropic"          # anthropic | openai | mock
    base_url: str = "https://api.minimax.io/anthropic/v1/messages"
    model: str = "MiniMax-M3.1-Flash-Preview"
    key_file: str | None = None          # None => MINIMAX_KEY_FILE albo ~/kluczMiniMaxKacper
    temperature: float = 0.0
    max_tokens: int = 8000
    timeout_s: float = 120.0
    retries: int = 2
    effort: str | None = None            # tylko MiniMax (output_config.effort)


@dataclass
class Limits:
    max_upload_bytes: int = 30 * 1024 * 1024
    max_pages: int = 60
    document_timeout_s: float = 600.0
    max_workers: int = 1
    max_batch_documents: int = 500


@dataclass
class HarnessConfig:
    name: str = "domyslny"
    pdf_reader: str = "pdfium"           # pdfium
    ocr: str = "none"                    # none | rapidocr
    ocr_dpi: int = 200
    ocr_policy: str = "if_needed"        # if_needed | always | never
    router: str = "rules"                # rules | llm
    extractor: str = "rules"             # rules | llm | none
    anchor: str = "words"                # words
    llm_input: str = "text"              # text | (image: E10)
    work_dir: str = str(WORK_ROOT / "server")
    seed: int = 20261122
    llm: LlmSettings = field(default_factory=LlmSettings)
    limits: Limits = field(default_factory=Limits)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_INTS = {"ocr_dpi", "seed", "max_upload_bytes", "max_pages", "max_workers", "max_batch_documents", "max_tokens", "retries"}
_FLOATS = {"document_timeout_s", "temperature", "timeout_s"}


def _coerce(name: str, raw: Any) -> Any:
    if name in _INTS:
        return int(raw)
    if name in _FLOATS:
        return float(raw)
    return raw


def _apply(obj: Any, data: Mapping[str, Any], where: str) -> None:
    known = {f.name for f in fields(obj)}
    for key, value in data.items():
        if key not in known:
            raise HarnessError("invalid_configuration", f"nieznane pole konfiguracji {where}{key}", stage="config")
        current = getattr(obj, key)
        if isinstance(current, (LlmSettings, Limits)):
            _apply(current, value, f"{key}.")
        else:
            setattr(obj, key, _coerce(key, value))


def load_config(path: str | Path | None = None, env: Mapping[str, str] | None = None) -> HarnessConfig:
    """Plik (opcjonalny) + nadpisania `HARNESS_*`; `HARNESS_LLM_MODEL`, `HARNESS_LIMITS_MAX_PAGES` itd."""
    environ = os.environ if env is None else env
    cfg = HarnessConfig()
    file_path = path or environ.get("HARNESS_CONFIG")
    if file_path:
        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise HarnessError("invalid_configuration", f"nie wczytano konfiguracji: {type(e).__name__}", stage="config") from e
        _apply(cfg, data, "")
    for name in (f.name for f in fields(cfg)):
        if name in ("llm", "limits"):
            continue
        raw = environ.get(f"HARNESS_{name.upper()}")
        if raw not in (None, ""):
            setattr(cfg, name, _coerce(name, raw))
    for group, prefix in ((cfg.llm, "LLM"), (cfg.limits, "LIMITS")):
        for f in fields(group):
            raw = environ.get(f"HARNESS_{prefix}_{f.name.upper()}")
            if raw not in (None, ""):
                setattr(group, f.name, _coerce(f.name, raw))
    return cfg
