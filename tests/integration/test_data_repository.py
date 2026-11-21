"""Testy kontraktowe DataRepository (architektura §9) na SQLite.

Fixture ``repository`` jest jedynym miejscem wyboru implementacji. Druga
implementacja (ADR-004, warunki powrotu) musi przejść ten sam zestaw.
"""

import json
import threading
from pathlib import Path

import odwolania2json.db.data_repository as module
import pytest
from odwolania2json.db import migrate as migrator
from odwolania2json.db.data_repository import (
    AlreadyExistsError,
    Artifact,
    Batch,
    DataRepository,
    Document,
    IntegrityViolationError,
    InvalidTransitionError,
    Job,
    NotFoundError,
    Result,
    RevisionConflictError,
    SqliteDataRepository,
)
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

PDF = b"%PDF-1.7 przykladowe bajty"


@pytest.fixture
def database_url(tmp_path):
    url = f"sqlite:///{tmp_path / 'data.db'}"
    migrator.migrate(url)
    return url


@pytest.fixture
def work_dir(tmp_path):
    return tmp_path / "work"


@pytest.fixture
def repository(database_url, work_dir):
    repo = SqliteDataRepository(database_url, work_dir)
    try:
        yield repo
    finally:
        repo.dispose()


def new_job(repo, name="a", batch="b1", content=PDF):
    """Wsad (jeśli brak), dokument i zadanie w stanie queued."""
    if repo.get_batch(batch) is None:
        repo.create_batch(Batch(id=batch))
    repo.put_document(
        Document(id=f"d-{name}", batch_id=batch, input_path=f"sprawa/{name}.pdf"), content
    )
    return repo.create_job(
        Job(id=f"j-{name}", batch_id=batch, document_id=f"d-{name}", run_id=f"r-{name}")
    )


def running_job(repo, name="a"):
    job = new_job(repo, name)
    return repo.claim_job(job.id, job.revision)


def add_artifact(repo, run_id, artifact_id="art1", content=b'{"x":1}'):
    return repo.put_artifact(
        run_id,
        Artifact(
            id=artifact_id,
            run_id=run_id,
            stage="t5",
            schema_version="1",
            media_type="application/json",
        ),
        content,
    )


def test_sqlite_repository_implements_data_repository(repository):
    assert isinstance(repository, DataRepository)


# --- wsady i dokumenty ---------------------------------------------------


def test_batch_lists_its_jobs_in_creation_order(repository):
    new_job(repository, "a")
    new_job(repository, "b")
    batch = repository.get_batch("b1")
    assert batch is not None
    assert batch.job_ids == ("j-a", "j-b")
    assert [job.id for job in repository.list_jobs("b1")] == ["j-a", "j-b"]


def test_create_batch_rejects_duplicate_id(repository):
    repository.create_batch(Batch(id="b1"))
    with pytest.raises(AlreadyExistsError):
        repository.create_batch(Batch(id="b1"))


def test_unknown_records_read_as_none(repository):
    assert repository.get_batch("x") is None
    assert repository.get_document("x") is None
    assert repository.get_job("x") is None
    assert repository.get_result("x") is None
    assert repository.get_manifest("x") is None
    assert repository.list_runs("x") == []


def test_document_roundtrip_keeps_exact_bytes_and_hash(repository):
    new_job(repository)
    document = repository.get_document("d-a")
    assert document is not None
    assert document.input_path == "sprawa/a.pdf"
    assert document.size_bytes == len(PDF)
    assert document.sha256 is not None
    assert repository.open_document("d-a") == PDF


@pytest.mark.parametrize(
    "path", ["../x.pdf", "/abs/x.pdf", "a/../../x.pdf", "a\\b.pdf", "C:/x.pdf", "./x.pdf"]
)
def test_put_document_rejects_path_escaping_input_directory(repository, path):
    repository.create_batch(Batch(id="b1"))
    with pytest.raises(ValueError, match="Ścieżka"):
        repository.put_document(Document(id="d1", batch_id="b1", input_path=path), PDF)
    assert repository.get_document("d1") is None


