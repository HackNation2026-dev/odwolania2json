"""Testy SQLite na izolowanych plikach; bez zewnętrznego serwera."""

import uuid

import pytest
from odwolania2json.db import migrate as migrator
from odwolania2json.db.repository import (
    DocumentRepository,
    ReadOnlySqlError,
    is_configured,
    normalize_url,
)
from sqlalchemy.exc import OperationalError

EXPECTED_TABLES = {"documents", "runs", "extractions", "schema_migrations"}


@pytest.fixture(autouse=True)
def database_url(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    return url


@pytest.fixture
def repository(database_url):
    """Repozytorium na czystej bazie testowej."""
    url = database_url
    migrator.migrate(url)
    repo = DocumentRepository(url)
    try:
        yield repo
    finally:
        repo.dispose()


@pytest.fixture
def clean_database(repository):
    """Baza po migracji z pustymi tabelami danych."""
    repository.run_select("SELECT 1")  # sprawdza, że baza odpowiada
    with repository.engine.begin() as connection:
        for table in ("extractions", "runs", "documents"):
            connection.exec_driver_sql(f"DELETE FROM {table}")  # noqa: S608 — stała lista tabel testowych.
    return repository


def test_migrate_creates_expected_tables(database_url):
    url = database_url
    migrator.migrate(url)
    repo = DocumentRepository(url)
    try:
        tables = set(repo.list_tables())
    finally:
        repo.dispose()
    assert EXPECTED_TABLES.issubset(tables)


def test_migrate_is_idempotent(database_url):
    url = database_url
    migrator.migrate(url)
    second = migrator.migrate(url)
    assert second == []


def test_migrate_reports_applied_versions(database_url):
    url = database_url
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
    clean_database.upsert_document(document_id=first_id, filename="odwolanie.pdf", sha256="d" * 64)
    clean_database.upsert_document(document_id=second_id, filename="przelew.pdf", sha256="e" * 64)
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
    clean_database.upsert_run(run_id=run_id, status="ok", documents_count=1, duration_ms=120)
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
    clean_database.upsert_document(document_id=document_id, filename="obcy.pdf", sha256="8" * 64)
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


def test_normalize_url_accepts_sqlite():
    assert normalize_url("sqlite:///test.db") == "sqlite:///test.db"


def test_is_configured_tells_about_empty_url():
    assert is_configured("sqlite:///test.db") is True
    assert is_configured(None) is False
    assert is_configured("") is False


# --- Runda poprawek 1: regresje dla C1, C2, I4, I5, I6 i M8 ---------------


def test_run_select_allows_select_from_documents(clean_database):
    """C1: słowo ``do`` wewnątrz ``documents`` nie może odrzucać odczytu."""
    rows = clean_database.run_select("SELECT * FROM documents")
    assert rows == []


def test_run_select_allows_columns_with_forbidden_words_inside(clean_database):
    """C1: ``created_at``, ``document_id``, ``source_path`` itd. to nie mutacje."""
    rows = clean_database.run_select(
        "SELECT id, created_at, source_path, size_bytes, sha256, has_text_layer FROM documents"
    )
    assert rows == []
    rows = clean_database.run_select("SELECT id, document_id, run_id, created_at FROM extractions")
    assert rows == []
    rows = clean_database.run_select("SELECT id, status, started_at, documents_count FROM runs")
    assert rows == []


def test_run_select_allows_count_aggregate(clean_database):
    """C1: ``count(*)`` zawiera ``count``, ale nie jest mutacją."""
    rows = clean_database.run_select("SELECT count(*) AS count FROM documents")
    assert rows == [{"count": 0}]


def test_run_select_still_rejects_mutation_with_word_boundary(clean_database):
    """C1: dopasowanie z granicą słowa nadal odrzuca ``DROP TABLE``."""
    with pytest.raises(ReadOnlySqlError):
        clean_database.run_select("DROP TABLE documents")


def test_run_select_reads_reserved_class_column(clean_database):
    """C2: kolumna ``class`` jest zarezerwowanym słowem i wymaga cudzysłowów."""
    rows = clean_database.run_select('SELECT "class" FROM extractions')
    assert rows == []


def test_repository_lists_extractions_with_reserved_class_column(clean_database):
    """C2: zapytania repozytorium cytują ``extractions."class"``."""
    run_id = uuid.uuid4()
    document_id = uuid.uuid4()
    clean_database.upsert_document(
        document_id=document_id, filename="odwolanie.pdf", sha256="7" * 64
    )
    clean_database.upsert_run(run_id=run_id, status="ok", documents_count=1)
    clean_database.upsert_extraction(
        extraction_id=uuid.uuid4(),
        document_id=document_id,
        run_id=run_id,
        document_class="odwolanie",
        schema_version="0.1.0",
        payload={"a": 1},
        evidence={},
    )
    extractions = clean_database.list_extractions()
    assert len(extractions) == 1
    assert extractions[0]["class"] == "odwolanie"
    assert clean_database.class_counts()[0]["class"] == "odwolanie"


def test_applied_versions_does_not_create_table_on_raw_database(tmp_path):
    """I6: ``applied_versions`` jest czystym odczytem — nie tworzy tabeli."""
    fresh_database = _fresh_database_name(tmp_path)

    try:
        assert migrator.applied_versions(_database_url_for_name(fresh_database)) == []
        assert not _table_exists(_database_url_for_name(fresh_database), "schema_migrations")
    finally:
        pass


def test_applied_versions_lists_applied_migrations(database_url):
    """I6: po migracji funkcja zwraca applied wersje."""
    url = database_url
    migrator.migrate(url)
    assert "0001_initial" in migrator.applied_versions(url)


def test_migrate_applies_whole_file_in_one_transaction(tmp_path):
    """I5: plik migracji wykonuje się jako całość, w jednej transakcji."""
    fresh_database = _fresh_database_name(tmp_path)

    url = _database_url_for_name(fresh_database)
    try:
        applied = migrator.migrate(url)
        assert applied == ["0001_initial", "0002_data_repository"]
        assert _table_exists(url, "documents")
        assert _table_exists(url, "runs")
        assert _table_exists(url, "extractions")
    finally:
        pass


def test_migrate_rolls_back_whole_file_on_error(tmp_path):
    """I5: błąd w pliku migracji cofa cały plik, nie tylko jego część."""
    fresh_database = _fresh_database_name(tmp_path)

    url = _database_url_for_name(fresh_database)
    directory = tmp_path / "migrations"
    directory.mkdir()
    try:
        (directory / "0001_calkowita.sql").write_text(
            "CREATE TABLE pilota (id int);\nSELECT nie_istniejaca_funkcja();\n",
            encoding="utf-8",
        )
        with pytest.raises(OperationalError):
            migrator.migrate_with_directory(url, directory)
        assert not _table_exists(url, "pilota")
    finally:
        pass


def test_list_documents_escapes_wildcards_in_name_filter(clean_database):
    """M8: znak ``_`` w nazwie pliku nie dopasowuje dowolnego znaku."""
    run_id = uuid.uuid4()
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    clean_database.upsert_run(run_id=run_id, status="ok", documents_count=2)
    clean_database.upsert_document(
        document_id=first_id, filename="odwolanie_a.pdf", sha256="1" * 64
    )
    clean_database.upsert_document(
        document_id=second_id, filename="odwolanieb.pdf", sha256="2" * 64
    )
    found = clean_database.list_documents(name_filter="odwolanie_a")
    assert [row["filename"] for row in found] == ["odwolanie_a.pdf"]


def test_list_documents_escapes_percent_in_name_filter(clean_database):
    """M8: znak ``%`` w nazwie pliku jest traktowany dosłownie."""
    document_id = uuid.uuid4()
    clean_database.upsert_document(
        document_id=document_id, filename="100%_wzorzec.pdf", sha256="3" * 64
    )
    found = clean_database.list_documents(name_filter="100%")
    assert [row["filename"] for row in found] == ["100%_wzorzec.pdf"]
    assert clean_database.list_documents(name_filter="100x") == []


def _database_url_for_name(name: str) -> str:
    return f"sqlite:///{name}"


def _fresh_database_name(tmp_path) -> str:
    return str(tmp_path / "fresh.db")


def _table_exists(database_url: str, table_name: str) -> bool:
    from odwolania2json.db.engine import create_database_engine
    from sqlalchemy import inspect

    engine = create_database_engine(database_url)
    try:
        return inspect(engine).has_table(table_name)
    finally:
        engine.dispose()


def test_repository_implements_catalog_repository(clean_database):
    from odwolania2json.db.repository import CatalogRepository

    assert isinstance(clean_database, CatalogRepository)


def test_list_documents_returns_real_bool_for_text_layer(clean_database):
    clean_database.upsert_document(uuid.uuid4(), "a.pdf", "4" * 64, has_text_layer=True)
    clean_database.upsert_document(uuid.uuid4(), "b.pdf", "5" * 64, has_text_layer=False)
    clean_database.upsert_document(uuid.uuid4(), "c.pdf", "6" * 64)
    by_name = {row["filename"]: row["has_text_layer"] for row in clean_database.list_documents()}
    assert by_name == {"a.pdf": True, "b.pdf": False, "c.pdf": None}
    assert all(value is None or type(value) is bool for value in by_name.values())


def test_normalize_url_rejects_non_sqlite_drivers():
    for url in ("postgresql://u:p@h/db", "postgresql+pg8000://h/db", "mysql://h/db"):
        with pytest.raises(ValueError, match="SQLite"):
            normalize_url(url)


def test_engine_enforces_foreign_keys_and_wal_for_file_database(clean_database):
    with clean_database.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert connection.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"


def test_foreign_keys_reject_missing_document_and_run(clean_database):
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        clean_database.upsert_extraction(
            extraction_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            run_id=uuid.uuid4(),
            document_class="obcy",
            schema_version="1",
            payload={},
            evidence={},
        )
    assert clean_database.count_extractions() == 0


def test_failed_read_does_not_leave_connection_query_only(clean_database):
    from sqlalchemy.exc import OperationalError

    with pytest.raises(OperationalError):
        clean_database.run_select("SELECT missing_column FROM documents")
    clean_database.upsert_document(uuid.uuid4(), "test.pdf", "a" * 64)
    assert clean_database.count_documents() == 1


def test_sql_migration_preserves_semicolons_and_rolls_back_version(tmp_path):
    directory = tmp_path / "migrations"
    directory.mkdir()
    (directory / "0001_test.sql").write_text(
        "CREATE TABLE example (value TEXT); INSERT INTO example VALUES ('a;b');"
    )
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    assert migrator.migrate_with_directory(url, directory) == ["0001_test"]
    repo = DocumentRepository(url)
    try:
        assert repo.run_select("SELECT value FROM example") == [{"value": "a;b"}]
    finally:
        repo.dispose()


def test_migrate_module_main_applies_and_skips(tmp_path, monkeypatch, capsys):
    url = f"sqlite:///{tmp_path / 'main.db'}"
    assert migrator.main(["--database-url", url]) == 0
    assert capsys.readouterr().out.split() == ["0001_initial", "0002_data_repository"]
    assert migrator.main(["--database-url", url]) == 0
    assert capsys.readouterr().out == ""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert migrator.main([]) == 0
    assert "pominięto" in capsys.readouterr().out
