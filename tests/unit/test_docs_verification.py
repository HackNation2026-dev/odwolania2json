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
