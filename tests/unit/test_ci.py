"""Kontrakt lokalnego runnera: etapy, poziomy hooków i mutacje z cache."""

import ast
import importlib
import importlib.util
import json
import subprocess
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
ci = importlib.import_module("ci")

OK = subprocess.CompletedProcess([], 0, stdout="")


@pytest.fixture(autouse=True)
def isolated_git_environment(monkeypatch):
    """Hook Git ustawia GIT_INDEX_FILE; testy na tymczasowych repo nie mogą go dziedziczyć."""
    for name in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):
        monkeypatch.delenv(name, raising=False)


def git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)
    git(path, "config", "user.email", "ci@example.invalid")
    git(path, "config", "user.name", "ci")


def pytest_result(base_code: int, mutant_code: int):
    """Pierwsze wywołanie to testy bazowe, kolejne to mutanty."""
    calls = {"count": 0}

    def run(*args, **kwargs):
        calls["count"] += 1
        code = base_code if calls["count"] == 1 else mutant_code
        return subprocess.CompletedProcess([], code, stdout="FAILED tests/x.py::test_a\n")

    return run


@pytest.fixture
def mutation_tree(tmp_path, monkeypatch):
    (tmp_path / ".ci").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_normalizer.py").write_text("import normalizer\n")
    (tmp_path / "normalizer.py").write_text("value = 10\n")
    monkeypatch.setattr(ci, "verify_shadow_loading", lambda *args: True)
    return tmp_path


def test_all_runs_stages_in_order(tmp_path, capsys):
    with patch.object(ci, "run_stage", return_value=True) as run:
        assert ci.main(["--stage", "all"], root=tmp_path) == 0
    assert [call.args[0] for call in run.call_args_list] == list(ci.STAGES)
    assert "OK" in capsys.readouterr().out


def test_failure_stops_following_stages(tmp_path, capsys):
    with patch.object(ci, "run_stage", return_value=False) as run:
        assert ci.main([], root=tmp_path) == 1
    assert run.call_count == 1
    assert "SKIP" in capsys.readouterr().out


def test_keep_going_preserves_failure(tmp_path):
    with patch.object(ci, "run_stage", side_effect=[False] + [True] * 6) as run:
        assert ci.main(["--keep-going"], root=tmp_path) == 1
    assert run.call_count == 7


def test_fast_checks_spec_without_tests(tmp_path):
    with patch.object(ci, "run_stage", return_value=True) as run:
        assert ci.main(["--fast"], root=tmp_path) == 0
    assert [call.args[0] for call in run.call_args_list] == ["docs", "lint", "types", "api"]
    assert run.call_args.args[2].fast is True


def test_missing_tool_fails_with_installation_hint(tmp_path, capsys):
    with patch.object(importlib.util, "find_spec", return_value=None):
        assert ci.main(["--stage", "lint"], root=tmp_path) == 1
    out = capsys.readouterr().out
    assert "requirements-dev.txt" in out
    assert "CI_PYTHON" in out