def test_put_document_rejects_declared_hash_mismatch(repository):
    repository.create_batch(Batch(id="b1"))
    with pytest.raises(IntegrityViolationError):
        repository.put_document(
            Document(id="d1", batch_id="b1", input_path="x.pdf", sha256="0" * 64), PDF
        )
    assert repository.get_document("d1") is None


def test_put_document_rejects_name_collision_in_batch(repository):
    new_job(repository, "a")
    with pytest.raises(AlreadyExistsError):
        repository.put_document(
            Document(id="d-other", batch_id="b1", input_path="sprawa/a.pdf"), b"inne"
        )
    assert repository.get_document("d-other") is None


def test_put_document_never_overwrites_existing_bytes(repository):
    new_job(repository, "a")
    with pytest.raises(AlreadyExistsError):
        repository.put_document(
            Document(id="d-a", batch_id="b1", input_path="inna/nazwa.pdf"), b"podmiana"
        )
    assert repository.open_document("d-a") == PDF


def test_put_document_requires_existing_batch(repository):
    with pytest.raises(NotFoundError):
        repository.put_document(Document(id="d1", batch_id="brak", input_path="x.pdf"), PDF)


def test_open_document_detects_tampered_bytes(repository, work_dir):
    new_job(repository)
    next(work_dir.rglob("input.pdf")).write_bytes(b"zmienione")
    with pytest.raises(IntegrityViolationError):
        repository.open_document("d-a")


def test_open_document_detects_missing_file(repository, work_dir):
    new_job(repository)
    next(work_dir.rglob("input.pdf")).unlink()
    with pytest.raises(IntegrityViolationError):
        repository.open_document("d-a")


def test_open_document_unknown_id_raises_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.open_document("brak")


# --- zadania i rewizje -------------------------------------------------------


def test_new_job_is_queued_with_revision_zero(repository):
    job = new_job(repository)
    stored = repository.get_job(job.id)
    assert stored is not None
    assert (stored.state, stored.revision) == ("queued", 0)


def test_create_job_rejects_non_initial_state(repository):
    new_job(repository, "a")
    with pytest.raises(InvalidTransitionError):
        repository.create_job(
            Job(id="j2", batch_id="b1", document_id="d-a", run_id="r2", state="running")
        )


def test_create_job_rejects_duplicate_run_id(repository):
    new_job(repository, "a")
    with pytest.raises(AlreadyExistsError):
        repository.create_job(Job(id="j2", batch_id="b1", document_id="d-a", run_id="r-a"))


def test_create_job_rejects_document_from_other_batch(repository):
    new_job(repository, "a", batch="b1")
    repository.create_batch(Batch(id="b2"))
    with pytest.raises(NotFoundError):
        repository.create_job(Job(id="j9", batch_id="b2", document_id="d-a", run_id="r9"))


def test_claim_job_moves_to_running_and_bumps_revision(repository):
    job = new_job(repository)
    claimed = repository.claim_job(job.id, 0)
    assert (claimed.state, claimed.revision) == ("running", 1)
    stored = repository.get_job(job.id)
    assert stored is not None
    assert (stored.state, stored.revision) == ("running", 1)


def test_claim_job_with_stale_revision_is_rejected_and_changes_nothing(repository):
    job = new_job(repository)
    repository.claim_job(job.id, 0)
    with pytest.raises(RevisionConflictError):
        repository.claim_job(job.id, 0)
    stored = repository.get_job(job.id)
    assert stored is not None
    assert stored.revision == 1


def test_claim_job_with_future_revision_is_rejected(repository):
    job = new_job(repository)
    with pytest.raises(RevisionConflictError):
        repository.claim_job(job.id, 5)
    stored = repository.get_job(job.id)
    assert stored is not None
    assert stored.state == "queued"


def test_claim_job_unknown_id_raises_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.claim_job("brak", 0)


def test_concurrent_claims_with_same_revision_have_exactly_one_winner(
    database_url, work_dir, repository
):
    job = new_job(repository)
    outcomes: list[str] = []
    barrier = threading.Barrier(6)

    def worker() -> None:
        own = SqliteDataRepository(database_url, work_dir)
        try:
            barrier.wait()
            own.claim_job(job.id, 0)
            outcomes.append("won")
        except RevisionConflictError:
            outcomes.append("conflict")
        finally:
            own.dispose()

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(outcomes) == ["conflict"] * 5 + ["won"]
    stored = repository.get_job(job.id)
    assert stored is not None
    assert stored.revision == 1


