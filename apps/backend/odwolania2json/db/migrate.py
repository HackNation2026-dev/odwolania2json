"""Migrator schematu bazy: pliki ``NNNN_nazwa.sql`` nakładane po kolei.

Każdy plik jest wykonywany w osobnej transakcji, a zastosowana wersja trafia
do tabeli ``schema_migrations``. Migracja zastosowana wcześniej nie jest
wykonywana ponownie.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

from .repository import normalize_url

__all__ = ["MIGRATIONS_DIR", "applied_versions", "migrate"]

#: Katalog z plikami migracji.
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

#: Klucz blokady doradczej — chroni przed równoczesnym nakładaniem migracji.
_ADVISORY_LOCK_KEY = 8420113

#: Tabela z listą zastosowanych migracji.
_SCHEMA_MIGRATIONS = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
)
"""


def _split_statements(sql: str) -> list[str]:
    """Dzieli skrypt SQL na osobne wyrażenia (bez semicolonów w literalach)."""
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    previous = ""
    for character in sql:
        if character == "'" and previous != "'":
            in_string = not in_string
        if character == ";" and not in_string:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(character)
        previous = character
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def _migration_files() -> list[Path]:
    """Zwraca pliki migracji posortowane po nazwie."""
    if not MIGRATIONS_DIR.is_dir():
        return []
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def _version_of(path: Path) -> str:
    """Nazwa pliku migracji bez rozszerzenia to numer wersji."""
    return path.stem


def applied_versions(database_url: str) -> list[str]:
    """Zwraca listę wersji migracji już zastosowanych w bazie."""
    engine = create_engine(normalize_url(database_url), future=True)
    try:
        with engine.begin() as connection:
            connection.execute(text(_SCHEMA_MIGRATIONS))
            rows = connection.execute(
                text("SELECT version FROM schema_migrations ORDER BY version ASC")
            )
        return [row[0] for row in rows]
    finally:
        engine.dispose()


def migrate(database_url: str) -> list[str]:
    """Nakłada brakujące migracje; zwraca listę właśnie zastosowanych wersji."""
    engine = create_engine(normalize_url(database_url), future=True)
    applied: list[str] = []
    try:
        with engine.begin() as connection:
            connection.execute(text(_SCHEMA_MIGRATIONS))
            known = {
                row[0]
                for row in connection.execute(
                    text("SELECT version FROM schema_migrations")
                )
            }
        for path in _migration_files():
            version = _version_of(path)
            if version in known:
                continue
            script = path.read_text(encoding="utf-8")
            # Blokada doradcza: dwa kontenery startujące naraz nie nakładają
            # tej samej migracji równolegle.
            with engine.begin() as connection:
                connection.execute(
                    text("SELECT pg_advisory_xact_lock(:key)"),
                    {"key": _ADVISORY_LOCK_KEY},
                )
                for statement in _split_statements(script):
                    connection.execute(text(statement))
                connection.execute(
                    text(
                        "INSERT INTO schema_migrations (version) VALUES (:version) "
                        "ON CONFLICT (version) DO NOTHING"
                    ),
                    {"version": version},
                )
            applied.append(version)
    finally:
        engine.dispose()
    return applied


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


def main(argv: list[str] | None = None) -> int:
    """Uruchamia migracje z wiersza poleceń (``python -m odwolania2json.db.migrate``)."""
    parser = argparse.ArgumentParser(
        prog="python -m odwolania2json.db.migrate",
        description="Nakłada migracje schematu bazy Odwołania2JSON.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="adres bazy; domyślnie ze zmiennej DATABASE_URL",
    )
    arguments = parser.parse_args(argv)

    database_url = arguments.database_url or os.environ.get("DATABASE_URL", "")
    if not database_url.strip():
        print("pominięto: baza nie skonfigurowana")
        return 0
    for version in migrate(database_url):
        print(version)
    return 0


if __name__ == "__main__":
    _use_utf8_output()
    raise SystemExit(main())
