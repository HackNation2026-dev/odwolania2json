"""Ustawienia aplikacji Odwołania2JSON odczytane ze środowiska.

Baza (SQLite przez SQLAlchemy, ADR-004) jest opcjonalna: brak ``DATABASE_URL`` nie
jest błędem, a warstwa dostępu do danych po prostu nie powstaje. ``WORK_DIR`` to
katalog roboczy z bajtami PDF i artefaktami (architektura §7).

Konfiguracja LLM: ``LLM_API_KEY`` (albo plik ``LLM_API_KEY_FILE`` poza Git),
``LLM_MODEL``, ``LLM_BASE_URL``, ``LLM_PROTOCOL`` (``anthropic`` | ``openai``)
i lista zezwolonych hostów ``LLM_ALLOWED_HOSTS``. Klucz nie pojawia się w ``repr``.

Dostawca zapasowy (opcjonalny, ADR-007): ``LLM_FALLBACK_BASE_URL``,
``LLM_FALLBACK_MODEL``, ``LLM_FALLBACK_PROTOCOL``, ``LLM_FALLBACK_API_KEY`` albo
``LLM_FALLBACK_KEY_FILE``, ``LLM_FALLBACK_USER_AGENT`` i ``LLM_FALLBACK_HEADERS``
(obiekt JSON nagłówków dodatkowych; ``{session}`` w wartości to identyfikator
bieżącego uruchomienia). Adres zapasowego nie ma wartości domyślnej
i przechodzi tę samą walidację (https, ``LLM_ALLOWED_HOSTS``) co główny.
"""

from __future__ import annotations

import getpass
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from . import __version__
from .errors import ProcessingError

if TYPE_CHECKING:
    from .llm.client import LlmSettings

__all__ = [
    "DEFAULT_ALLOWED_HOSTS",
    "SESSION_PLACEHOLDER",
    "Settings",
    "build_fallback_settings",
    "build_llm_settings",
    "resolve_api_key",
]

# Hosty, do których wolno wysłać klucz i treść dokumentów bez dodatkowej zgody
# w konfiguracji. Inny host wymaga jawnego wpisu w LLM_ALLOWED_HOSTS (E14, C02).
DEFAULT_ALLOWED_HOSTS = ("api.minimax.io",)

