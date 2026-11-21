"""Kontrakt lokalnego runnera na granicy procesów narzędzi."""

import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
ci = importlib.import_module("ci")


def test_all_runs_stages_in_order(tmp_path, capsys):
    with patch.object(ci, "run_stage", return_value=True) as run:
        assert ci.main(["--stage", "all"], root=tmp_path) == 0
    assert [call.args[0] for call in run.call_args_list] == [
        "docs",
        "lint",
        "types",
        "api",
        "test",
        "mutation",
    ]
    assert "OK" in capsys.readouterr().out


def test_failure_stops_following_stages(tmp_path, capsys):
    with patch.object(ci, "run_stage", return_value=False) as run:
        assert ci.main([], root=tmp_path) == 1
    assert run.call_count == 1
    assert "SKIP" in capsys.readouterr().out


def test_keep_going_preserves_failure(tmp_path):
    with patch.object(ci, "run_stage", side_effect=[False, True, True, True, True, True]) as run:
        assert ci.main(["--keep-going"], root=tmp_path) == 1
    assert run.call_count == 6


def test_fast_checks_spec_without_tests(tmp_path):
    with patch.object(ci, "run_stage", return_value=True) as run:
        assert ci.main(["--fast"], root=tmp_path) == 0
    assert [call.args[0] for call in run.call_args_list] == ["docs", "lint", "types", "api"]
    assert run.call_args.kwargs["fast"] is True


def test_missing_tool_fails_with_installation_hint(tmp_path, capsys):
    with patch.object(importlib.util, "find_spec", return_value=None):
        assert ci.main(["--stage", "lint"], root=tmp_path) == 1
    assert "requirements-dev.txt" in capsys.readouterr().out


def test_test_stage_excludes_eval_and_redirects_writes(tmp_path):
    with patch.object(ci.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
        assert ci.main(["--stage", "test"], root=tmp_path) == 0
    command = run.call_args.args[0]
    assert command[command.index("-m", 3) + 1] == "not eval"
    assert run.call_args.kwargs["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
    assert ".ci" in " ".join(command)


def test_fast_rejects_conflicting_stage():
    with pytest.raises(SystemExit) as error:
        ci.main(["--fast", "--stage", "test"])
    assert error.value.code == 2


def test_mutation_requires_nonempty_all_killed_metadata(tmp_path, monkeypatch):
    import json

    for name in ("apps", "packages", "tests", "scripts"):
        (tmp_path / name).mkdir()
    for name in ("pyproject.toml", "pytest.ini"):
        (tmp_path / name).write_text("")
    monkeypatch.setattr(ci, "require", lambda name: True)
    monkeypatch.setattr(ci, "check_declarative_mutations", lambda root: True)
    (tmp_path / "apps/backend/odwolania2json").mkdir(parents=True)
    (tmp_path / "packages/contracts/odwolania2json_contracts").mkdir(parents=True)
    statuses = [1, 0]

    def execute(command, root):
        output = root / "mutants"
        output.mkdir()
        (output / "test.meta").write_text(
            json.dumps({"exit_code_by_key": dict(enumerate(statuses))})
        )
        return True

    monkeypatch.setattr(ci, "execute", execute)
    assert ci.main(["--stage", "mutation"], root=tmp_path) == 1
    statuses[:] = []
    assert ci.main(["--stage", "mutation"], root=tmp_path) == 1
    statuses[:] = [1, 1]
    assert ci.main(["--stage", "mutation"], root=tmp_path) == 0


def test_fast_api_selects_spec(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "require", lambda module: True)
    with patch.object(ci.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
        assert ci.main(["--fast", "--keep-going"], root=tmp_path) == 0
    assert run.call_args.args[0][-2:] == ["--stage", "spec"]


def test_declarative_variants_cover_digits_labels_and_field_types():
    import ast

    source = 'import re\npattern = re.compile(r"NIP: [0-9]{10}")\nvalue: str\n'
    variants = [ast.parse(text) for text in ci.declarative_variants(source)]
    rendered = [ast.unparse(tree) for tree in variants]
    assert any("NIP: [0-9]{20}" in text for text in rendered)
    assert any("XIP:" in text for text in rendered)
    assert any("value: int" in text for text in rendered)
