"""Testy warstwy dostępu do bazy PostgreSQL.

Testy wymagają działającej bazy — bez ``DATABASE_URL`` są pomijane.
"""

import os
import uuid

import pytest

from odwolania2json.db import migrate as migrator
from odwolania2json.db.repository import (
    DocumentRepository,
    ReadOnlySqlError,
    is_configured,
    normalize_url,
)

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"), reason="brak DATABASE_URL"
)

EXPECTED_TABLES = {"documents", "runs", "extractions", "schema_migrations"}


@pytest.fixture()
def repository():
    """Repozytorium na czystej bazie testowej."""
    url = os.environ["DATABASE_URL"]
    migrator.migrate(url)
    repo = DocumentRepository(url)
    try:
        yield repo
    finally:
        repo.dispose()


@pytest.fixture()
def clean_database(repository):
    """Baza po migracji z pustymi tabelami danych."""
    repository.run_select("SELECT 1")  # sprawdza, że baza odpowiada
    with repository.engine.begin() as connection:
        for table in ("extractions", "runs", "documents"):
            connection.exec_driver_sql(f"DELETE FROM {table}")
    yield repository


def test_migrate_creates_expected_tables():
    url = os.environ["DATABASE_URL"]
    migrator.migrate(url)
    repo = DocumentRepository(url)
    try:
        tables = set(repo.list_tables())
    finally:
        repo.dispose()
    assert EXPECTED_TABLES.issubset(tables)


def test_migrate_is_idempotent():
    url = os.environ["DATABASE_URL"]
    migrator.migrate(url)
    second = migrator.migrate(url)
    assert second == []


def test_migrate_reports_applied_versions():
    url = os.environ["DATABASE_URL"]
    migrator.migrate(url)
    versions = migrator.applied_versions(url)
    assert "0001_initial" in versions


def test_applied_migrations_are_listed(clean_database):
    rows = clean_database.applied_migrations()
    assert rows
    assert "0001_initial" in {row["version"] for row in rows}


def test_upsert_document_is_idempotent_by_sha256(clean_database):
    sha256 = "a" * 64
    clean_database.upsert_document(
        document_id=uuid.uuid4(),
        filename="przyklad.pdf",
        sha256=sha256,
        size_bytes=1234,
        source_path="sprawa_01/przyklad.pdf",
        page_count=3,
        has_text_layer=True,
    )
    clean_database.upsert_document(
        document_id=uuid.uuid4(),
        filename="przyklad.pdf",
        sha256=sha256,
        size_bytes=1234,
        source_path="sprawa_01/przyklad.pdf",
        page_count=3,
        has_text_layer=True,
    )
    assert clean_database.count_documents() == 1


def test_upsert_document_updates_existing_row(clean_database):
    sha256 = "b" * 64
    document_id = uuid.uuid4()
    clean_database.upsert_document(
        document_id=document_id,
        filename="stara-nazwa.pdf",
        sha256=sha256,
        size_bytes=1,
    )
    clean_database.upsert_document(
        document_id=uuid.uuid4(),
        filename="nowa-nazwa.pdf",
        sha256=sha256,
        size_bytes=2,
    )
    documents = clean_database.list_documents()
    assert len(documents) == 1
    assert documents[0]["filename"] == "nowa-nazwa.pdf"
    assert documents[0]["size_bytes"] == 2


def test_upsert_run_and_extraction_are_counted(clean_database):
    run_id = uuid.uuid4()
    document_id = uuid.uuid4()
    clean_database.upsert_document(
        document_id=document_id,
        filename="odwolanie.pdf",
        sha256="c" * 64,
        size_bytes=10,
    )
    clean_database.upsert_run(
        run_id=run_id,
        status="ok",
        documents_count=1,
        duration_ms=250,
    )
    clean_database.upsert_extraction(
        extraction_id=uuid.uuid4(),
        document_id=document_id,
        run_id=run_id,
        document_class="odwolanie",
        schema_version="0.1.0",
        payload={"klucz": "wartosc"},
        evidence={"klucz": {"strona": 1, "fragment": "tekst"}},
    )
    assert clean_database.count_runs() == 1
    assert clean_database.count_extractions() == 1
    assert clean_database.class_counts()[0]["class"] == "odwolanie"
    assert clean_database.get_extraction(document_id) is not None
    assert clean_database.get_document(document_id) is not None