# Znacznik w wartości nagłówka zastępowany identyfikatorem uruchomienia programu.
SESSION_PLACEHOLDER = "{session}"

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
    llm_max_total_tokens: int | None = None
    llm_max_retries: int | None = None
    llm_provider_cooldown_s: float | None = None
    llm_fallback_base_url: str | None = None
    llm_fallback_model: str | None = None
    llm_fallback_protocol: str | None = None
    llm_fallback_api_key: str | None = field(default=None, repr=False)
    llm_fallback_key_file: Path | None = None
    llm_fallback_user_agent: str | None = None
    llm_fallback_headers: tuple[tuple[str, str], ...] = field(default=(), repr=False)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Buduje ustawienia z podanego mapowania albo ze środowiska procesu."""
        environment: Mapping[str, str] = os.environ if env is None else env
        key_file = _optional(environment, "LLM_API_KEY_FILE")
        fallback_key_file = _optional(environment, "LLM_FALLBACK_KEY_FILE")
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
            llm_max_total_tokens=_number(environment, "LLM_MAX_TOTAL_TOKENS", int),
            llm_max_retries=_number(environment, "LLM_MAX_RETRIES", int, minimum=0),
            llm_provider_cooldown_s=_number(environment, "LLM_PROVIDER_COOLDOWN_S", float),
            llm_fallback_base_url=_optional(environment, "LLM_FALLBACK_BASE_URL"),
            llm_fallback_model=_optional(environment, "LLM_FALLBACK_MODEL"),
            llm_fallback_protocol=_optional(environment, "LLM_FALLBACK_PROTOCOL"),
            llm_fallback_api_key=_optional(environment, "LLM_FALLBACK_API_KEY"),
            llm_fallback_key_file=(
                Path(fallback_key_file).expanduser() if fallback_key_file else None
            ),
            llm_fallback_user_agent=_optional(environment, "LLM_FALLBACK_USER_AGENT"),
            llm_fallback_headers=_headers(environment, "LLM_FALLBACK_HEADERS"),
        )


def _number[T: (int, float)](
    env: Mapping[str, str], name: str, kind: Callable[[str], T], *, minimum: int | None = None
) -> T | None:
    """Liczba ze środowiska (domyślnie dodatnia); zła wartość to jawny błąd konfiguracji."""
    raw = _optional(env, name)
    if raw is None:
        return None
    try:
        value = kind(raw)
    except ValueError:
        raise ProcessingError("invalid_configuration", f"{name} musi być liczbą") from None
    if minimum is not None:
        if value < minimum:
            raise ProcessingError(
                "invalid_configuration", f"{name} nie może być mniejsze niż {minimum}"
            )
        return value
    if value <= 0:
        raise ProcessingError("invalid_configuration", f"{name} musi być dodatnie")
    return value


def _headers(env: Mapping[str, str], name: str) -> tuple[tuple[str, str], ...]:
    """Nagłówki dodatkowe z obiektu JSON; komunikat błędu nie cytuje wartości."""
    raw = _optional(env, name)
    if raw is None:
        return ()
    try:
        parsed: object = json.loads(raw)
    except ValueError:
        raise ProcessingError("invalid_configuration", f"{name} musi być obiektem JSON") from None
    if not isinstance(parsed, dict) or not all(isinstance(v, str) for v in parsed.values()):
        raise ProcessingError(
            "invalid_configuration", f"{name} musi być obiektem JSON z tekstowymi wartościami"
        )
    return tuple((str(key), str(value)) for key, value in parsed.items())


def _key_from_file(path: Path, name: str) -> str:
    try:
        tokens = path.read_text(encoding="utf-8").split()
    except (OSError, UnicodeDecodeError) as error:
        raise ProcessingError(
            "llm_authorization", f"nie odczytano pliku z {name} ({type(error).__name__})"
        ) from None
    if not tokens:
        raise ProcessingError("llm_authorization", f"plik z {name} jest pusty")
    return tokens[0]


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
        return _key_from_file(settings.llm_api_key_file, "LLM_API_KEY_FILE")
    if interactive:
        typed = prompt("Klucz API LLM (znaki nie będą widoczne): ").strip()
        if typed:
            return typed
    raise ProcessingError("llm_authorization", f"brak klucza API LLM: {_KEY_HINT}")


def _protocol(explicit: str | None, base_url: str, name: str) -> Literal["anthropic", "openai"]:
    """Protokół jawny albo wywnioskowany z adresu (ścieżka `/anthropic` to Anthropic)."""
    if explicit is None:
        return "anthropic" if "anthropic" in base_url.lower() else "openai"
    if explicit == "anthropic":
        return "anthropic"
    if explicit == "openai":
        return "openai"
    raise ProcessingError(
        "invalid_configuration", f"{name} musi być jednym z: {', '.join(_PROTOCOLS)}"
    )


def _with_limits(settings: Settings, base: LlmSettings) -> LlmSettings:
    """Limity ze środowiska są wspólne dla dostawcy głównego i zapasowego."""
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
    if settings.llm_max_retries is not None:
        base = replace(base, max_retries=settings.llm_max_retries)
    return base


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
        protocol=_protocol(settings.llm_protocol, settings.llm_base_url, "LLM_PROTOCOL"),
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=api_key,
        allowed_hosts=settings.llm_allowed_hosts,
        # Lokalna atrapa (testy instalacji) działa po http; klucz nie opuszcza maszyny.
        allow_http_localhost=True,
    )
    return _with_limits(settings, base)


def build_fallback_settings(settings: Settings, session_id: str) -> LlmSettings | None:
    """Ustawienia dostawcy zapasowego albo `None`, gdy nie jest skonfigurowany.

    `session_id` to identyfikator bieżącego uruchomienia programu: zastępuje
    znacznik `{session}` w wartościach `LLM_FALLBACK_HEADERS` (dostawcy wymagający
    nagłówka sesji dostają jeden identyfikator na proces). Domyślny `User-Agent`
    przedstawia program jego własną nazwą i wersją.

    Adres zapasowego nie ma wartości domyślnej: wybór drugiego dostawcy (i jego
    zgodność z wymogami konkursu) należy do człowieka. Niepełna konfiguracja to
    `ProcessingError`, który wywołujący zamienia na ostrzeżenie: zapas jest opcjonalny.
    """
    from .llm.client import LlmSettings

    base_url = settings.llm_fallback_base_url
    if base_url is None:
        return None
    if settings.llm_fallback_model is None:
        raise ProcessingError(
            "invalid_configuration", "brak modelu dostawcy zapasowego: ustaw LLM_FALLBACK_MODEL"
        )
    if settings.llm_fallback_api_key:
        api_key = settings.llm_fallback_api_key
    elif settings.llm_fallback_key_file is not None:
        api_key = _key_from_file(settings.llm_fallback_key_file, "LLM_FALLBACK_KEY_FILE")
    else:
        raise ProcessingError(
            "llm_authorization",
            "brak klucza dostawcy zapasowego: "
            "ustaw LLM_FALLBACK_API_KEY albo LLM_FALLBACK_KEY_FILE",
        )
    base = LlmSettings(
        protocol=_protocol(settings.llm_fallback_protocol, base_url, "LLM_FALLBACK_PROTOCOL"),
        base_url=base_url,
        model=settings.llm_fallback_model,
        api_key=api_key,
        allowed_hosts=settings.llm_allowed_hosts,
        allow_http_localhost=True,
        user_agent=settings.llm_fallback_user_agent or f"odwolania2json/{__version__}",
        extra_headers=tuple(
            (name, value.replace(SESSION_PLACEHOLDER, session_id))
            for name, value in settings.llm_fallback_headers
        ),
    )
    return _with_limits(settings, base)
