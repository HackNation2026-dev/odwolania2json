"""Repozytorium dokumentów, przebiegów i ekstrakcji w PostgreSQL.

Warstwa jest opcjonalna: bez ``DATABASE_URL`` nic nie powstaje i aplikacja
działa dalej. Zapisy idą wyłącznie przez parametry nazwane (``text()`` z
parametrami), nigdy przez sklejanie SQL-u ze stringów.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

__all__ = [
    "DocumentRepository",
    "ReadOnlySqlError",
    "is_configured",
    "normalize_url",
]

#: Schematy URL wymieniane na sterownik ``pg8000`` (czysty Python, bez kompilacji).
_DRIVER_SCHEMES = ("postgresql://", "postgres://")

#: Słowa, których nie wolno w zapytaniu wykonywanym w trybie tylko do odczytu.
_FORBIDDEN_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "copy",
    "call",
    "do",
    "vacuum",
    "analyze",
)


class ReadOnlySqlError(RuntimeError):
    """Zapytanie SQL nie jest odczytem i zostało odrzucone."""


def normalize_url(database_url: str) -> str:
    """Zamienia schemat ``postgresql``/``postgres`` na sterownik ``pg8000``."""
    for scheme in _DRIVER_SCHEMES:
        if database_url.startswith(scheme):
            return "postgresql+pg8000://" + database_url[len(scheme) :]
    return database_url


def is_configured(database_url: str | None) -> bool:
    """Czy baza jest skonfigurowana — wystarczy niepusty adres."""
    if database_url is None:
        return False
    return bool(database_url.strip())


def _strip_comments(sql: str) -> str:
    """Usuwa komentarze ``--`` i bloki ``/* */`` oraz zwija białe znaki."""
    without_block = sql.replace("/*", " ")
    lines = [line.split("--", 1)[0] for line in without_block.splitlines()]
    return " ".join(" ".join(lines).split())


def _assert_read_only(sql: str) -> None:
    """Sprawdza, że zapytanie jest odczytem; inaczej rzuca ``ReadOnlySqlError``."""
    cleaned = _strip_comments(sql).strip()
    if not cleaned:
        raise ReadOnlySqlError("Zapytanie SQL jest puste.")
    head = cleaned.split(None, 1)[0].lower()
    if head not in {"select", "with"}:
        raise ReadOnlySqlError(
            f"Dozwolone są wyłącznie zapytania SELECT lub WITH, a nie: {head.upper()}."
        )
    lowered = cleaned.lower()
    for keyword in _FORBIDDEN_KEYWORDS:
        if keyword in lowered:
            raise ReadOnlySqlError(
                f"Zapytanie zawiera niedozwolone słowo: {keyword.upper()}."
            )


def _json_value(value: Any) -> Any:
    """Zamienia wartość na tekst JSON gotowy do rzutowania na kolumnę ``jsonb``."""
    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        text_value = value.decode("utf-8") if isinstance(value, bytes) else value
        try:
            json.loads(text_value)
        except (ValueError, TypeError):
            return json.dumps(text_value, ensure_ascii=False)
        return text_value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _as_dicts(rows: Any) -> list[dict]:
    """Zamienia wiersze ``RowMapping`` na listę zwykłych słowników."""
    return [dict(row) for row in rows]


class DocumentRepository:
    """Dostęp do dokumentów, przebiegów i ekstrakcji zapisanych w PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        """Tworzy repozytorium dla podanego adresu bazy."""
        if not is_configured(database_url):
            raise ValueError("Adres bazy jest pusty — repozytorium nie powstaje.")
        self.database_url = database_url
        self._engine: Engine = create_engine(normalize_url(database_url), future=True)

    @property
    def engine(self) -> Engine:
        """Silnik SQLAlchemy używany przez repozytorium."""
        return self._engine

    def dispose(self) -> None:
        """Zamyka pulę połączeń."""
        self._engine.dispose()

    # -- zapisy ------------------------------------------------------------

    def upsert_document(
        self,
        document_id: str | UUID,
        filename: str,
        sha256: str,
        size_bytes: int | None = None,
        source_path: str | None = None,
        page_count: int | None = None,
        has_text_layer: bool | None = None,
    ) -> None:
        """Wstawia dokument albo aktualizuje istniejący o tym samym ``sha256``."""
        statement = text(
            """
            INSERT INTO documents (id, filename, sha256, size_bytes, source_path,
                                   page_count, has_text_layer)
            VALUES (:id, :filename, :sha256, :size_bytes, :source_path,
                    :page_count, :has_text_layer)
            ON CONFLICT (sha256) DO UPDATE SET
                filename = EXCLUDED.filename,
                size_bytes = EXCLUDED.size_bytes,
                source_path = EXCLUDED.source_path,
                page_count = EXCLUDED.page_count,
                has_text_layer = EXCLUDED.has_text_layer
            """
        )
        parameters = {
            "id": str(document_id),
            "filename": filename,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "source_path": source_path,
            "page_count": page_count,
            "has_text_layer": has_text_layer,
        }
        with self._engine.begin() as connection:
            connection.execute(statement, parameters)

    def upsert_run(
        self,
        run_id: str | UUID,
        status: str,
        documents_count: int = 0,
        duration_ms: int | None = None,
    ) -> None:
        """Wstawia przebieg albo aktualizuje jego stan."""
        statement = text(
            """
            INSERT INTO runs (id, status, documents_count, duration_ms)
            VALUES (:id, :status, :documents_count, :duration_ms)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                documents_count = EXCLUDED.documents_count,
                duration_ms = EXCLUDED.duration_ms,
                finished_at = now()
            """
        )
        parameters = {
            "id": str(run_id),
            "status": status,
            "documents_count": documents_count,
            "duration_ms": duration_ms,
        }
        with self._engine.begin() as connection:
            connection.execute(statement, parameters)

    def upsert_extraction(
        self,
        extraction_id: str | UUID,
        document_id: str | UUID,
        run_id: str | UUID,
        document_class: str,
        schema_version: str,
        payload: Any,
        evidence: Any,
    ) -> None:
        """Wstawia ekstrakcję albo aktualizuje istniejącą o tym samym identyfikatorze."""
        statement = text(
            """
            INSERT INTO extractions (id, document_id, run_id, class, schema_version,
                                     payload, evidence)
            VALUES (:id, :document_id, :run_id, :class, :schema_version,
                    CAST(:payload AS jsonb), CAST(:evidence AS jsonb))
            ON CONFLICT (id) DO UPDATE SET
                document_id = EXCLUDED.document_id,
                run_id = EXCLUDED.run_id,
                class = EXCLUDED.class,
                schema_version = EXCLUDED.schema_version,
                payload = EXCLUDED.payload,
                evidence = EXCLUDED.evidence
            """
        )
        parameters = {
            "id": str(extraction_id),
            "document_id": str(document_id),
            "run_id": str(run_id),
            "class": document_class,
            "schema_version": schema_version,
            "payload": _json_value(payload),
            "evidence": _json_value(evidence),
        }
        with self._engine.begin() as connection:
            connection.execute(statement, parameters)

    # -- odczyty ------------------------------------------------------------

    def _scalar(self, statement: Any) -> Any:
        """Wykonuje zapytanie zwracające pojedynczą wartość."""
        with self._engine.connect() as connection:
            return connection.execute(statement).scalar()

    def count_documents(self) -> int:
        """Liczba dokumentów w bazie."""
        return int(self._scalar(text("SELECT count(*) FROM documents")) or 0)

    def count_extractions(self) -> int:
        """Liczba ekstrakcji w bazie."""
        return int(self._scalar(text("SELECT count(*) FROM extractions")) or 0)

    def count_runs(self) -> int:
        """Liczba przebiegów w bazie."""
        return int(self._scalar(text("SELECT count(*) FROM runs")) or 0)

    def class_counts(self) -> list[dict]:
        """Rozkład ekstrakcji według klas dokumentów."""
        statement = text(
            """
            SELECT class, count(*) AS count
            FROM extractions
            GROUP BY class
            ORDER BY count DESC, class ASC
            """
        )
        with self._engine.connect() as connection:
            return _as_dicts(connection.execute(statement).mappings())

    def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        name_filter: str | None = None,
        document_class: str | None = None,
    ) -> list[dict]:
        """Lista dokumentów z opcjonalnym filtrem po nazwie i klasie."""
        # Warunki składane są ze stałych wariantów SQL — nie ma tu sklejania
        # danych wejściowych z tekstem zapytania.
        conditions: list[str] = []
        parameters: dict[str, Any] = {"limit": limit, "offset": offset}
        if name_filter:
            conditions.append("d.filename ILIKE :name_pattern")
            parameters["name_pattern"] = f"%{name_filter}%"
        if document_class:
            conditions.append("e.class = :document_class")
            parameters["document_class"] = document_class
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        statement = text(
            f"""
            SELECT d.id, d.filename, d.sha256, d.size_bytes, d.source_path,
                   d.page_count, d.has_text_layer, d.created_at,
                   e.class AS document_class
            FROM documents d
            LEFT JOIN extractions e ON e.document_id = d.id
            {where}
            ORDER BY d.created_at DESC, d.filename ASC
            LIMIT :limit OFFSET :offset
            """
        )
        with self._engine.connect() as connection:
            return _as_dicts(
                connection.execute(statement, parameters).mappings()
            )

    def get_document(self, document_id: str | UUID) -> dict | None:
        """Jeden dokument po identyfikatorze albo ``None``."""
        statement = text(
            """
            SELECT id, filename, sha256, size_bytes, source_path, page_count,
                   has_text_layer, created_at
            FROM documents
            WHERE id = :id
            """
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement, {"id": str(document_id)}).mappings().first()
        return dict(row) if row is not None else None

    def list_extractions(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """Lista ekstrakcji z podsumowaniem dokumentu."""
        statement = text(
            """
            SELECT e.id, e.document_id, e.run_id, e.class, e.schema_version,
                   e.payload, e.evidence, e.created_at, d.filename
            FROM extractions e
            LEFT JOIN documents d ON d.id = e.document_id
            ORDER BY e.created_at DESC, e.id ASC
            LIMIT :limit OFFSET :offset
            """
        )
        parameters = {"limit": limit, "offset": offset}
        with self._engine.connect() as connection:
            return _as_dicts(
                connection.execute(statement, parameters).mappings()
            )

    def get_extraction(self, document_id: str | UUID) -> dict | None:
        """Ekstrakcja dokumentu o podanym identyfikatorze albo ``None``."""
        statement = text(
            """
            SELECT e.id, e.document_id, e.run_id, e.class, e.schema_version,
                   e.payload, e.evidence, e.created_at, d.filename
            FROM extractions e
            LEFT JOIN documents d ON d.id = e.document_id
            WHERE e.document_id = :document_id
            ORDER BY e.created_at DESC
            """
        )
        parameters = {"document_id": str(document_id)}
        with self._engine.connect() as connection:
            row = connection.execute(statement, parameters).mappings().first()
        return dict(row) if row is not None else None

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """Lista przebiegów przetwarzania."""
        statement = text(
            """
            SELECT id, started_at, finished_at, status, duration_ms, documents_count
            FROM runs
            ORDER BY started_at DESC, id ASC
            LIMIT :limit OFFSET :offset
            """
        )
        parameters = {"limit": limit, "offset": offset}
        with self._engine.connect() as connection:
            return _as_dicts(connection.execute(statement, parameters).mappings())

    def list_tables(self) -> list[str]:
        """Nazwy tabel widocznych w schemacie ``public``."""
        statement = text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name ASC
            """
        )
        with self._engine.connect() as connection:
            return [row[0] for row in connection.execute(statement)]

    def list_columns(self, table_name: str) -> list[dict]:
        """Kolumny wskazanej tabeli wraz z typami i dopuszczalnością ``NULL``."""
        statement = text(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table_name
            ORDER BY ordinal_position ASC
            """
        )
        parameters = {"table_name": table_name}
        with self._engine.connect() as connection:
            return _as_dicts(connection.execute(statement, parameters).mappings())

    def applied_migrations(self) -> list[dict]:
        """Lista zastosowanych migracji wraz z czasem ich nałożenia."""
        statement = text(
            """
            SELECT version, applied_at
            FROM schema_migrations
            ORDER BY version ASC
            """
        )
        with self._engine.connect() as connection:
            return _as_dicts(connection.execute(statement).mappings())

    def run_select(self, sql: str) -> list[dict]:
        """Wykonuje zapytanie tylko do odczytu; mutacje są odrzucane."""
        _assert_read_only(sql)
        statement = text(sql)
        with self._engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            rows = connection.execute(statement).mappings().all()
        return _as_dicts(rows)