def test_test_stage_excludes_eval_and_redirects_writes(tmp_path):
    with patch.object(ci.subprocess, "run", return_value=OK) as run:
        assert ci.main(["--stage", "test"], root=tmp_path) == 0
    command = run.call_args.args[0]
    assert command[command.index("-m", 3) + 1] == "not eval"
    assert "--cov=odwolania2json" in command
    assert run.call_args.kwargs["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
    assert ".ci" in " ".join(command)


@pytest.mark.parametrize("arguments", [["--fast", "--stage", "test"], ["--spec"], ["--files", "a"]])
def test_conflicting_options_are_rejected(arguments):
    with pytest.raises(SystemExit) as error:
        ci.main(arguments)
    assert error.value.code == 2


@pytest.mark.parametrize(
    "arguments",
    [
        ["--stage", "lint", "--changed"],
        ["--stage", "mutation", "--changed", "--since", "main"],
        ["--profile", "commit", "--stage", "lint"],
        ["--profile", "push", "--fast"],
        ["--jobs", "0"],
    ],
)
def test_invalid_mutation_and_profile_combinations_are_rejected(arguments):
    with pytest.raises(SystemExit) as error:
        ci.main(arguments)
    assert error.value.code == 2


def test_fast_api_selects_spec(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "require", lambda module: True)
    with patch.object(ci.subprocess, "run", return_value=OK) as run:
        assert ci.main(["--fast", "--keep-going"], root=tmp_path) == 0
    assert run.call_args.args[0][-2:] == ["--stage", "spec"]


def test_lint_with_files_checks_only_existing_python_and_respects_exclusions(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    with patch.object(ci.subprocess, "run", return_value=OK) as run:
        assert ci.lint(tmp_path, ci.Options(files=("a.py", "gone.py", "note.md"))) is True
    commands = [call.args[0] for call in run.call_args_list]
    assert len(commands) == 2
    assert all(command[-1] == "a.py" for command in commands)
    assert all("--force-exclude" in command for command in commands)


def test_lint_without_python_files_is_explicit_skip(tmp_path, capsys):
    assert ci.lint(tmp_path, ci.Options(files=("note.md",))) is None
    assert "SKIP lint" in capsys.readouterr().out


def test_select_tests_maps_modules_and_falls_back_to_full_suite(tmp_path):
    (tmp_path / "tests/unit").mkdir(parents=True)
    (tmp_path / "tests/unit/test_alpha.py").write_text("from pkg import alpha\n")
    (tmp_path / "tests/unit/test_other.py").write_text("import beta\n")
    (tmp_path / "apps/backend/pkg").mkdir(parents=True)
    assert ci.select_tests(tmp_path, ("apps/backend/pkg/alpha.py",)) == ["tests/unit/test_alpha.py"]
    assert ci.select_tests(tmp_path, ("tests/unit/test_other.py", "README.md")) == [
        "tests/unit/test_other.py"
    ]
    assert ci.select_tests(tmp_path, ("README.md",)) == []
    assert ci.select_tests(tmp_path, ("apps/backend/pkg/unknown.py",)) is None
    assert ci.select_tests(tmp_path, ("pyproject.toml",)) is None
    assert ci.select_tests(tmp_path, ("tests/conftest.py",)) is None


def test_commit_test_stage_runs_selected_tests_without_coverage(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_alpha.py").write_text("")
    with patch.object(ci.subprocess, "run", return_value=OK) as run:
        assert ci.test(tmp_path, ci.Options(files=("tests/test_alpha.py",))) is True
    command = run.call_args.args[0]
    assert "tests/test_alpha.py" in command
    assert not any(part.startswith("--cov") for part in command)
    assert "-x" in command


def test_commit_test_stage_skips_when_nothing_relevant_changed(tmp_path, capsys):
    assert ci.test(tmp_path, ci.Options(files=("docs/a.md",))) is None
    assert "SKIP test" in capsys.readouterr().out


def test_commit_plan_runs_only_stages_for_changed_files():
    assert ci.commit_plan({"docs/a.md"}).keys() == {"docs"}
    plan = ci.commit_plan({"apps/backend/odwolania2json/domain/normalize.py"})
    assert plan.keys() == {"lint", "test", "types", "mutation"}
    assert plan["lint"].files == ("apps/backend/odwolania2json/domain/normalize.py",)
    assert plan["mutation"].changed is True
    assert ci.commit_plan({"packages/contracts/odwolania2json_contracts/openapi.yaml"}) == {
        "api": ci.Options(fast=True)
    }
    assert ci.commit_plan({"pyproject.toml"})["lint"].files is None
    assert ci.commit_plan(set()) == {}


def test_commit_profile_skips_untouched_stages_and_reports_budget(tmp_path, capsys):
    init_repo(tmp_path)
    (tmp_path / "note.md").write_text("x\n")
    git(tmp_path, "add", "note.md")
    with patch.object(ci, "run_stage", return_value=True) as run:
        assert ci.main(["--profile", "commit"], root=tmp_path) == 0
    assert run.call_count == 0
    output = capsys.readouterr().out
    assert "SKIP mutation" in output
    assert "budżet 10 s: w budżecie" in output


def test_profile_reports_exceeded_budget(tmp_path, capsys, monkeypatch):
    init_repo(tmp_path)
    monkeypatch.setitem(ci.BUDGETS, "commit", -1.0)
    assert ci.main(["--profile", "commit"], root=tmp_path) == 0
    assert "BUDŻET PRZEKROCZONY" in capsys.readouterr().out


def test_push_profile_uses_incremental_mutation_and_no_audit(tmp_path, monkeypatch):
    # Hooki gita ustawiają GIT_DIR, więc baza zależałaby od otoczenia; ustalamy ją jawnie.
    monkeypatch.setattr(ci, "push_base", lambda root: "main")
    with patch.object(ci, "run_stage", return_value=True) as run:
        assert ci.main(["--profile", "push"], root=tmp_path) == 0
    assert [call.args[0] for call in run.call_args_list] == list(ci.STAGES[:6])
    assert run.call_args.args[2].since == "main"


def test_push_base_prefers_remote_main_over_stale_local_main(tmp_path):
    init_repo(tmp_path)
    (tmp_path / "base.py").write_text("a = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    git(tmp_path, "branch", "-M", "main")
    git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")
    assert ci.push_base(tmp_path) == "origin/main"
    git(tmp_path, "update-ref", "-d", "refs/remotes/origin/main")
    assert ci.push_base(tmp_path) == "main"


def test_failing_stage_is_reported_in_profile_summary(tmp_path, capsys):
    with patch.object(ci, "run_stage", return_value=False):
        assert ci.main(["--profile", "push"], root=tmp_path) == 1
    assert "FAIL razem" in capsys.readouterr().out


def test_declarative_variants_cover_digits_labels_and_field_types():
    source = (
        "import re\nfrom pydantic import BaseModel\n"
        'pattern = re.compile(r"NIP: [0-9]{10}")\n'
        "class Model(BaseModel):\n    value: str\n"
    )
    rendered = [ast.unparse(ast.parse(text)) for text in ci.declarative_variants(source)]
    assert any("NIP: [0-9]{11}" in text for text in rendered)
    assert any("XIP:" in text for text in rendered)
    assert any("value: int" in text for text in rendered)


def test_changed_uses_only_staged_paths(tmp_path):
    init_repo(tmp_path)
    (tmp_path / "normalizer.py").write_text("value = 1\n")
    git(tmp_path, "add", "normalizer.py")
    (tmp_path / "unstaged.py").write_text("value = 2\n")
    assert ci.changed_paths(tmp_path) == {"normalizer.py"}


def test_since_collects_branch_dirty_and_untracked_files(tmp_path):
    init_repo(tmp_path)
    (tmp_path / "base.py").write_text("a = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    git(tmp_path, "branch", "-M", "main")
    git(tmp_path, "checkout", "-qb", "work")
    (tmp_path / "committed.py").write_text("b = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "work")
    (tmp_path / "base.py").write_text("a = 2\n")
    (tmp_path / "new.py").write_text("c = 1\n")
    assert ci.since_paths(tmp_path, "main") == {"committed.py", "base.py", "new.py"}
    assert ci.since_paths(tmp_path, "no-such-ref") is None


def test_changed_without_matching_files_skips_mutation(tmp_path, capsys):
    init_repo(tmp_path)
    assert ci.main(["--stage", "mutation", "--changed"], root=tmp_path) == 0
    assert "SKIP mutation" in capsys.readouterr().out


def test_changed_mutates_index_snapshot_and_propagates_failure(tmp_path, monkeypatch):
    init_repo(tmp_path)
    source = tmp_path / "apps/normalizer.py"
    source.parent.mkdir()
    source.write_text("value = 10\n")
    git(tmp_path, "add", ".")
    source.write_text("value = 99\n")
    (source.parent / "validator.py").write_text("value = 2\n")

    def inspect_snapshot(workspace, paths, **kwargs):
        assert paths == ["apps/normalizer.py"]
        assert (workspace / paths[0]).read_text() == "value = 10\n"
        assert not (workspace / "apps/validator.py").exists()
        assert kwargs["ci_root"] == tmp_path
        return False

    monkeypatch.setattr(ci, "check_mutants", inspect_snapshot)
    assert ci.main(["--stage", "mutation", "--changed"], root=tmp_path) == 1
    assert source.read_text() == "value = 99\n"


def test_since_scope_includes_modules_whose_tests_changed(tmp_path, monkeypatch):
    (tmp_path / "apps").mkdir()
    (tmp_path / "apps/normalizer.py").write_text("value = 1\n")
    (tmp_path / "apps/validator.py").write_text("value = 1\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_validator.py").write_text("import validator\n")
    seen: list[list[str]] = []
    monkeypatch.setattr(ci, "since_paths", lambda root, ref: {"tests/test_validator.py"})
    monkeypatch.setattr(ci, "check_mutants", lambda root, paths, **kw: seen.append(paths) or True)
    assert ci.mutation(tmp_path, ci.Options(since="main")) is True
    assert seen == [["apps/validator.py"]]


def test_since_scope_without_matching_files_is_skip(tmp_path, monkeypatch, capsys):
    (tmp_path / "apps").mkdir()
    (tmp_path / "apps/normalizer.py").write_text("value = 1\n")
    monkeypatch.setattr(ci, "since_paths", lambda root, ref: {"README.md"})
    assert ci.mutation(tmp_path, ci.Options(since="main")) is None
    assert "SKIP mutation" in capsys.readouterr().out


def test_missing_merge_base_falls_back_to_full_scope(tmp_path, monkeypatch, capsys):
    (tmp_path / "apps").mkdir()
    (tmp_path / "apps/normalizer.py").write_text("value = 1\n")
    seen: list[list[str]] = []
    monkeypatch.setattr(ci, "since_paths", lambda root, ref: None)
    monkeypatch.setattr(ci, "check_mutants", lambda root, paths, **kw: seen.append(paths) or True)
    assert ci.mutation(tmp_path, ci.Options(since="main")) is True
    assert seen == [["apps/normalizer.py"]]
    assert "brak merge-base" in capsys.readouterr().out


@pytest.mark.parametrize(("code", "expected"), [(0, False), (2, False), (-1, False), (1, True)])
def test_mutation_requires_all_mutants_killed(mutation_tree, code, expected):
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, code)):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"], use_cache=False) is expected
    assert (mutation_tree / "normalizer.py").read_text() == "value = 10\n"


def test_mutation_without_mutants_fails(mutation_tree):
    (mutation_tree / "normalizer.py").write_text("pass\n")
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"], use_cache=False) is False


def test_mutation_timeout_blocks_and_never_touches_repository_source(mutation_tree):
    results = [OK]

    def run(*args, **kwargs):
        if results:
            return results.pop()
        raise subprocess.TimeoutExpired("pytest", 60)

    with patch.object(ci.subprocess, "run", side_effect=run):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"], use_cache=False) is False
    assert (mutation_tree / "normalizer.py").read_text() == "value = 10\n"
    assert "error exit=-1" in (mutation_tree / ".ci/mutation-report.txt").read_text()
    assert (mutation_tree / ".ci/mutation-failures/normalizer-1.py").exists()


def test_baseline_failure_is_reported_honestly_and_skips_mutants(mutation_tree, capsys):
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(1, 1)) as run:
        assert ci.check_mutants(mutation_tree, ["normalizer.py"], use_cache=False) is False
    assert run.call_count == 1
    output = capsys.readouterr().out
    assert "testy bazowe nie przechodzą" in output
    assert "tests/x.py::test_a" in output
    assert not (mutation_tree / ".ci/mutation-cache.json").read_text().count("normalizer")


def test_green_run_is_cached_and_unchanged_module_is_skipped(mutation_tree, capsys):
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)) as run:
        assert ci.check_mutants(mutation_tree, ["normalizer.py"]) is True
        first = run.call_count
        assert ci.check_mutants(mutation_tree, ["normalizer.py"]) is True
        assert run.call_count == first
    assert "cache" in capsys.readouterr().out
    cache = json.loads((mutation_tree / ".ci/mutation-cache.json").read_text())
    assert cache["entries"]["normalizer.py"]["mutants"] == 1


def test_cache_is_invalidated_by_source_or_test_change(mutation_tree):
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"]) is True
    for target, text in [
        ("normalizer.py", "value = 11\n"),
        ("tests/test_normalizer.py", "# normalizer changed\n"),
    ]:
        (mutation_tree / target).write_text(text)
        with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)) as run:
            assert ci.check_mutants(mutation_tree, ["normalizer.py"]) is True
        assert run.call_count >= 2


