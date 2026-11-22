"""Dispatcher poleceń wiersza poleceń Odwołania2JSON.

Każde polecenie ma własny moduł (``odwolania2json.db.migrate`` itd.), a ``cli``
jest cienką warstwą wywołującą te same funkcje. Dzięki temu rozbudowa CLI nie
psuje startu kontenera.
"""

from __future__ import annotations

import argparse
import contextlib
import sys
import time
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from .config import Settings, build_fallback_settings, build_llm_settings, resolve_api_key
from .errors import ProcessingError
from .extract.ports import JsonLlm

if TYPE_CHECKING:
    from .llm.chain import LlmChain
    from .llm.client import LlmClient

__all__ = ["APP_NAME", "build_llm_client", "build_parser", "main"]

APP_NAME = "Odwołania2JSON"


class BatchLlm(JsonLlm, Protocol):
    """Klient LLM wsadu: odpowiedzi JSON oraz próba połączenia przed wsadem."""

    def self_check(self) -> Sequence[str] | None: ...


# Próba połączenia przed wsadem: chwilowy brak sieci dostaje kilka podejść,
# zły klucz albo wyczerpany limit (401/403/429) kończą od razu.
_SELF_CHECK_ATTEMPTS = 3
_SELF_CHECK_DELAY_S = 2.0
_SELF_CHECK_HINTS = {
    "llm_authorization": "sprawdź LLM_API_KEY (albo LLM_API_KEY_FILE)",
    "llm_rate_limit": "limit zapytań lub konta LLM jest wyczerpany; ponów później",
    "llm_unavailable": "sprawdź sieć i LLM_BASE_URL",
    "invalid_configuration": "sprawdź LLM_BASE_URL, LLM_MODEL, LLM_PROTOCOL i LLM_ALLOWED_HOSTS",
}


def build_parser() -> argparse.ArgumentParser:
    """Buduje parser argumentów CLI."""
    parser = argparse.ArgumentParser(
        prog="odwolania2json",
        description=f"{APP_NAME} — konwerter PDF-ów spraw odwoławczych do ścisłego JSON.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="polecenie")
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="nakłada migracje schematu bazy",
        description="Nakłada migracje schematu bazy; idempotentne.",
    )
    migrate_parser.add_argument(
        "--database-url",
        default=None,
        help="adres bazy; domyślnie ze zmiennej DATABASE_URL",
    )
    process_parser = subparsers.add_parser(
        "process",
        help="przetwarza PDF-y z katalogu wejściowego do JSON w katalogu wyjściowym",
        description=(
            "Odtwarza strukturę katalogów wejścia i zapisuje raport report.jsonl; kody wyjścia: "
            "0 OK, 1 błąd dokumentu, 2 błąd użycia, konfiguracji albo połączenia z LLM."
        ),
    )
    process_parser.add_argument(
        "input_dir",
        nargs="?",
        default=None,
        help="katalog z PDF-ami (przeszukiwany rekurencyjnie); domyślnie INPUT_DIR albo input",
    )
    process_parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="katalog na wyniki JSON; domyślnie OUTPUT_DIR albo output",
    )
    return parser


