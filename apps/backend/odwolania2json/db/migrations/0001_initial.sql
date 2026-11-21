-- Migracja 0001: schemat podstawowy — dokumenty, przebiegi i ekstrakcje.
-- Plik nakładany idempotentnie: każda tabela używa CREATE TABLE IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS documents (
    id text NOT NULL PRIMARY KEY,
    filename text NOT NULL,
    sha256 text NOT NULL UNIQUE,
    size_bytes bigint,
    source_path text,
    page_count int,
    has_text_layer bool,
    created_at text NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS documents_sha256_idx ON documents (sha256);

CREATE TABLE IF NOT EXISTS runs (
    id text NOT NULL PRIMARY KEY,
    started_at text NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at text,
    status text NOT NULL,
    duration_ms int,
    documents_count int NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS extractions (
    id text NOT NULL PRIMARY KEY,
    document_id text NOT NULL REFERENCES documents (id),
    run_id text NOT NULL REFERENCES runs (id),
    "class" text NOT NULL,
    schema_version text NOT NULL,
    payload text NOT NULL CHECK (json_valid(payload)),
    evidence text NOT NULL CHECK (json_valid(evidence)),
    created_at text NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS extractions_document_id_idx ON extractions (document_id);