def test_failed_run_never_becomes_cached_pass(mutation_tree):
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"]) is True
    (mutation_tree / "tests/test_normalizer.py").write_text("# weaker tests\n")
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 0)):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"]) is False
    cache = json.loads((mutation_tree / ".ci/mutation-cache.json").read_text())
    assert "normalizer.py" not in cache["entries"]
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 0)):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"]) is False


def test_no_cache_option_forces_rerun(mutation_tree):
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"]) is True
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)) as run:
        assert ci.check_mutants(mutation_tree, ["normalizer.py"], use_cache=False) is True
    assert run.call_count >= 2


def test_shadow_copies_repository_data_for_baseline_tests(tmp_path):
    root = tmp_path / "repo"
    shadow = tmp_path / "shadow"
    (root / "apps").mkdir(parents=True)
    (root / "apps/mod.py").write_text("value = 1\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "data").mkdir()
    (root / "data/podzial.json").write_text("{}\n", encoding="utf-8")
    (root / "docs/02-materialy/organizator-uzp").mkdir(parents=True)
    (root / "docs/02-materialy/organizator-uzp/x.md").write_text("# x\n", encoding="utf-8")

    ci.make_shadow(root, shadow, [])

    assert (shadow / "data/podzial.json").read_text(encoding="utf-8") == "{}\n"
    assert (shadow / "docs/02-materialy/organizator-uzp/x.md").is_file()


def test_mutants_run_in_parallel_with_separate_workspaces(mutation_tree):
    (mutation_tree / "normalizer.py").write_text("a = 1\nb = 2\nc = 3\nd = 4\n")
    workdirs: set[str] = set()
    first = pytest_result(0, 1)

    def run(command, **kwargs):
        workdirs.add(kwargs["env"]["TMPDIR"])
        return first(command, **kwargs)

    with patch.object(ci.subprocess, "run", side_effect=run):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"], jobs=3, use_cache=False) is True
    assert len(workdirs) <= 3
    assert not list((mutation_tree / ".ci").glob("mutation-*/"))


def test_mutant_timeout_option_is_passed_to_pytest(mutation_tree):
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)) as run:
        ci.check_mutants(mutation_tree, ["normalizer.py"], timeout=7.0, use_cache=False)
    assert run.call_args.kwargs["timeout"] == 7.0


