"""Katalog dokumentów, przebiegów i ekstrakcji (odczyty panelu) w SQLite.

Interfejs ``DataRepository`` z architektury §9 jest w ``data_repository.py``;
tu żyje starszy, prostszy katalog ekstrakcji (``CatalogRepository``).

Warstwa jest opcjonalna: bez ``DATABASE_URL`` nic nie powstaje i aplikacja
działa dalej. Zapisy idą wyłącznie przez parametry nazwane (``text()`` z
parametrami), nigdy przez sklejanie SQL-u ze stringów.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Protocol, cast, runtime_checkable
from uuid import UUID

from pydantic import JsonValue, TypeAdapter
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.sql.elements import TextClause

from .engine import create_database_engine, normalize_url, write_transaction

__all__ = [
    "CatalogRepository",
    "DocumentRepository",
    "ReadOnlySqlError",
    "is_configured",
    "normalize_url",
]

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
        # Granica słowa: „do” w „documents” i „create” w „created_at”
        # to fragmenty nazw, a nie polecenia zmieniające dane.
        if re.search(rf"\b{keyword}\b", lowered):
            raise ReadOnlySqlError(f"Zapytanie zawiera niedozwolone słowo: {keyword.upper()}.")


def _escape_like(value: str) -> str:
    """Escapuje znaki wieloznaczne ``LIKE`` (``%``, ``_``) i znak ucieczki.

    Używana w zapytaniu z ``ESCAPE '\\'``, żeby nazwa pliku z ``_`` lub ``%``
    była traktowana dosłownie, a nie jako wzorzec.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _json_value(value: JsonValue) -> str:
    """Waliduje granicę JSON przed zapisem do SQLite."""
    adapter: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
    if isinstance(value, (str, bytes)):
        try:
            return adapter.dump_json(adapter.validate_json(value)).decode("utf-8")
        except ValueError:
            pass
    validated = adapter.validate_python(value)
    return json.dumps(validated, ensure_ascii=False, sort_keys=True)


def _as_dicts(rows: Iterable[RowMapping]) -> list[dict[str, object]]:
    """Zamienia wiersze ``RowMapping`` na listę zwykłych słowników."""
    result = [dict(row) for row in rows]
    for row in result:
        for key in ("payload", "evidence"):
            value = row.get(key)
            if isinstance(value, str):
                row[key] = TypeAdapter(JsonValue).validate_json(value)
        flag = row.get("has_text_layer")
        if isinstance(flag, int):
            # SQLite przechowuje bool jako 0/1; API zwraca prawdziwy bool.
            row["has_text_layer"] = bool(flag)
    return result


@runtime_checkable
class CatalogRepository(Protocol):
    """Granica katalogu ekstrakcji dla panelu i CLI."""

    @property
    def engine(self) -> Engine: ...

    def dispose(self) -> None: ...

    def upsert_document(
        self,
        document_id: str | UUID,
        filename: str,
        sha256: str,
        size_bytes: int | None = None,
        source_path: str | None = None,
        page_count: int | None = None,
        has_text_layer: bool | None = None,
    ) -> None: ...

    def upsert_run(
        self,
        run_id: str | UUID,
        status: str,
        documents_count: int = 0,
        duration_ms: int | None = None,
    ) -> None: ...

    def upsert_extraction(
        self,
        extraction_id: str | UUID,
        document_id: str | UUID,
        run_id: str | UUID,
        document_class: str,
        schema_version: str,
        payload: JsonValue,
        evidence: JsonValue,
    ) -> None: ...

    def count_documents(self) -> int: ...

    def count_extractions(self) -> int: ...

    def count_runs(self) -> int: ...

    def class_counts(self) -> list[dict[str, object]]: ...

    def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        name_filter: str | None = None,
        document_class: str | None = None,
    ) -> list[dict[str, object]]: ...

    def get_document(self, document_id: str | UUID) -> dict[str, object] | None: ...

    def list_extractions(self, limit: int = 50, offset: int = 0) -> list[dict[str, object]]: ...

    def get_extraction(self, document_id: str | UUID) -> dict[str, object] | None: ...

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[dict[str, object]]: ...

    def list_tables(self) -> list[str]: ...

    def list_columns(self, table_name: str) -> list[dict[str, object]]: ...

    def applied_migrations(self) -> list[dict[str, object]]: ...

    def run_select(self, sql: str) -> list[dict[str, object]]: ...


