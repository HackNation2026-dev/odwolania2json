"""Jedyny adapter sterownika: transakcje SQLite kontrolowane przez SQLAlchemy."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.pool import ConnectionPoolEntry


def normalize_url(database_url: str) -> str:
    """Odrzuca inne bazy i sterowniki przed utworzeniem połączenia."""
    url = make_url(database_url)
    if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
        raise ValueError("Obsługiwana jest wyłącznie baza SQLite przez SQLAlchemy.")
    return database_url


#: Opcja wykonania oznaczająca transakcję zapisu (``BEGIN IMMEDIATE``).
WRITE_OPTION = "o2j_write"


def create_database_engine(database_url: str) -> Engine:
    """Włącza FK i jawny BEGIN, aby także DDL podlegało rollbackowi.

    Odczyty używają zwykłego ``BEGIN``; zapisy przez :func:`write_transaction`
    zajmują blokadę zapisu od początku, więc nie kończą się błędem „locked”
    przy podnoszeniu blokady w środku transakcji.
    """
    engine = create_engine(normalize_url(database_url))

    @event.listens_for(engine, "connect")
    def configure(connection: sqlite3.Connection, record: ConnectionPoolEntry) -> None:
        connection.isolation_level = None
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            # WAL pozwala czytać podczas zapisu; dla bazy w pamięci pozostaje „memory”.
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()

    @event.listens_for(engine, "begin")
    def begin(connection: Connection) -> None:
        # Blokada przed odczytem wersji chroni przed wyścigiem migratorów i
        # lost update w claim_job/commit_run.
        immediate = bool(connection.get_execution_options().get(WRITE_OPTION))
        connection.exec_driver_sql("BEGIN IMMEDIATE" if immediate else "BEGIN")

    return engine


@contextmanager
def write_transaction(engine: Engine) -> Iterator[Connection]:
    """Transakcja zapisu: ``BEGIN IMMEDIATE``, commit na wyjściu, rollback przy wyjątku."""
    with engine.connect() as connection:
        connection.execution_options(**{WRITE_OPTION: True})
        with connection.begin():
            yield connection


def split_statements(script: str) -> list[str]:
    """Parser sterownika zachowuje średniki w literałach i ciałach triggerów."""
    statements: list[str] = []
    buffer = ""
    for char in script:
        buffer += char
        if char == ";" and sqlite3.complete_statement(buffer):
            statements.append(buffer)
            buffer = ""
    if buffer.strip():
        statements.append(buffer)
    return statements