def test_shadow_check_fails_when_installed_package_wins(mutation_tree, monkeypatch, capsys):
    monkeypatch.setattr(ci, "verify_shadow_loading", lambda *args: False)
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)):
        assert ci.check_mutants(mutation_tree, ["normalizer.py"], use_cache=False) is False
    assert "nie jest ładowany" in capsys.readouterr().out


def test_module_tests_use_models_override_and_name_matching(tmp_path):
    (tmp_path / "tests/unit").mkdir(parents=True)
    (tmp_path / "tests/unit/test_a.py").write_text("import normalize\n")
    assert ci.module_tests(tmp_path, "x/normalize.py") == ["tests/unit/test_a.py"]
    assert ci.module_tests(tmp_path, "x/other.py") == ["tests"]
    assert ci.module_tests(tmp_path, "x/models.py") == list(ci.MODEL_TESTS)


def test_cache_write_is_atomic_and_tolerates_corrupt_file(tmp_path):
    (tmp_path / ".ci").mkdir()
    (tmp_path / ci.CACHE_PATH).write_text("{broken")
    assert ci.load_cache(tmp_path) == {}
    ci.save_cache(tmp_path, {"a.py": {"key": "k", "mutants": 2}})
    assert ci.load_cache(tmp_path) == {"a.py": {"key": "k", "mutants": 2}}
    assert not list((tmp_path / ".ci").glob(".mutation-cache-*"))