def test_update_job_rejects_illegal_transitions(repository):
    job = new_job(repository)
    with pytest.raises(InvalidTransitionError):
        repository.update_job(job.id, "done", 0)
    with pytest.raises(InvalidTransitionError):
        repository.update_job(job.id, "queued", 0)


def test_update_job_cannot_mark_done_without_commit_run(repository):
    job = running_job(repository)
    with pytest.raises(InvalidTransitionError, match="commit_run"):
        repository.update_job(job.id, "done", job.revision)
    stored = repository.get_job(job.id)
    assert stored is not None
    assert stored.state == "running"


def test_update_job_checks_revision_before_transition(repository):
    job = new_job(repository)
    with pytest.raises(RevisionConflictError):
        repository.update_job(job.id, "running", 3)


# --- artefakty ---------------------------------------------------------------


def test_artifact_roundtrip_and_hash(repository):
    job = running_job(repository)
    stored = add_artifact(repository, job.run_id)
    assert stored.sha256 is not None
    assert repository.open_artifact("art1") == b'{"x":1}'


def test_artifact_requires_running_job(repository):
    job = new_job(repository)
    with pytest.raises(InvalidTransitionError):
        add_artifact(repository, job.run_id)


def test_artifact_for_unknown_run_raises_not_found(repository):
    with pytest.raises(NotFoundError):
        add_artifact(repository, "brak")


def test_artifact_run_id_must_match(repository):
    job = running_job(repository)
    with pytest.raises(ValueError, match="run_id"):
        repository.put_artifact(
            job.run_id,
            Artifact(
                id="a", run_id="inny", stage="t5", schema_version="1", media_type="text/plain"
            ),
            b"x",
        )


def test_artifact_is_immutable_duplicate_id_is_rejected(repository):
    job = running_job(repository)
    add_artifact(repository, job.run_id, content=b"pierwszy")
    with pytest.raises(AlreadyExistsError):
        add_artifact(repository, job.run_id, content=b"drugi")
    assert repository.open_artifact("art1") == b"pierwszy"


def test_artifact_declared_hash_mismatch_is_rejected_and_invisible(repository):
    job = running_job(repository)
    with pytest.raises(IntegrityViolationError):
        repository.put_artifact(
            job.run_id,
            Artifact(
                id="a",
                run_id=job.run_id,
                stage="t5",
                schema_version="1",
                media_type="text/plain",
                sha256="1" * 64,
            ),
            b"x",
        )
    with pytest.raises(NotFoundError):
        repository.open_artifact("a")


def test_failed_artifact_write_leaves_no_row(repository, monkeypatch):
    job = running_job(repository)

    def broken(path: Path, content: bytes) -> None:
        raise OSError("dysk pelny")

    monkeypatch.setattr(module, "_atomic_write", broken)
    with pytest.raises(OSError, match="dysk"):
        add_artifact(repository, job.run_id)
    with pytest.raises(NotFoundError):
        repository.open_artifact("art1")


def test_database_forbids_updating_or_deleting_artifacts(repository):
    job = running_job(repository)
    add_artifact(repository, job.run_id)
    with pytest.raises(DBAPIError, match="immutable"), repository.engine.begin() as connection:
        connection.execute(text("UPDATE artifacts SET stage = 'x'"))
    with pytest.raises(DBAPIError, match="immutable"), repository.engine.begin() as connection:
        connection.execute(text("DELETE FROM artifacts"))


def test_open_artifact_detects_tampered_bytes(repository, work_dir):
    job = running_job(repository)
    add_artifact(repository, job.run_id)
    next(work_dir.rglob("art1")).write_bytes(b"zmienione")
    with pytest.raises(IntegrityViolationError):
        repository.open_artifact("art1")


def test_open_artifact_unknown_id_raises_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.open_artifact("brak")