def test_list_documents_filters_by_name_and_class(clean_database):
    run_id = uuid.uuid4()
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    clean_database.upsert_run(run_id=run_id, status="ok", documents_count=2)
    clean_database.upsert_document(
        document_id=first_id, filename="odwolanie.pdf", sha256="d" * 64
    )
    clean_database.upsert_document(
        document_id=second_id, filename="przelew.pdf", sha256="e" * 64
    )
    clean_database.upsert_extraction(
        extraction_id=uuid.uuid4(),
        document_id=first_id,
        run_id=run_id,
        document_class="odwolanie",
        schema_version="0.1.0",
        payload={},
        evidence={},
    )
    assert len(clean_database.list_documents(name_filter="odwolanie")) == 1
    assert len(clean_database.list_documents(document_class="odwolanie")) == 1
    assert len(clean_database.list_documents(document_class="przelew")) == 0


def test_list_extractions_and_runs_return_rows(clean_database):
    run_id = uuid.uuid4()
    document_id = uuid.uuid4()
    clean_database.upsert_document(
        document_id=document_id,
        filename="odwolanie.pdf",
        sha256="9" * 64,
        size_bytes=10,
    )
    clean_database.upsert_run(
        run_id=run_id, status="ok", documents_count=1, duration_ms=120
    )
    clean_database.upsert_extraction(
        extraction_id=uuid.uuid4(),
        document_id=document_id,
        run_id=run_id,
        document_class="odwolanie",
        schema_version="0.1.0",
        payload={"klucz": "wartosc"},
        evidence={"klucz": {"strona": 1, "fragment": "tekst"}},
    )
    extractions = clean_database.list_extractions()
    assert len(extractions) == 1
    assert extractions[0]["filename"] == "odwolanie.pdf"
    assert extractions[0]["payload"] == {"klucz": "wartosc"}
    assert extractions[0]["evidence"] == {"klucz": {"strona": 1, "fragment": "tekst"}}
    runs = clean_database.list_runs()
    assert len(runs) == 1
    assert runs[0]["status"] == "ok"
    assert runs[0]["documents_count"] == 1


def test_list_columns_describes_table(clean_database):
    columns = clean_database.list_columns("documents")
    names = {column["column_name"] for column in columns}
    assert {"id", "filename", "sha256", "created_at"} <= names


def test_get_document_returns_none_for_unknown_id(clean_database):
    assert clean_database.get_document(uuid.uuid4()) is None


def test_upsert_extraction_accepts_payload_as_text(clean_database):
    run_id = uuid.uuid4()
    document_id = uuid.uuid4()
    clean_database.upsert_document(
        document_id=document_id, filename="obcy.pdf", sha256="8" * 64
    )
    clean_database.upsert_run(run_id=run_id, status="ok", documents_count=1)
    clean_database.upsert_extraction(
        extraction_id=uuid.uuid4(),
        document_id=document_id,
        run_id=run_id,
        document_class="obcy",
        schema_version="0.1.0",
        payload="{}",
        evidence={},
    )
    extraction = clean_database.get_extraction(document_id)
    assert extraction is not None
    assert extraction["payload"] == {}


def test_run_select_rejects_mutation(clean_database):
    before = clean_database.count_documents()
    with pytest.raises(ReadOnlySqlError):
        clean_database.run_select("DELETE FROM documents")
    assert clean_database.count_documents() == before


def test_run_select_rejects_comment_hidden_mutation(clean_database):
    with pytest.raises(ReadOnlySqlError):
        clean_database.run_select("-- komentarz\nDROP TABLE documents")


def test_run_select_returns_rows(clean_database):
    rows = clean_database.run_select("SELECT 1 AS x")
    assert rows == [{"x": 1}]


def test_run_select_allows_with_query(clean_database):
    rows = clean_database.run_select("WITH tabela AS (SELECT 2 AS y) SELECT y FROM tabela")
    assert rows == [{"y": 2}]


def test_normalize_url_switches_driver():
    assert normalize_url("postgresql://u:p@h:5432/d") == (
        "postgresql+pg8000://u:p@h:5432/d"
    )


def test_is_configured_tells_about_empty_url():
    assert is_configured("postgresql://u:p@h/d") is True
    assert is_configured(None) is False
    assert is_configured("") is False