def test_engine_fingerprint_depends_on_operators():
    first = ci.engine_fingerprint()
    with patch.object(ci, "ENGINE_VERSION", "other"):
        assert ci.engine_fingerprint() != first


def test_reexec_prefers_ci_python_once(tmp_path, monkeypatch):
    interpreter = tmp_path / "python"
    interpreter.write_text("")
    monkeypatch.delenv("CI_PYTHON_ACTIVE", raising=False)
    monkeypatch.setenv("CI_PYTHON", str(interpreter))
    with patch.object(ci.os, "execv") as execv:
        ci.reexec_in_project_python(tmp_path)
        assert execv.call_args.args[0] == str(interpreter)
        execv.reset_mock()
        ci.reexec_in_project_python(tmp_path)
        assert execv.call_count == 0


def test_audit_network_failure_is_explicit_skip(tmp_path, monkeypatch, capsys):
    def offline(*args, **kwargs):
        raise urllib.error.URLError("DNS unavailable")

    monkeypatch.setattr(ci, "require", lambda name: True)
    monkeypatch.setattr(ci.urllib.request, "urlopen", offline)
    assert ci.main(["--stage", "audit"], root=tmp_path) == 0
    output = capsys.readouterr().out
    assert "SKIP audit" in output
    assert "sieci" in output