# --- commit_run i odczyt zatwierdzonych wyników ------------------------------


def commit(repo, run_id, **kwargs):
    result = Result(run_id=run_id, outcome="complete", **kwargs)
    return repo.commit_run(run_id, {"engine": "1.0"}, result)


def test_commit_run_publishes_result_manifest_and_done_state(repository):
    job = running_job(repository)
    add_artifact(repository, job.run_id, "res", b"{}")
    committed = commit(repository, job.run_id, result_artifact_id="res")
    assert committed.committed_at is not None
    result = repository.get_result(job.run_id)
    assert result is not None
    assert (result.outcome, result.result_artifact_id) == ("complete", "res")
    assert result.evidence_artifact_id is None
    assert repository.get_manifest(job.run_id) == {"engine": "1.0"}
    stored = repository.get_job(job.id)
    assert stored is not None
    assert (stored.state, stored.revision) == ("done", 2)


def test_get_result_hides_uncommitted_runs(repository):
    job = running_job(repository)
    add_artifact(repository, job.run_id)
    assert repository.get_result(job.run_id) is None
    assert repository.get_manifest(job.run_id) is None


def test_commit_run_is_all_or_nothing_when_state_update_fails(repository, work_dir):
    job = running_job(repository)
    add_artifact(repository, job.run_id, "res")
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER boom BEFORE UPDATE ON jobs "
                "BEGIN SELECT RAISE(ABORT, 'awaria zapisu'); END"
            )
        )
    with pytest.raises(DBAPIError, match="awaria"):
        commit(repository, job.run_id, result_artifact_id="res")
    # Ani wynik, ani manifest, ani stan końcowy nie są widoczne.
    assert repository.get_result(job.run_id) is None
    assert repository.get_manifest(job.run_id) is None
    stored = repository.get_job(job.id)
    assert stored is not None
    assert stored.state == "running"
    with repository.engine.begin() as connection:
        connection.execute(text("DROP TRIGGER boom"))
    commit(repository, job.run_id, result_artifact_id="res")
    assert repository.get_result(job.run_id) is not None


def test_commit_run_is_all_or_nothing_when_manifest_write_fails(repository, monkeypatch):
    job = running_job(repository)
    add_artifact(repository, job.run_id, "res")

    def broken(path: Path, content: bytes) -> None:
        raise OSError("brak miejsca")

    monkeypatch.setattr(module, "_atomic_write", broken)
    with pytest.raises(OSError, match="brak miejsca"):
        commit(repository, job.run_id, result_artifact_id="res")
    monkeypatch.undo()
    assert repository.get_result(job.run_id) is None
    stored = repository.get_job(job.id)
    assert stored is not None
    assert stored.state == "running"


def test_commit_run_rejects_tampered_artifact_and_publishes_nothing(repository, work_dir):
    job = running_job(repository)
    add_artifact(repository, job.run_id, "res")
    add_artifact(repository, job.run_id, "other")
    next(work_dir.rglob("other")).write_bytes(b"zmienione")
    with pytest.raises(IntegrityViolationError):
        commit(repository, job.run_id, result_artifact_id="res")
    assert repository.get_result(job.run_id) is None
    stored = repository.get_job(job.id)
    assert stored is not None
    assert stored.state == "running"


def test_commit_run_rejects_missing_artifact_file(repository, work_dir):
    job = running_job(repository)
    add_artifact(repository, job.run_id, "res")
    next(work_dir.rglob("res")).unlink()
    with pytest.raises(IntegrityViolationError):
        commit(repository, job.run_id, result_artifact_id="res")


def test_commit_run_rejects_reference_to_artifact_of_other_run(repository):
    first = running_job(repository, "a")
    second = running_job(repository, "b")
    add_artifact(repository, first.run_id, "res")
    with pytest.raises(IntegrityViolationError):
        commit(repository, second.run_id, result_artifact_id="res")
    assert repository.get_result(second.run_id) is None


