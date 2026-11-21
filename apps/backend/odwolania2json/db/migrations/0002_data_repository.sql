-- Migracja 0002: tabele DataRepository (architektura §9, ADR-004).
-- SQLite trzyma metadane, zadania i stany; bajty PDF i artefakty leżą w katalogu
-- roboczym pod nieprzezroczystym storage_key. Identyfikatory i daty to tekst (UTC).

CREATE TABLE IF NOT EXISTS batches (
    id text NOT NULL PRIMARY KEY,
    created_at text NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS batch_documents (
    id text NOT NULL PRIMARY KEY,
    batch_id text NOT NULL REFERENCES batches (id),
    input_path text NOT NULL,
    sha256 text NOT NULL CHECK (length(sha256) = 64),
    size_bytes integer NOT NULL CHECK (size_bytes >= 0),
    storage_key text NOT NULL,
    created_at text NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Kolizja nazw wejścia w jednym wsadzie jest odrzucana.
    UNIQUE (batch_id, input_path),
    -- Klucz rodzica dla złożonego FK zadania: dokument musi należeć do wsadu zadania.
    UNIQUE (id, batch_id)
);

CREATE TABLE IF NOT EXISTS jobs (
    id text NOT NULL PRIMARY KEY,
    batch_id text NOT NULL REFERENCES batches (id),
    document_id text NOT NULL,
    run_id text NOT NULL UNIQUE,
    state text NOT NULL CHECK (state IN ('queued', 'running', 'done')),
    revision integer NOT NULL DEFAULT 0 CHECK (revision >= 0),
    created_at text NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id, batch_id) REFERENCES batch_documents (id, batch_id)
);

CREATE INDEX IF NOT EXISTS jobs_batch_id_idx ON jobs (batch_id);
CREATE INDEX IF NOT EXISTS jobs_document_id_idx ON jobs (document_id);

CREATE TABLE IF NOT EXISTS artifacts (
    id text NOT NULL PRIMARY KEY,
    run_id text NOT NULL REFERENCES jobs (run_id),
    stage text NOT NULL,
    schema_version text NOT NULL,
    sha256 text NOT NULL CHECK (length(sha256) = 64),
    media_type text NOT NULL,
    size_bytes integer NOT NULL CHECK (size_bytes >= 0),
    storage_key text NOT NULL,
    created_at text NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS artifacts_run_id_idx ON artifacts (run_id);

-- Artefakt jest niezmienny: poprawka oznacza nowy artefakt w nowym przebiegu.
CREATE TRIGGER IF NOT EXISTS artifacts_no_update BEFORE UPDATE ON artifacts
BEGIN
    SELECT RAISE(ABORT, 'artifact is immutable');
END;

CREATE TRIGGER IF NOT EXISTS artifacts_no_delete BEFORE DELETE ON artifacts
BEGIN
    SELECT RAISE(ABORT, 'artifact is immutable');
END;

-- Obecność wiersza oznacza zatwierdzenie przebiegu (commit_run); odczyt wyniku
-- widzi wyłącznie te wiersze.
CREATE TABLE IF NOT EXISTS run_results (
    run_id text NOT NULL PRIMARY KEY REFERENCES jobs (run_id),
    outcome text NOT NULL
        CHECK (outcome IN ('complete', 'partial', 'foreign', 'ambiguous', 'technical_error')),
    result_artifact_id text REFERENCES artifacts (id),
    evidence_artifact_id text REFERENCES artifacts (id),
    report_artifact_id text REFERENCES artifacts (id),
    manifest text NOT NULL CHECK (json_valid(manifest)),
    manifest_sha256 text NOT NULL CHECK (length(manifest_sha256) = 64),
    committed_at text NOT NULL DEFAULT CURRENT_TIMESTAMP
);