def test_changed_lines_reads_added_and_modified_ranges_from_index(tmp_path):
    init_repo(tmp_path)
    source = tmp_path / "normalizer.py"
    source.write_text("a = 1\nb = 2\nc = 3\nd = 4\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    source.write_text("a = 1\nb = 20\nc = 3\nd = 4\ne = 5\nf = 6\n")
    (tmp_path / "fresh.py").write_text("x = 1\ny = 2\n")
    git(tmp_path, "add", ".")
    assert ci.changed_lines(tmp_path, {"normalizer.py", "fresh.py"}) == {
        "normalizer.py": {2, 5, 6},
        "fresh.py": {1, 2},
    }


def test_declarative_mutants_report_original_line_numbers():
    pairs = list(ci.declarative_mutants("a = 1\n\nb = 2\n"))
    assert sorted({line for line, _ in pairs}) == [1, 3]


def test_partial_mutation_runs_only_changed_lines_and_is_not_cached(mutation_tree):
    (mutation_tree / "normalizer.py").write_text("a = 1\nb = 2\nc = 3\n")
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)) as run:
        ok = ci.check_mutants(mutation_tree, ["normalizer.py"], lines={"normalizer.py": {2}})
    assert ok is True
    assert run.call_count == 2  # baza + jeden mutant
    assert not (mutation_tree / ".ci/mutation-cache.json").read_text().count("normalizer.py")


def test_partial_mutation_without_mutants_in_changed_lines_is_skip(mutation_tree, capsys):
    (mutation_tree / "normalizer.py").write_text("a = 1\n# komentarz\n")
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 1)):
        ok = ci.check_mutants(mutation_tree, ["normalizer.py"], lines={"normalizer.py": {2}})
    assert ok is True
    assert "brak mutantów w zmienionych liniach" in capsys.readouterr().out


def test_surviving_mutant_still_blocks_partial_mutation(mutation_tree):
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 0)):
        assert (
            ci.check_mutants(mutation_tree, ["normalizer.py"], lines={"normalizer.py": {1}})
            is False
        )


def test_max_survivors_stops_running_remaining_mutants(mutation_tree, capsys):
    (mutation_tree / "normalizer.py").write_text("\n".join(f"v{i} = {i}" for i in range(10)))
    with patch.object(ci.subprocess, "run", side_effect=pytest_result(0, 0)) as run:
        assert (
            ci.check_mutants(mutation_tree, ["normalizer.py"], max_survivors=1, use_cache=False)
            is False
        )
    assert run.call_count < 11
    assert "nieuruchomione po przerwaniu" in capsys.readouterr().out
