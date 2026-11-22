"""Kopie robocze CI nie są dokumentacją repozytorium."""

import subprocess
import sys
import tempfile
from pathlib import Path


def test_docs_ignore_temporary_ci_copies():
    root = Path(__file__).resolve().parents[2]
    (root / ".ci").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root / ".ci") as directory:
        (Path(directory) / "broken.md").write_text("[broken](missing.md)\n")
        result = subprocess.run(
            [sys.executable, "scripts/verify_docs.py"], cwd=root, capture_output=True, text=True
        )
    assert result.returncode == 0, result.stdout + result.stderr


def test_docs_ignore_sdd_workspace():
    """Scratch SDD (.superpowers) to notatnik sterujący, nie dokumentacja repozytorium."""
    root = Path(__file__).resolve().parents[2]
    (root / ".superpowers").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root / ".superpowers") as directory:
        (Path(directory) / "broken.md").write_text("[broken](missing.md)\n")
        result = subprocess.run(
            [sys.executable, "scripts/verify_docs.py"], cwd=root, capture_output=True, text=True
        )
    assert result.returncode == 0, result.stdout + result.stderr


def test_docs_ignore_any_virtualenv_directory():
    """Środowiska `.venv*` (także `.venv-exp`) zawierają cudze pliki Markdown z własnymi linkami."""
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(dir=root, prefix=".venv-test-") as directory:
        (Path(directory) / "broken.md").write_text("[broken](missing.md)\n")
        result = subprocess.run(
            [sys.executable, "scripts/verify_docs.py"], cwd=root, capture_output=True, text=True
        )
    assert result.returncode == 0, result.stdout + result.stderr


def test_docs_ignore_vendored_third_party_directories():
    """Katalogi `vendor` i `site-packages` to cudze pliki Markdown z własnymi linkami."""
    root = Path(__file__).resolve().parents[2]
    for name in ("vendor", "site-packages"):
        with tempfile.TemporaryDirectory(dir=root, prefix=".ci-") as directory:
            third_party = Path(directory) / name
            third_party.mkdir()
            (third_party / "broken.md").write_text("[broken](missing.md)\n")
            result = subprocess.run(
                [sys.executable, "scripts/verify_docs.py"], cwd=root, capture_output=True, text=True
            )
        assert result.returncode == 0, result.stdout + result.stderr
