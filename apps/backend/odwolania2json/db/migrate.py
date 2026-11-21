"""Migrator schematu bazy: pliki ``NNNN_nazwa.sql`` nakładane po kolei.

Każdy plik jest wykonywany jako całość w jednej transakcji, a zastosowana
wersja trafia do tabeli ``schema_migrations``. Migracja zastosowana wcześniej
nie jest wykonywana ponownie.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

from .repository import normalize_url

__all__ = ["MIGRATIONS_DIR", "applied_versions", "migrate", "migrate_with_directory"]

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

#: Nazwa tabeli z zastosowanymi migracjami.
_SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


def _migration_files(directory: Path | None = None) -> list[Path]:
    """Zwraca pliki migracji posortowane po nazwie."""
    katalog = MIGRATIONS_DIR if directory is None else directory
    if not katalog.is_dir():
        return []
    return sorted(katalog.glob("*.sql"))


def _version_of(path: Path) -> str:
    """Nazwa pliku migracji bez rozszerzenia to numer wersji."""
    return path.stem


def _table_exists(connection, table_name: str) -> bool:
    """Czy wskazana tabela istnieje w schemacie ``public``."""
    return bool(
        connection.execute(
            text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = :name"
            ),
            {"name": table_name},
        ).scalar()
    )


def applied_versions(database_url: str) -> list[str]:
    """Zwraca listę wersji migracji już zastosowanych w bazie.

    Funkcja jest czystym odczytem: nie tworzy żadnych tabel. Gdy tabela
    ``schema_migrations`` jeszcze nie istnieje, zwraca pustą listę.
    """
    engine = create_engine(normalize_url(database_url), future=True)
    try:
        with engine.connect() as connection:
            if not _table_exists(connection, _SCHEMA_MIGRATIONS_TABLE):
                return []
            rows = connection.execute(
                text("SELECT version FROM schema_migrations ORDER BY version ASC")
            )
        return [row[0] for row in rows]
    finally:
        engine.dispose()


def migrate(database_url: str) -> list[str]:
    """Nakłada brakujące migracje; zwraca listę właśnie zastosowanych wersji."""
    return migrate_with_directory(database_url, MIGRATIONS_DIR)


def migrate_with_directory(database_url: str, directory: Path) -> list[str]:
    """Nakłada migracje z podanego katalogu; zwraca zastosowane wersje.

    Blokada doradcza jest pobierana **przed** odczytem zastosowanych wersji i
    trzymana przez cały przebieg, więc dwa procesy nie wykonają tej samej
    migracji równolegle. Każdy plik migracji jest jedną transakcją: albo
    wykonuje się w całości, albo zostaje cofnięty w całości.
    """
    engine = create_engine(normalize_url(database_url), future=True)
    applied: list[str] = []
    try:
        for path in _migration_files(directory):
            version = _version_of(path)
            script = path.read_text(encoding="utf-8")
            with engine.begin() as connection:
                # Blokada na poziomie sesji trzymana do końca transakcji.
                connection.execute(
                    text("SELECT pg_advisory_xact_lock(:key)"),
                    {"key": _ADVISORY_LOCK_KEY},
                )
                connection.execute(text(_SCHEMA_MIGRATIONS))
                already_applied = bool(
                    connection.execute(
                        text(
                            "SELECT count(*) FROM schema_migrations "
                            "WHERE version = :version"
                        ),
                        {"version": version},
                    ).scalar()
                )
                if already_applied:
                    continue
                # Cały plik jako jeden skrypt — bez własnego dzielenia na
                # wyrażenia, żeby nie rozrywać napisów i komentarzy.
                connection.exec_driver_sql(script)
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