def test_commit_run_twice_is_rejected_and_keeps_first_result(repository):
    job = running_job(repository)
    commit(repository, job.run_id)
    with pytest.raises(AlreadyExistsError):
        repository.commit_run(
            job.run_id, {"engine": "2.0"}, Result(run_id=job.run_id, outcome="foreign")
        )
    result = repository.get_result(job.run_id)
    assert result is not None
    assert result.outcome == "complete"
    assert repository.get_manifest(job.run_id) == {"engine": "1.0"}


def test_commit_run_requires_running_state(repository):
    job = new_job(repository)
    with pytest.raises(InvalidTransitionError):
        commit(repository, job.run_id)


def test_commit_run_rejects_foreign_run_id_in_result(repository):
    job = running_job(repository)
    with pytest.raises(ValueError, match="run_id"):
        repository.commit_run(job.run_id, {}, Result(run_id="inny", outcome="complete"))


def test_commit_run_accepts_only_done_state(repository):
    job = running_job(repository)
    with pytest.raises(InvalidTransitionError):
        repository.commit_run(
            job.run_id,
            {},
            Result(run_id=job.run_id, outcome="complete"),
            state="running",  # type: ignore[arg-type]
        )


def test_commit_run_unknown_run_raises_not_found(repository):
    with pytest.raises(NotFoundError):
        commit(repository, "brak")


def test_get_result_detects_tampered_manifest(repository, work_dir):
    job = running_job(repository)
    commit(repository, job.run_id)
    (next(work_dir.rglob("manifest.json"))).write_text("{}", encoding="utf-8")
    with pytest.raises(IntegrityViolationError):
        repository.get_result(job.run_id)


def test_every_outcome_can_be_committed_with_null_references(repository):
    for index, outcome in enumerate(
        ("complete", "partial", "foreign", "ambiguous", "technical_error")
    ):
        job = running_job(repository, f"o{index}")
        repository.commit_run(job.run_id, {}, Result(run_id=job.run_id, outcome=outcome))
        result = repository.get_result(job.run_id)
        assert result is not None
        assert result.outcome == outcome


def test_result_rejects_unknown_outcome():
    with pytest.raises(ValueError, match="outcome"):
        Result(run_id="r", outcome="success")  # type: ignore[arg-type]


# --- historia przebiegów -----------------------------------------------------


def test_retry_creates_new_run_and_keeps_previous_result_as_history(repository):
    first = running_job(repository, "a")
    repository.commit_run(first.run_id, {}, Result(run_id=first.run_id, outcome="technical_error"))
    retry = repository.create_job(Job(id="j-retry", batch_id="b1", document_id="d-a", run_id="r-2"))
    runs = repository.list_runs("d-a")
    assert [(run.run_id, run.state, run.outcome) for run in runs] == [
        ("r-a", "done", "technical_error"),
        ("r-2", "queued", None),
    ]
    assert retry.run_id != first.run_id
    assert repository.get_result("r-2") is None
    first_result = repository.get_result("r-a")
    assert first_result is not None
    assert first_result.outcome == "technical_error"


# --- restart i uzgodnienie ---------------------------------------------------


def test_recovery_marks_interrupted_running_as_technical_error_with_report(database_url, work_dir):
    before = SqliteDataRepository(database_url, work_dir)
    job = running_job(before)
    queued = new_job(before, "q")
    before.dispose()  # „restart”: nowa instancja bez pamięci procesu
    after = SqliteDataRepository(database_url, work_dir)
    try:
        report = after.recover_after_restart()
        assert report.interrupted_run_ids == (job.run_id,)
        result = after.get_result(job.run_id)
        assert result is not None
        assert result.outcome == "technical_error"
        assert result.report_artifact_id is not None
        body = json.loads(after.open_artifact(result.report_artifact_id))
        assert body["code"] == "run_interrupted"
        stored = after.get_job(job.id)
        assert stored is not None
        assert stored.state == "done"
        untouched = after.get_job(queued.id)
        assert untouched is not None
        assert (untouched.state, untouched.revision) == ("queued", 0)
    finally:
        after.dispose()


def test_recovery_is_idempotent(repository):
    job = running_job(repository)
    first = repository.recover_after_restart()
    second = repository.recover_after_restart()
    assert first.interrupted_run_ids == (job.run_id,)
    assert second.interrupted_run_ids == ()
    assert second.inconsistent_run_ids == ()
    stored = repository.get_job(job.id)
    assert stored is not None
    assert stored.revision == 2


