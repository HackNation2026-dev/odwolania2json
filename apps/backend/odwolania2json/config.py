"""Ustawienia aplikacji Odwołania2JSON odczytane ze środowiska.

Baza (SQLite przez SQLAlchemy, ADR-004) jest opcjonalna: brak ``DATABASE_URL`` nie
jest błędem, a warstwa dostępu do danych po prostu nie powstaje. ``WORK_DIR`` to
katalog roboczy z bajtami PDF i artefaktami (architektura §7).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Settings"]


def _default_web_dir() -> Path:
    """Zwraca katalog ``apps/web`` liczony od położenia tego modułu."""
    return Path(__file__).resolve().parents[2] / "web"


def _flag(env: Mapping[str, str], name: str) -> bool:
    """Czyta flagę ``0``/``1`` ze środowiska; brak wartości oznacza ``False``."""
    raw = env.get(name, "").strip().lower()
    return raw in {"1", "true", "yes", "tak", "on"}


def _optional(env: Mapping[str, str], name: str) -> str | None:
    """Czyta opcjonalny tekst ze środowiska; pusta wartość to brak."""
    value = env.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


@dataclass(frozen=True)
class Settings:
    """Niezmienny zestaw ustawień aplikacji."""

    input_dir: Path
    output_dir: Path
    work_dir: Path
    database_url: str | None
    llm_base_url: str | None
    llm_model: str | None
    llm_api_key: str | None
    ocr_enabled: bool
    docs_enabled: bool
    web_dir: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Buduje ustawienia z podanego mapowania albo ze środowiska procesu."""
        environment: Mapping[str, str] = os.environ if env is None else env
        return cls(
            input_dir=Path(environment.get("INPUT_DIR", "input")),
            output_dir=Path(environment.get("OUTPUT_DIR", "output")),
            work_dir=Path(environment.get("WORK_DIR", "work")),
            database_url=_optional(environment, "DATABASE_URL"),
            llm_base_url=_optional(environment, "LLM_BASE_URL"),
            llm_model=_optional(environment, "LLM_MODEL"),
            llm_api_key=_optional(environment, "LLM_API_KEY"),
            ocr_enabled=_flag(environment, "OCR_ENABLED"),
            docs_enabled=_flag(environment, "O2J_DOCS_ENABLED"),
            web_dir=Path(environment.get("O2J_WEB_DIR") or _default_web_dir()),
        )
