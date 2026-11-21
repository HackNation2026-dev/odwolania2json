"""Wydanie lokalne nie publikuje pakietów ani nie wysyła tagów."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import release


@pytest.fixture
def repository(tmp_path):
    (tmp_path / "VERSION").write_text("1.2.3\n")
    (tmp_path / "CHANGELOG.md").write_text("## 1.2.3 — 2026-11-21\n\n- Zmiana.\n")
    for folder in ("apps/backend", "packages/contracts"):
        (tmp_path / folder).mkdir(parents=True)
        (tmp_path / folder / "pyproject.toml").write_text("[project]\nname='example'\n")
    return tmp_path


def successful_command(command, **kwargs):
    if "build" in command:
        output = Path(command[command.index("--outdir") + 1])
        output.mkdir(parents=True, exist_ok=True)
        source = Path(command[-1]).name
        (output / f"{source}-1.2.3-py3-none-any.whl").write_bytes(b"package")
        (output / f"{source}-1.2.3.tar.gz").write_bytes(b"package")
    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def test_dry_run_builds_without_git_mutation(repository, capsys):
    with patch.object(release.subprocess, "run", side_effect=successful_command) as run:
        assert release.main([], root=repository) == 0
    commands = [call.args[0] for call in run.call_args_list]
    assert any(
        "ci.py" in " ".join(command) and command[-2:] == ["--stage", "all"] for command in commands
    )
    assert sum("build" in command for command in commands) == 2
    assert not any(
        "tag" in command or "push" in command or "upload" in command for command in commands
    )
    assert "SHA-256" in capsys.readouterr().out


def test_dirty_tree_stops_before_ci_or_build(repository):
    with patch.object(
        release.subprocess,
        "run",
        return_value=subprocess.CompletedProcess([], 0, stdout=" M VERSION\n"),
    ) as run:
        assert release.main([], root=repository) == 1
    assert run.call_count == 1
    assert not (repository / "dist").exists()


def test_version_requires_exact_changelog_heading(repository):
    (repository / "CHANGELOG.md").write_text("## 1.2.30\n")
    with patch.object(release.subprocess, "run", side_effect=successful_command) as run:
        assert release.main([], root=repository) == 1
    assert not any("build" in call.args[0] for call in run.call_args_list)


def test_ci_failure_prevents_build_and_tag(repository):
    def command(args, **kwargs):
        if "ci.py" in " ".join(args):
            raise subprocess.CalledProcessError(1, args, output="FAIL test\n")
        return subprocess.CompletedProcess(args, 0, stdout="")

    with patch.object(release.subprocess, "run", side_effect=command) as run:
        assert release.main(["--tag"], root=repository) == 1
    assert not any("build" in call.args[0] or "tag" in call.args[0] for call in run.call_args_list)


def test_tag_is_local_and_created_after_build(repository):
    with patch.object(release.subprocess, "run", side_effect=successful_command) as run:
        assert release.main(["--tag"], root=repository) == 0
    assert run.call_args.args[0] == ["git", "tag", "v1.2.3"]


def test_build_failure_does_not_tag(repository):
    def command(args, **kwargs):
        if "build" in args:
            raise subprocess.CalledProcessError(1, args, output="FAIL build\n")
        return successful_command(args, **kwargs)

    with patch.object(release.subprocess, "run", side_effect=command) as run:
        assert release.main(["--tag"], root=repository) == 1
    assert not any("tag" in call.args[0] for call in run.call_args_list)


def test_artifact_version_requires_exact_match(repository):
    def command(args, **kwargs):
        result = successful_command(args, **kwargs)
        if "build" in args:
            output = Path(args[args.index("--outdir") + 1])
            for artifact in output.glob("*"):
                artifact.rename(artifact.with_name(artifact.name.replace("1.2.3", "1.2.30")))
        return result

    with patch.object(release.subprocess, "run", side_effect=command):
        assert release.main([], root=repository) == 1
    assert not (repository / "dist").exists()
