"""Ustawienia aplikacji Odwołania2JSON odczytane ze środowiska.

Baza (SQLite przez SQLAlchemy, ADR-004) jest opcjonalna: brak ``DATABASE_URL`` nie
jest błędem, a warstwa dostępu do danych po prostu nie powstaje. ``WORK_DIR`` to
katalog roboczy z bajtami PDF i artefaktami (architektura §7).

Konfiguracja LLM: ``LLM_API_KEY`` (albo plik ``LLM_API_KEY_FILE`` poza Git),
``LLM_MODEL``, ``LLM_BASE_URL``, ``LLM_PROTOCOL`` (``anthropic`` | ``openai``)
i lista zezwolonych hostów ``LLM_ALLOWED_HOSTS``. Klucz nie pojawia się w ``repr``.
"""

from __future__ import annotations

import getpass
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from .errors import ProcessingError

if TYPE_CHECKING:
    from .llm.client import LlmSettings

__all__ = ["DEFAULT_ALLOWED_HOSTS", "Settings", "build_llm_settings", "resolve_api_key"]

# Hosty, do których wolno wysłać klucz i treść dokumentów bez dodatkowej zgody
# w konfiguracji. Inny host wymaga jawnego wpisu w LLM_ALLOWED_HOSTS (E14, C02).
DEFAULT_ALLOWED_HOSTS = ("api.minimax.io",)

_PROTOCOLS = ("anthropic", "openai")
_ERROR_EXPORTS = ("empty_json", "no_file")
_KEY_HINT = "ustaw LLM_API_KEY albo LLM_API_KEY_FILE (plik z kluczem poza Git)"


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


def _hosts(env: Mapping[str, str]) -> tuple[str, ...]:
    raw = _optional(env, "LLM_ALLOWED_HOSTS")
    if raw is None:
        return DEFAULT_ALLOWED_HOSTS
    return tuple(host.strip().lower() for host in raw.split(",") if host.strip())


@dataclass(frozen=True)
class Settings:
    """Niezmienny zestaw ustawień aplikacji."""

    input_dir: Path
    output_dir: Path
    work_dir: Path
    database_url: str | None
    llm_base_url: str | None
    llm_model: str | None
    llm_api_key: str | None = field(repr=False)
    ocr_enabled: bool
    docs_enabled: bool
    web_dir: Path
    llm_api_key_file: Path | None = None
    llm_protocol: str | None = None
    llm_allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS
    llm_max_output_tokens: int | None = None
    llm_timeout_s: float | None = None
    llm_max_calls: int | None = None
    error_export: str = "empty_json"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Buduje ustawienia z podanego mapowania albo ze środowiska procesu."""
        environment: Mapping[str, str] = os.environ if env is None else env
        key_file = _optional(environment, "LLM_API_KEY_FILE")
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
            llm_api_key_file=Path(key_file).expanduser() if key_file else None,
            llm_protocol=_optional(environment, "LLM_PROTOCOL"),
            llm_allowed_hosts=_hosts(environment),
            llm_max_output_tokens=_number(environment, "LLM_MAX_OUTPUT_TOKENS", int),
            llm_timeout_s=_number(environment, "LLM_TIMEOUT_S", float),
            llm_max_calls=_number(environment, "LLM_MAX_CALLS", int),
            error_export=_optional(environment, "ERROR_EXPORT") or "empty_json",
        )


def _number[T: (int, float)](
    env: Mapping[str, str], name: str, kind: Callable[[str], T]
) -> T | None:
    """Dodatnia liczba ze środowiska; zła wartość to jawny błąd konfiguracji."""
    raw = _optional(env, name)
    if raw is None:
        return None
    try:
        value = kind(raw)
    except ValueError:
        raise ProcessingError("invalid_configuration", f"{name} musi być liczbą") from None
    if value <= 0:
        raise ProcessingError("invalid_configuration", f"{name} musi być dodatnie")
    return value


def resolve_api_key(
    settings: Settings,
    *,
    interactive: bool,
    prompt: Callable[[str], str] = getpass.getpass,
) -> str:
    """Klucz ze środowiska, potem z pliku, a w trybie interaktywnym z ukrytego pytania.

    W trybie nieinteraktywnym (wsad bez terminala) brak klucza to jawny błąd
    `llm_authorization`: program nie czeka na wpisanie i nie przetwarza wsadu na pusto.
    """
    if settings.llm_api_key:
        return settings.llm_api_key
    if settings.llm_api_key_file is not None:
        try:
            lines = settings.llm_api_key_file.read_text(encoding="utf-8").split()
        except (OSError, UnicodeDecodeError) as error:
            raise ProcessingError(
                "llm_authorization",
                f"nie odczytano pliku z LLM_API_KEY_FILE ({type(error).__name__})",
            ) from None
        if not lines:
            raise ProcessingError("llm_authorization", "plik z LLM_API_KEY_FILE jest pusty")
        return lines[0]
    if interactive:
        typed = prompt("Klucz API LLM (znaki nie będą widoczne): ").strip()
        if typed:
            return typed
    raise ProcessingError("llm_authorization", f"brak klucza API LLM: {_KEY_HINT}")


def _protocol(settings: Settings, base_url: str) -> Literal["anthropic", "openai"]:
    """Protokół jawny albo wywnioskowany z adresu (ścieżka `/anthropic` to Anthropic)."""
    protocol = settings.llm_protocol
    if protocol is None:
        return "anthropic" if "anthropic" in base_url.lower() else "openai"
    if protocol == "anthropic":
        return "anthropic"
    if protocol == "openai":
        return "openai"
    raise ProcessingError(
        "invalid_configuration", f"LLM_PROTOCOL musi być jednym z: {', '.join(_PROTOCOLS)}"
    )


def build_llm_settings(settings: Settings, api_key: str) -> LlmSettings:
    """Ustawienia klienta LLM; brak adresu lub modelu to `invalid_configuration`."""
    from .llm.client import LlmSettings

    if settings.error_export not in _ERROR_EXPORTS:
        raise ProcessingError(
            "invalid_configuration", f"ERROR_EXPORT musi być jednym z: {', '.join(_ERROR_EXPORTS)}"
        )
    if settings.llm_base_url is None:
        raise ProcessingError("invalid_configuration", "brak adresu LLM: ustaw LLM_BASE_URL")
    if settings.llm_model is None:
        raise ProcessingError("invalid_configuration", "brak nazwy modelu: ustaw LLM_MODEL")
    base = LlmSettings(
        protocol=_protocol(settings, settings.llm_base_url),
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=api_key,
        allowed_hosts=settings.llm_allowed_hosts,
        # Lokalna atrapa (testy instalacji) działa po http; klucz nie opuszcza maszyny.
        allow_http_localhost=True,
    )
    if settings.llm_max_output_tokens is not None:
        base = replace(
            base,
            max_output_tokens=settings.llm_max_output_tokens,
            retry_output_tokens=min(base.retry_output_tokens, settings.llm_max_output_tokens),
        )
    if settings.llm_timeout_s is not None:
        base = replace(base, timeout_s=settings.llm_timeout_s)
    if settings.llm_max_calls is not None:
        base = replace(base, max_calls=settings.llm_max_calls)
    return base
