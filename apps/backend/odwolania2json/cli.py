"""Dispatcher poleceń wiersza poleceń Odwołania2JSON.

Każde polecenie ma własny moduł (``odwolania2json.db.migrate`` itd.), a ``cli``
jest cienką warstwą wywołującą te same funkcje. Dzięki temu rozbudowa CLI nie
psuje startu kontenera.
"""

from __future__ import annotations

import argparse
import sys

from .config import Settings

__all__ = ["APP_NAME", "build_parser", "main"]

APP_NAME = "Odwołania2JSON"


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
    return parser


def _use_utf8_output() -> None:
    """Wymusza UTF-8 na wyjściu procesu, aby polskie znaki nie przerywały pracy konsoli."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


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


def main(argv: list[str] | None = None) -> int:
    """Uruchamia CLI i zwraca kod wyjścia procesu."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not arguments:
        parser.print_help()
        return 0
    parsed = parser.parse_args(arguments)
    if parsed.command == "migrate":
        return _run_migrate(parsed)
    parser.print_help()
    return 0


if __name__ == "__main__":
    _use_utf8_output()
    raise SystemExit(main())
