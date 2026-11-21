"""``DataRepository`` z architektury §9 oraz implementacja v1 na SQLAlchemy + SQLite.

Metadane, zadania i stany leżą w SQLite (ADR-004), a bajty PDF i artefakty w
katalogu roboczym pod nieprzezroczystym ``storage_key``. Silnik zna wyłącznie
interfejs; SQL i ścieżki są szczegółem ``SqliteDataRepository``.

Gwarancje:

* ``claim_job``/``update_job`` zmieniają stan tylko przy zgodnej rewizji
  (jeden wykonawca; konflikt odrzuca zapis);
* ``commit_run`` zatwierdza manifest, wynik i stan końcowy w jednej transakcji
  po sprawdzeniu skrótów wszystkich artefaktów przebiegu;
* ``get_result`` widzi wyłącznie zatwierdzone przebiegi;
* ``recover_after_restart`` oznacza przerwane ``running`` jako
  ``done/technical_error`` z raportem przerwania i uzgadnia indeks z dyskiem.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, NoReturn, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints, TypeAdapter
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from .engine import create_database_engine, write_transaction

__all__ = [
    "AlreadyExistsError",
    "Artifact",
    "Batch",
    "DataRepository",
    "Document",
    "IntegrityViolationError",
    "InvalidTransitionError",
    "Job",
    "JobState",
    "NotFoundError",
    "Outcome",
    "RecoveryReport",
    "RepositoryError",
    "Result",
    "RevisionConflictError",
    "RunSummary",
    "SqliteDataRepository",
]

Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
JobState = Literal["queued", "running", "done"]
Outcome = Literal["complete", "partial", "foreign", "ambiguous", "technical_error"]

#: Dozwolone przejścia stanu zadania; ``done`` wymaga zatwierdzonego wyniku.
_TRANSITIONS: Mapping[JobState, frozenset[JobState]] = {
    "queued": frozenset({"running"}),
    "running": frozenset({"done"}),
    "done": frozenset(),
}

_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_TMP_SUFFIX = ".tmp"
_MANIFEST_NAME = "manifest.json"


class RepositoryError(RuntimeError):
    """Bazowy błąd repozytorium danych."""


class NotFoundError(RepositoryError):
    """Rekord nie istnieje."""


class AlreadyExistsError(RepositoryError):
    """Rekord o tym identyfikatorze lub kluczu naturalnym już istnieje."""


class RevisionConflictError(RepositoryError):
    """Rewizja zadania różni się od oczekiwanej; zapis odrzucono."""


class InvalidTransitionError(RepositoryError):
    """Zmiana stanu niezgodna z modelem wykonania."""


class IntegrityViolationError(RepositoryError):
    """Bajty na dysku nie zgadzają się z zapisanym skrótem albo brakuje pliku."""


class _Record(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Batch(_Record):
    """Wsad: niezależne zadania zarejestrowane razem."""

    id: Identifier
    created_at: str | None = None
    job_ids: tuple[str, ...] = ()


class Document(_Record):
    """Dokument wejściowy; ``input_path`` to względna nazwa wejścia."""

    id: Identifier
    batch_id: Identifier
    input_path: str = Field(min_length=1, max_length=1024)
    sha256: Sha256 | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    storage_key: str | None = None


class Job(_Record):
    """Zadanie przetwarzania jednego dokumentu w jednej próbie (``run_id``)."""

    id: Identifier
    batch_id: Identifier
    document_id: Identifier
    run_id: Identifier
    state: JobState = "queued"
    revision: int = Field(default=0, ge=0)


class Artifact(_Record):
    """Niezmienny artefakt przebiegu."""

    id: Identifier
    run_id: Identifier
    stage: Identifier
    schema_version: str = Field(min_length=1, max_length=64)
    media_type: str = Field(min_length=1, max_length=255)
    sha256: Sha256 | None = None
    storage_key: str | None = None


class Result(_Record):
    """Zatwierdzony wynik przebiegu; referencje są ``None``, gdy artefakt nie powstał."""

    run_id: Identifier
    outcome: Outcome
    result_artifact_id: Identifier | None = None
    evidence_artifact_id: Identifier | None = None
    report_artifact_id: Identifier | None = None
    committed_at: str | None = None


class RunSummary(_Record):
    """Pozycja jawnej historii przebiegów dokumentu."""

    run_id: str
    job_id: str
    document_id: str
    state: JobState
    outcome: Outcome | None
    revision: int


class RecoveryReport(_Record):
    """Skutki uzgodnienia po restarcie."""

    interrupted_run_ids: tuple[str, ...] = ()
    inconsistent_run_ids: tuple[str, ...] = ()
    removed_temp_files: int = 0


@runtime_checkable
class DataRepository(Protocol):
    """Granica trwałości dla silnika, CLI i API (architektura §9)."""

    def create_batch(self, batch: Batch) -> Batch: ...

    def get_batch(self, batch_id: str) -> Batch | None: ...

    def put_document(self, document: Document, content: bytes) -> Document: ...

    def get_document(self, document_id: str) -> Document | None: ...

    def open_document(self, document_id: str) -> bytes: ...

    def create_job(self, job: Job) -> Job: ...

    def get_job(self, job_id: str) -> Job | None: ...

    def list_jobs(self, batch_id: str) -> list[Job]: ...

    def claim_job(self, job_id: str, expected_revision: int) -> Job: ...

    def update_job(self, job_id: str, state: JobState, expected_revision: int) -> Job: ...

    def put_artifact(self, run_id: str, artifact: Artifact, content: bytes) -> Artifact: ...

    def open_artifact(self, artifact_id: str) -> bytes: ...

    def commit_run(
        self, run_id: str, manifest: JsonValue, result: Result, state: Literal["done"] = "done"
    ) -> Result: ...

    def get_result(self, run_id: str) -> Result | None: ...

    def get_manifest(self, run_id: str) -> JsonValue | None: ...

    def list_runs(self, document_id: str) -> list[RunSummary]: ...

    def recover_after_restart(self) -> RecoveryReport: ...

    def dispose(self) -> None: ...


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_json(value: JsonValue) -> str:
    """Kanoniczny JSON (posortowane klucze) po walidacji granicy pydantic."""
    validated = _JSON.validate_python(value)
    return json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fsync_directory(directory: Path) -> None:
    """Utrwala zamianę nazwy; na platformach bez otwierania katalogu pomija krok."""
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, content: bytes) -> None:
    """Plik tymczasowy w tym samym katalogu, ``fsync``, atomowa zamiana celu."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{os.urandom(4).hex()}{_TMP_SUFFIX}")
    try:
        with temporary.open("wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    _fsync_directory(path.parent)


def _validate_input_path(input_path: str) -> str:
    """Odrzuca ścieżki bezwzględne, ``..`` i separatory Windows przed jakąkolwiek pracą."""
    if "\\" in input_path or "\x00" in input_path:
        raise ValueError("Ścieżka wejścia zawiera niedozwolone znaki.")
    # Części liczymy z surowego tekstu: PurePosixPath po cichu gubi „.” i puste człony.
    if input_path.startswith("/") or any(part in {"", ".", ".."} for part in input_path.split("/")):
        raise ValueError("Ścieżka wejścia musi być względna, bez „.”, „..” i pustych członów.")
    if re.match(r"^[A-Za-z]:", input_path):
        raise ValueError("Ścieżka wejścia nie może zawierać litery dysku.")
    return input_path


class SqliteDataRepository:
    """Implementacja v1: SQLite przez SQLAlchemy + katalog roboczy na dysku."""

    def __init__(self, database_url: str, work_dir: Path) -> None:
        self._engine: Engine = create_database_engine(database_url)
        self._work_dir = work_dir

    @property
    def engine(self) -> Engine:
        """Silnik SQLAlchemy (testy i diagnostyka)."""
        return self._engine

    def dispose(self) -> None:
        """Zamyka pulę połączeń."""
        self._engine.dispose()

    # -- ścieżki -------------------------------------------------------------

    def _path(self, storage_key: str) -> Path:
        return self._work_dir.joinpath(*PurePosixPath(storage_key).parts)

    @staticmethod
    def _document_key(batch_id: str, document_id: str) -> str:
        return f"{batch_id}/documents/{document_id}/input.pdf"

    @staticmethod
    def _artifact_key(batch_id: str, document_id: str, run_id: str, artifact_id: str) -> str:
        return f"{batch_id}/documents/{document_id}/runs/{run_id}/artifacts/{artifact_id}"

    @staticmethod
    def _manifest_key(batch_id: str, document_id: str, run_id: str) -> str:
        return f"{batch_id}/documents/{document_id}/runs/{run_id}/{_MANIFEST_NAME}"

    def _read_verified(self, storage_key: str, sha256: str, label: str) -> bytes:
        try:
            content = self._path(storage_key).read_bytes()
        except FileNotFoundError as error:
            raise IntegrityViolationError(f"Brak pliku: {label}.") from error
        if _sha256(content) != sha256:
            raise IntegrityViolationError(f"Skrót nie zgadza się z zapisanym: {label}.")
        return content

    # -- wsady ---------------------------------------------------------------

    def create_batch(self, batch: Batch) -> Batch:
        """Rejestruje pusty wsad; lista zadań powstaje przez ``create_job``."""
        try:
            with write_transaction(self._engine) as connection:
                connection.execute(text("INSERT INTO batches (id) VALUES (:id)"), {"id": batch.id})
        except IntegrityError as error:
            raise AlreadyExistsError(f"Wsad już istnieje: {batch.id}.") from error
        stored = self.get_batch(batch.id)
        if stored is None:  # pragma: no cover - zatwierdzony wiersz musi być widoczny
            raise RepositoryError("Wsad zniknął po zatwierdzeniu.")
        return stored

    def get_batch(self, batch_id: str) -> Batch | None:
        """Wsad z identyfikatorami jego zadań albo ``None``."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text("SELECT id, created_at FROM batches WHERE id = :id"), {"id": batch_id}
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            jobs = connection.execute(
                text("SELECT id FROM jobs WHERE batch_id = :id ORDER BY rowid"), {"id": batch_id}
            )
            job_ids = tuple(str(item[0]) for item in jobs)
        return Batch(id=row["id"], created_at=row["created_at"], job_ids=job_ids)

    # -- dokumenty -----------------------------------------------------------

    def put_document(self, document: Document, content: bytes) -> Document:
        """Zapisuje niezmienne bajty PDF; skrót liczy repozytorium, deklaracja musi się zgadzać."""
        input_path = _validate_input_path(document.input_path)
        digest = _sha256(content)
        if document.sha256 is not None and document.sha256 != digest:
            raise IntegrityViolationError("Deklarowany skrót dokumentu nie zgadza się z bajtami.")
        key = self._document_key(document.batch_id, document.id)
        try:
            with write_transaction(self._engine) as connection:
                # Wiersz trafia do bazy przed plikiem: kolizja id/nazwy kończy się
                # błędem, zanim cokolwiek na dysku zostanie nadpisane.
                connection.execute(
                    text(
                        """
                        INSERT INTO batch_documents
                            (id, batch_id, input_path, sha256, size_bytes, storage_key)
                        VALUES (:id, :batch_id, :input_path, :sha256, :size_bytes, :storage_key)
                        """
                    ),
                    {
                        "id": document.id,
                        "batch_id": document.batch_id,
                        "input_path": input_path,
                        "sha256": digest,
                        "size_bytes": len(content),
                        "storage_key": key,
                    },
                )
                _atomic_write(self._path(key), content)
        except IntegrityError as error:
            self._raise_for_integrity(error, "dokument", document.id)
        return document.model_copy(
            update={
                "input_path": input_path,
                "sha256": digest,
                "size_bytes": len(content),
                "storage_key": key,
            }
        )

    def get_document(self, document_id: str) -> Document | None:
        """Metadane dokumentu albo ``None``."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT id, batch_id, input_path, sha256, size_bytes, storage_key "
                        "FROM batch_documents WHERE id = :id"
                    ),
                    {"id": document_id},
                )
                .mappings()
                .first()
            )
        return None if row is None else Document(**dict(row))

    def open_document(self, document_id: str) -> bytes:
        """Bajty dokumentu po sprawdzeniu skrótu."""
        document = self.get_document(document_id)
        if document is None or document.storage_key is None or document.sha256 is None:
            raise NotFoundError(f"Brak dokumentu: {document_id}.")
        return self._read_verified(document.storage_key, document.sha256, f"dokument {document_id}")

    # -- zadania -------------------------------------------------------------

    def create_job(self, job: Job) -> Job:
        """Rejestruje zadanie w stanie ``queued`` z rewizją 0; odczyt nie uruchamia pracy."""
        if job.state != "queued" or job.revision != 0:
            raise InvalidTransitionError("Nowe zadanie ma stan queued i rewizję 0.")
        try:
            with write_transaction(self._engine) as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO jobs (id, batch_id, document_id, run_id, state, revision)
                        VALUES (:id, :batch_id, :document_id, :run_id, 'queued', 0)
                        """
                    ),
                    job.model_dump(),
                )
        except IntegrityError as error:
            self._raise_for_integrity(error, "zadanie", job.id)
        return job

    def get_job(self, job_id: str) -> Job | None:
        """Zadanie albo ``None``."""
        with self._engine.connect() as connection:
            return self._select_job(connection, "id", job_id)

    def list_jobs(self, batch_id: str) -> list[Job]:
        """Zadania wsadu w kolejności utworzenia."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id, batch_id, document_id, run_id, state, revision "
                    "FROM jobs WHERE batch_id = :id ORDER BY rowid"
                ),
                {"id": batch_id},
            ).mappings()
            return [Job(**dict(row)) for row in rows]

    def claim_job(self, job_id: str, expected_revision: int) -> Job:
        """Atomowo przejmuje zadanie ``queued``; inna rewizja oznacza konflikt."""
        return self._transition(job_id, "running", expected_revision)

    def update_job(self, job_id: str, state: JobState, expected_revision: int) -> Job:
        """Zmienia stan zgodnie z tabelą przejść i rewizją; ``done`` wymaga ``commit_run``."""
        return self._transition(job_id, state, expected_revision)

    def _transition(self, job_id: str, state: JobState, expected_revision: int) -> Job:
        with write_transaction(self._engine) as connection:
            current = self._select_job(connection, "id", job_id)
            if current is None:
                raise NotFoundError(f"Brak zadania: {job_id}.")
            if current.revision != expected_revision:
                raise RevisionConflictError(
                    f"Rewizja {job_id}: jest {current.revision}, oczekiwano {expected_revision}."
                )
            if state not in _TRANSITIONS[current.state]:
                raise InvalidTransitionError(f"Niedozwolone przejście {current.state} → {state}.")
            if state == "done" and not self._has_result(connection, current.run_id):
                raise InvalidTransitionError("Stan done ustawia wyłącznie commit_run.")
            return self._set_state(connection, current, state)

    @staticmethod
    def _set_state(connection: Connection, current: Job, state: JobState) -> Job:
        changed = connection.execute(
            text(
                "UPDATE jobs SET state = :state, revision = revision + 1 "
                "WHERE id = :id AND revision = :revision"
            ),
            {"state": state, "id": current.id, "revision": current.revision},
        )
        if changed.rowcount != 1:  # pragma: no cover - blokada zapisu wyklucza wyścig
            raise RevisionConflictError(f"Zadanie {current.id} zmienione równolegle.")
        return current.model_copy(update={"state": state, "revision": current.revision + 1})

    @staticmethod
    def _select_job(
        connection: Connection, column: Literal["id", "run_id"], value: str
    ) -> Job | None:
        # Nazwa kolumny pochodzi z literału typu, nie z danych wejściowych.
        statement = text(
            "SELECT id, batch_id, document_id, run_id, state, revision "  # noqa: S608
            f"FROM jobs WHERE {column} = :value"
        )
        row = connection.execute(statement, {"value": value}).mappings().first()
        return None if row is None else Job(**dict(row))

    @staticmethod
    def _has_result(connection: Connection, run_id: str) -> bool:
        return (
            connection.execute(
                text("SELECT 1 FROM run_results WHERE run_id = :run_id"), {"run_id": run_id}
            ).first()
            is not None
        )

    # -- artefakty -----------------------------------------------------------

    def put_artifact(self, run_id: str, artifact: Artifact, content: bytes) -> Artifact:
        """Zapisuje niezmienny artefakt przebiegu running; niepełny zapis jest niewidoczny."""
        if artifact.run_id != run_id:
            raise ValueError("Artefakt należy do innego przebiegu niż run_id.")
        with write_transaction(self._engine) as connection:
            job = self._select_job(connection, "run_id", run_id)
            if job is None:
                raise NotFoundError(f"Brak przebiegu: {run_id}.")
            if job.state != "running":
                raise InvalidTransitionError("Artefakty zapisuje wyłącznie przebieg running.")
            return self._store_artifact(connection, job, artifact, content)

    def _store_artifact(
        self, connection: Connection, job: Job, artifact: Artifact, content: bytes
    ) -> Artifact:
        digest = _sha256(content)
        if artifact.sha256 is not None and artifact.sha256 != digest:
            raise IntegrityViolationError("Deklarowany skrót artefaktu nie zgadza się z bajtami.")
        key = self._artifact_key(job.batch_id, job.document_id, job.run_id, artifact.id)
        try:
            connection.execute(
                text(
                    """
                    INSERT INTO artifacts
                        (id, run_id, stage, schema_version, sha256, media_type,
                         size_bytes, storage_key)
                    VALUES (:id, :run_id, :stage, :schema_version, :sha256, :media_type,
                            :size_bytes, :storage_key)
                    """
                ),
                {
                    "id": artifact.id,
                    "run_id": job.run_id,
                    "stage": artifact.stage,
                    "schema_version": artifact.schema_version,
                    "sha256": digest,
                    "media_type": artifact.media_type,
                    "size_bytes": len(content),
                    "storage_key": key,
                },
            )
        except IntegrityError as error:
            self._raise_for_integrity(error, "artefakt", artifact.id)
        _atomic_write(self._path(key), content)
        return artifact.model_copy(update={"sha256": digest, "storage_key": key})

    def open_artifact(self, artifact_id: str) -> bytes:
        """Bajty artefaktu po sprawdzeniu skrótu."""
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT sha256, storage_key FROM artifacts WHERE id = :id"),
                {"id": artifact_id},
            ).first()
        if row is None:
            raise NotFoundError(f"Brak artefaktu: {artifact_id}.")
        return self._read_verified(str(row[1]), str(row[0]), f"artefakt {artifact_id}")

    # -- zatwierdzanie i odczyt wyników -------------------------------------

    def commit_run(
        self, run_id: str, manifest: JsonValue, result: Result, state: Literal["done"] = "done"
    ) -> Result:
        """Atomowo zatwierdza manifest, wynik i stan ``done`` po sprawdzeniu artefaktów."""
        if state != "done":
            raise InvalidTransitionError("commit_run ustawia wyłącznie stan done.")
        if result.run_id != run_id:
            raise ValueError("Wynik należy do innego przebiegu niż run_id.")
        manifest_text = _canonical_json(manifest)
        with write_transaction(self._engine) as connection:
            job = self._select_job(connection, "run_id", run_id)
            if job is None:
                raise NotFoundError(f"Brak przebiegu: {run_id}.")
            if self._has_result(connection, run_id):
                raise AlreadyExistsError(f"Przebieg {run_id} jest już zatwierdzony.")
            if job.state != "running":
                raise InvalidTransitionError("Zatwierdzić można wyłącznie przebieg running.")
            self._verify_run_artifacts(connection, run_id, result)
            return self._commit(connection, job, manifest_text, result)

    def _verify_run_artifacts(self, connection: Connection, run_id: str, result: Result) -> None:
        rows = connection.execute(
            text("SELECT id, sha256, storage_key FROM artifacts WHERE run_id = :run_id"),
            {"run_id": run_id},
        ).all()
        known = {str(row[0]) for row in rows}
        referenced = (
            result.result_artifact_id,
            result.evidence_artifact_id,
            result.report_artifact_id,
        )
        for artifact_id in referenced:
            if artifact_id is not None and artifact_id not in known:
                raise IntegrityViolationError(
                    f"Wynik wskazuje artefakt spoza przebiegu: {artifact_id}."
                )
        for row in rows:
            self._read_verified(str(row[2]), str(row[1]), f"artefakt {row[0]}")

    def _commit(
        self, connection: Connection, job: Job, manifest_text: str, result: Result
    ) -> Result:
        """Manifest na dysk, wiersze w bieżącej transakcji; widoczne dopiero po jej commit."""
        manifest_bytes = manifest_text.encode("utf-8")
        _atomic_write(
            self._path(self._manifest_key(job.batch_id, job.document_id, job.run_id)),
            manifest_bytes,
        )
        connection.execute(
            text(
                """
                INSERT INTO run_results
                    (run_id, outcome, result_artifact_id, evidence_artifact_id,
                     report_artifact_id, manifest, manifest_sha256)
                VALUES (:run_id, :outcome, :result_artifact_id, :evidence_artifact_id,
                        :report_artifact_id, :manifest, :manifest_sha256)
                """
            ),
            {
                **result.model_dump(exclude={"committed_at"}),
                "manifest": manifest_text,
                "manifest_sha256": _sha256(manifest_bytes),
            },
        )
        self._set_state(connection, job, "done")
        committed = (
            connection.execute(
                text("SELECT committed_at FROM run_results WHERE run_id = :run_id"),
                {"run_id": job.run_id},
            )
            .mappings()
            .one()
        )
        return result.model_copy(update={"committed_at": committed["committed_at"]})

    def get_result(self, run_id: str) -> Result | None:
        """Zatwierdzony wynik albo ``None``; manifest na dysku musi zgadzać się ze skrótem."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT r.run_id, r.outcome, r.result_artifact_id, r.evidence_artifact_id,
                               r.report_artifact_id, r.committed_at, r.manifest_sha256,
                               j.batch_id, j.document_id
                        FROM run_results r JOIN jobs j ON j.run_id = r.run_id
                        WHERE r.run_id = :run_id AND j.state = 'done'
                        """
                    ),
                    {"run_id": run_id},
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        self._read_verified(
            self._manifest_key(row["batch_id"], row["document_id"], run_id),
            row["manifest_sha256"],
            f"manifest {run_id}",
        )
        return Result(**{key: row[key] for key in Result.model_fields})

    def get_manifest(self, run_id: str) -> JsonValue | None:
        """Manifest zatwierdzonego przebiegu albo ``None``."""
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT r.manifest FROM run_results r JOIN jobs j ON j.run_id = r.run_id "
                    "WHERE r.run_id = :run_id AND j.state = 'done'"
                ),
                {"run_id": run_id},
            ).first()
        return None if row is None else _JSON.validate_json(str(row[0]))

    def list_runs(self, document_id: str) -> list[RunSummary]:
        """Jawna historia przebiegów; wynik widać dopiero po zatwierdzeniu."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT j.run_id, j.id AS job_id, j.document_id, j.state, j.revision,
                           r.outcome
                    FROM jobs j LEFT JOIN run_results r ON r.run_id = j.run_id
                    WHERE j.document_id = :document_id ORDER BY j.rowid
                    """
                ),
                {"document_id": document_id},
            ).mappings()
            return [RunSummary(**dict(row)) for row in rows]

    # -- restart i uzgodnienie ----------------------------------------------

    def recover_after_restart(self) -> RecoveryReport:
        """Uzgadnia indeks z dyskiem po restarcie; operacja jest idempotentna.

        Przerwane ``running`` kończą jako ``done/technical_error`` z raportem
        przerwania (jawne ponowienie to nowy ``run_id``). Zatwierdzony wynik,
        którego manifest lub artefakt zniknął albo ma inny skrót, jest jawnie
        zamieniany na ``technical_error`` — nigdy po cichu zachowany.
        """
        with write_transaction(self._engine) as connection:
            inconsistent = self._reconcile_committed(connection)
            interrupted = self._interrupt_running(connection)
        return RecoveryReport(
            interrupted_run_ids=tuple(interrupted),
            inconsistent_run_ids=tuple(inconsistent),
            removed_temp_files=self._remove_temp_files(),
        )

    def _interrupt_running(self, connection: Connection) -> list[str]:
        rows = connection.execute(
            text("SELECT run_id FROM jobs WHERE state = 'running' ORDER BY rowid")
        ).all()
        interrupted: list[str] = []
        for row in rows:
            run_id = str(row[0])
            job = self._select_job(connection, "run_id", run_id)
            if job is None:  # pragma: no cover - wiersz właśnie odczytano w tej transakcji
                continue
            report = self._store_artifact(
                connection,
                job,
                Artifact(
                    id=f"interrupted-{_sha256(run_id.encode())[:32]}",
                    run_id=run_id,
                    stage="report",
                    schema_version="1",
                    media_type="application/json",
                ),
                _canonical_json({"code": "run_interrupted", "run_id": run_id}).encode("utf-8"),
            )
            self._commit(
                connection,
                job,
                _canonical_json({"code": "run_interrupted", "interrupted": True}),
                Result(run_id=run_id, outcome="technical_error", report_artifact_id=report.id),
            )
            interrupted.append(run_id)
        return interrupted

    def _reconcile_committed(self, connection: Connection) -> list[str]:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT r.run_id, r.manifest_sha256, j.batch_id, j.document_id
                    FROM run_results r JOIN jobs j ON j.run_id = r.run_id
                    ORDER BY r.rowid
                    """
                )
            )
            .mappings()
            .all()
        )
        inconsistent: list[str] = []
        for row in rows:
            run_id = str(row["run_id"])
            try:
                self._read_verified(
                    self._manifest_key(row["batch_id"], row["document_id"], run_id),
                    row["manifest_sha256"],
                    f"manifest {run_id}",
                )
                self._verify_run_artifacts(
                    connection, run_id, Result(run_id=run_id, outcome="technical_error")
                )
            except IntegrityViolationError:
                self._demote(connection, run_id, row["batch_id"], row["document_id"])
                inconsistent.append(run_id)
        return inconsistent

    def _demote(self, connection: Connection, run_id: str, batch_id: str, document_id: str) -> None:
        manifest_text = _canonical_json({"code": "storage_inconsistent", "run_id": run_id})
        manifest_bytes = manifest_text.encode("utf-8")
        _atomic_write(self._path(self._manifest_key(batch_id, document_id, run_id)), manifest_bytes)
        connection.execute(
            text(
                """
                UPDATE run_results
                SET outcome = 'technical_error', result_artifact_id = NULL,
                    evidence_artifact_id = NULL, report_artifact_id = NULL,
                    manifest = :manifest, manifest_sha256 = :sha256
                WHERE run_id = :run_id
                """
            ),
            {"manifest": manifest_text, "sha256": _sha256(manifest_bytes), "run_id": run_id},
        )

    def _remove_temp_files(self) -> int:
        removed = 0
        if not self._work_dir.is_dir():
            return removed
        for path in self._work_dir.rglob(f".*{_TMP_SUFFIX}"):
            if path.is_file():
                path.unlink(missing_ok=True)
                removed += 1
        return removed

    # -- błędy ---------------------------------------------------------------

    @staticmethod
    def _raise_for_integrity(error: IntegrityError, kind: str, identifier: str) -> NoReturn:
        message = str(error.orig)
        if "UNIQUE" in message:
            raise AlreadyExistsError(f"Kolizja: {kind} {identifier} już istnieje.") from error
        if "FOREIGN KEY" in message:
            raise NotFoundError(f"Brak powiązanego rekordu dla: {kind} {identifier}.") from error
        raise RepositoryError(f"Naruszenie ograniczeń dla: {kind} {identifier}.") from error