def test_recovery_does_not_start_new_run_or_rerun(repository):
    job = running_job(repository)
    repository.recover_after_restart()
    assert [run.run_id for run in repository.list_runs(job.document_id)] == [job.run_id]


def test_recovery_keeps_intact_committed_results(repository):
    job = running_job(repository)
    add_artifact(repository, job.run_id, "res")
    commit(repository, job.run_id, result_artifact_id="res")
    report = repository.recover_after_restart()
    assert report.inconsistent_run_ids == ()
    result = repository.get_result(job.run_id)
    assert result is not None
    assert result.outcome == "complete"
    assert result.result_artifact_id == "res"


def test_recovery_replaces_result_whose_manifest_is_missing_by_explicit_error(repository, work_dir):
    job = running_job(repository)
    commit(repository, job.run_id)
    next(work_dir.rglob("manifest.json")).unlink()
    report = repository.recover_after_restart()
    assert report.inconsistent_run_ids == (job.run_id,)
    result = repository.get_result(job.run_id)
    assert result is not None
    assert result.outcome == "technical_error"
    assert repository.get_manifest(job.run_id) == {
        "code": "storage_inconsistent",
        "run_id": job.run_id,
    }


def test_recovery_replaces_result_whose_artifact_was_tampered(repository, work_dir):
    job = running_job(repository)
    add_artifact(repository, job.run_id, "res")
    commit(repository, job.run_id, result_artifact_id="res")
    next(work_dir.rglob("res")).write_bytes(b"zmienione")
    report = repository.recover_after_restart()
    assert report.inconsistent_run_ids == (job.run_id,)
    result = repository.get_result(job.run_id)
    assert result is not None
    assert (result.outcome, result.result_artifact_id) == ("technical_error", None)


def test_recovery_removes_incomplete_temporary_files(repository, work_dir):
    job = running_job(repository)
    leftover = next(work_dir.rglob("input.pdf")).with_name(".input.pdf.1.abcd.tmp")
    leftover.write_bytes(b"polowa")
    report = repository.recover_after_restart()
    assert report.removed_temp_files == 1
    assert not leftover.exists()
    assert job.run_id in report.interrupted_run_ids


def test_recovery_on_empty_work_dir_is_a_noop(repository, work_dir):
    assert not work_dir.exists()
    report = repository.recover_after_restart()
    assert (report.interrupted_run_ids, report.inconsistent_run_ids) == ((), ())
    assert report.removed_temp_files == 0


# --- migracja 0002 -----------------------------------------------------------


def test_migration_0002_creates_repository_tables_and_is_idempotent(database_url):
    assert migrator.migrate(database_url) == []
    assert "0002_data_repository" in migrator.applied_versions(database_url)
    repo = SqliteDataRepository(database_url, Path("unused"))
    try:
        with repo.engine.connect() as connection:
            names = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master"))}
    finally:
        repo.dispose()
    assert {"batches", "batch_documents", "jobs", "artifacts", "run_results"} <= names


# --- walidacja granicy (wzorce identyfikatorów i skrótów) ------------------


@pytest.mark.parametrize("value", ["a", "A9", "run_1-x", "9z", "a" * 64])
def test_identifier_accepts_safe_values(value):
    assert Batch(id=value).id == value


@pytest.mark.parametrize("value", ["", "_a", "-a", "a/b", "a.b", "a b", "a" * 65, "ą", "../x"])
def test_identifier_rejects_unsafe_values(value):
    with pytest.raises(ValueError, match="id"):
        Batch(id=value)


@pytest.mark.parametrize("value", ["0" * 63, "0" * 65, "A" * 64, "g" * 64, ""])
def test_sha256_rejects_malformed_digests(value):
    with pytest.raises(ValueError, match="sha256"):
        Document(id="d", batch_id="b", input_path="x.pdf", sha256=value)


def test_sha256_accepts_lowercase_hex_digest():
    assert Document(id="d", batch_id="b", input_path="x.pdf", sha256="ab" * 32).sha256