class DocumentRepository(CatalogRepository):
    """Dostęp do dokumentów, przebiegów i ekstrakcji zapisanych w SQLite."""

    def __init__(self, database_url: str) -> None:
        """Tworzy repozytorium dla podanego adresu bazy."""
        if not is_configured(database_url):
            raise ValueError("Adres bazy jest pusty — repozytorium nie powstaje.")
        self.database_url = database_url
        self._engine: Engine = create_database_engine(database_url)

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
        with write_transaction(self._engine) as connection:
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
                finished_at = CURRENT_TIMESTAMP
            """
        )
        parameters = {
            "id": str(run_id),
            "status": status,
            "documents_count": documents_count,
            "duration_ms": duration_ms,
        }
        with write_transaction(self._engine) as connection:
            connection.execute(statement, parameters)

    def upsert_extraction(
        self,
        extraction_id: str | UUID,
        document_id: str | UUID,
        run_id: str | UUID,
        document_class: str,
        schema_version: str,
        payload: JsonValue,
        evidence: JsonValue,
    ) -> None:
        """Wstawia ekstrakcję albo aktualizuje istniejącą o tym samym identyfikatorze."""
        # „class” jest słowem zarezerwowanym w SQL, więc identyfikator jest cytowany.
        statement = text(
            """
            INSERT INTO extractions (id, document_id, run_id, "class", schema_version,
                                     payload, evidence)
            VALUES (:id, :document_id, :run_id, :document_class, :schema_version,
                    :payload, :evidence)
            ON CONFLICT (id) DO UPDATE SET
                document_id = EXCLUDED.document_id,
                run_id = EXCLUDED.run_id,
                "class" = EXCLUDED."class",
                schema_version = EXCLUDED.schema_version,
                payload = EXCLUDED.payload,
                evidence = EXCLUDED.evidence
            """
        )
        parameters = {
            "id": str(extraction_id),
            "document_id": str(document_id),
            "run_id": str(run_id),
            "document_class": document_class,
            "schema_version": schema_version,
            "payload": _json_value(payload),
            "evidence": _json_value(evidence),
        }
        with write_transaction(self._engine) as connection:
            connection.execute(statement, parameters)

    # -- odczyty ------------------------------------------------------------

    def _scalar(self, statement: TextClause) -> object:
        """Wykonuje zapytanie zwracające pojedynczą wartość."""
        with self._engine.connect() as connection:
            return connection.execute(statement).scalar()

    def count_documents(self) -> int:
        """Liczba dokumentów w bazie."""
        return int(cast(int, self._scalar(text("SELECT count(*) FROM documents"))) or 0)

    def count_extractions(self) -> int:
        """Liczba ekstrakcji w bazie."""
        return int(cast(int, self._scalar(text("SELECT count(*) FROM extractions"))) or 0)

    def count_runs(self) -> int:
        """Liczba przebiegów w bazie."""
        return int(cast(int, self._scalar(text("SELECT count(*) FROM runs"))) or 0)

    def class_counts(self) -> list[dict[str, object]]:
        """Rozkład ekstrakcji według klas dokumentów."""
        # „class” jest słowem zarezerwowanym w SQL, więc identyfikator jest cytowany.
        statement = text(
            """
            SELECT "class", count(*) AS count
            FROM extractions
            GROUP BY "class"
            ORDER BY count DESC, "class" ASC
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
    ) -> list[dict[str, object]]:
        """Lista dokumentów z opcjonalnym filtrem po nazwie i klasie."""
        # Warunki składane są ze stałych wariantów SQL — nie ma tu sklejania
        # danych wejściowych z tekstem zapytania.
        conditions: list[str] = []
        parameters: dict[str, object] = {"limit": limit, "offset": offset}
        if name_filter:
            conditions.append("d.filename LIKE :name_pattern ESCAPE :escape")
            parameters["name_pattern"] = f"%{_escape_like(name_filter)}%"
            parameters["escape"] = "\\"
        if document_class:
            conditions.append('e."class" = :document_class')
            parameters["document_class"] = document_class
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        statement = text(
            f"""
            SELECT d.id, d.filename, d.sha256, d.size_bytes, d.source_path,
                   d.page_count, d.has_text_layer, d.created_at,
                   e."class" AS document_class
            FROM documents d
            LEFT JOIN extractions e ON e.document_id = d.id
            {where}
            ORDER BY d.created_at DESC, d.filename ASC
            LIMIT :limit OFFSET :offset
            """  # noqa: S608 — warunki są stałe, dane przekazujemy parametrami.
        )
        with self._engine.connect() as connection:
            return _as_dicts(connection.execute(statement, parameters).mappings())

    def get_document(self, document_id: str | UUID) -> dict[str, object] | None:
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
        return _as_dicts([row])[0] if row is not None else None

    def list_extractions(self, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
        """Lista ekstrakcji z podsumowaniem dokumentu."""
        statement = text(
            """
            SELECT e.id, e.document_id, e.run_id, e."class", e.schema_version,
                   e.payload, e.evidence, e.created_at, d.filename
            FROM extractions e
            LEFT JOIN documents d ON d.id = e.document_id
            ORDER BY e.created_at DESC, e.id ASC
            LIMIT :limit OFFSET :offset
            """
        )
        parameters = {"limit": limit, "offset": offset}
        with self._engine.connect() as connection:
            return _as_dicts(connection.execute(statement, parameters).mappings())

    def get_extraction(self, document_id: str | UUID) -> dict[str, object] | None:
        """Ekstrakcja dokumentu o podanym identyfikatorze albo ``None``."""
        statement = text(
            """
            SELECT e.id, e.document_id, e.run_id, e."class", e.schema_version,
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
        return _as_dicts([row])[0] if row is not None else None

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
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
        """Nazwy tabel przez publiczne API inspekcji SQLAlchemy."""
        return inspect(self._engine).get_table_names()

    def list_columns(self, table_name: str) -> list[dict[str, object]]:
        """Kolumny w formacie istniejącego interfejsu panelu."""
        inspector = inspect(self._engine)
        if not inspector.has_table(table_name):
            return []
        return [
            {
                "column_name": column["name"],
                "data_type": str(column["type"]),
                "is_nullable": "YES" if column["nullable"] else "NO",
                "column_default": column["default"],
            }
            for column in inspector.get_columns(table_name)
        ]

    def applied_migrations(self) -> list[dict[str, object]]:
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

    def run_select(self, sql: str) -> list[dict[str, object]]:
        """Wykonuje zapytanie tylko do odczytu; mutacje są odrzucane."""
        _assert_read_only(sql)
        statement = text(sql)
        with self._engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA query_only=ON")
            try:
                rows = connection.execute(statement).mappings().all()
            finally:
                connection.exec_driver_sql("PRAGMA query_only=OFF")
        return _as_dicts(rows)