def _use_utf8_output() -> None:
    """Wymusza UTF-8 na wyjściu procesu, aby polskie znaki nie przerywały pracy konsoli."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        with contextlib.suppress(ValueError, OSError):
            reconfigure(encoding="utf-8", errors="replace")


def _run_migrate(arguments: argparse.Namespace) -> int:
    """Wykonuje polecenie ``migrate`` — nakłada migracje schematu bazy."""
    from .db import migrate as migrator

    database_url = arguments.database_url or Settings.from_env().database_url or ""
    if not database_url.strip():
        print("pominięto: baza nie skonfigurowana")
        return 0
    for version in migrator.migrate(database_url):
        print(version)
    return 0


def _fallback_client(settings: Settings, primary: LlmClient) -> LlmClient | None:
    """Klient dostawcy zapasowego albo `None`; wadliwa konfiguracja zapasu to ostrzeżenie."""
    from .llm.client import LlmClient

    try:
        # Jeden identyfikator sesji na uruchomienie programu (znacznik `{session}`).
        fallback = build_fallback_settings(settings, str(uuid.uuid4()))
        if fallback is None:
            return None
        return LlmClient(fallback, budget=primary.budget)
    except ProcessingError as error:
        print(
            f"ostrzeżenie: dostawca zapasowy LLM pominięty: {error.code}: {error.message}",
            file=sys.stderr,
        )
        return None


def build_llm_client(settings: Settings) -> LlmChain:
    """Łańcuch dostawców LLM z ustawień; brak klucza bez terminala to jawny błąd."""
    from .llm.chain import DEFAULT_COOLDOWN_S, LlmChain
    from .llm.client import LlmBudget, LlmClient

    interactive = sys.stdin.isatty() and sys.stderr.isatty()
    api_key = resolve_api_key(settings, interactive=interactive)
    primary_settings = build_llm_settings(settings, api_key)
    # Wspólny budżet: zapasowy dostawca nie podwaja limitu wywołań ani tokenów wsadu.
    budget = LlmBudget(primary_settings.max_calls, settings.llm_max_total_tokens)
    primary = LlmClient(primary_settings, budget=budget)
    return LlmChain(
        primary,
        _fallback_client(settings, primary),
        cooldown_s=settings.llm_provider_cooldown_s or DEFAULT_COOLDOWN_S,
    )


def _self_check(client: BatchLlm, sleep: Callable[[float], None]) -> None:
    """Jedno wywołanie próbne na dostawcę; tylko niedostępność sieci jest ponawiana."""
    for attempt in range(1, _SELF_CHECK_ATTEMPTS + 1):
        try:
            for warning in client.self_check() or ():
                print(f"ostrzeżenie: {warning}", file=sys.stderr)
            return
        except ProcessingError as error:
            if error.code != "llm_unavailable" or attempt == _SELF_CHECK_ATTEMPTS:
                raise
            sleep(_SELF_CHECK_DELAY_S * attempt)


def _run_process(arguments: argparse.Namespace, sleep: Callable[[float], None]) -> int:
    """Wykonuje polecenie ``process``: self-check LLM, potem PDF-y na wyniki JSON.

    Zły klucz albo wyczerpany limit dałyby pusty wynik całego wsadu, więc
    sprawdzamy połączenie raz przed wsadem i kończymy kodem 2 z komunikatem.
    """
    from .engine import EXIT_OK, EXIT_USAGE, Engine, ErrorExport, find_pdfs, run_process

    settings = Settings.from_env()
    input_dir = Path(arguments.input_dir) if arguments.input_dir else settings.input_dir
    output_dir = Path(arguments.output_dir) if arguments.output_dir else settings.output_dir
    if not input_dir.is_dir():
        print(f"błąd: katalog wejściowy nie istnieje: {input_dir}", file=sys.stderr)
        return EXIT_USAGE
    if not find_pdfs(input_dir):
        print(f"brak plików PDF w katalogu wejściowym: {input_dir}")
        return EXIT_OK
    try:
        client: BatchLlm = build_llm_client(settings)
        _self_check(client, sleep)
    except ProcessingError as error:
        print(f"błąd: {error.code}: {error.message}", file=sys.stderr)
        hint = _SELF_CHECK_HINTS.get(error.code)
        if hint:
            print(f"wskazówka: {hint}", file=sys.stderr)
        print("wsad nie został przetworzony", file=sys.stderr)
        return EXIT_USAGE
    error_export: ErrorExport = "no_file" if settings.error_export == "no_file" else "empty_json"
    exit_code = run_process(input_dir, output_dir, Engine(client), error_export=error_export)
    _print_usage(client)
    return exit_code


def _print_usage(client: object) -> None:
    """Zużycie LLM w tym wsadzie (wywołania i tokeny łącznie dla obu dostawców)."""
    from .llm.client import LlmBudget

    budget = getattr(client, "budget", None)
    if isinstance(budget, LlmBudget):
        print(
            f"LLM: wywołania={budget.calls} tokeny_wejścia={budget.input_tokens} "
            f"tokeny_wyjścia={budget.output_tokens}"
        )


def main(argv: list[str] | None = None, *, sleep: Callable[[float], None] = time.sleep) -> int:
    """Uruchamia CLI i zwraca kod wyjścia procesu."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not arguments:
        parser.print_help()
        return 0
    parsed = parser.parse_args(arguments)
    if parsed.command == "migrate":
        return _run_migrate(parsed)
    if parsed.command == "process":
        return _run_process(parsed, sleep)
    parser.print_help()
    return 0


if __name__ == "__main__":
    _use_utf8_output()
    raise SystemExit(main())
