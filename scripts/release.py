#!/usr/bin/env python3
"""Sprawdza i buduje wydanie pip; opcjonalnie tworzy wyłącznie lokalny tag."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def command(args: list[str], root: Path) -> str:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        args,
        cwd=root,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.stdout:
        print(result.stdout, end="")
    return result.stdout or ""


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", action="store_true", help="utwórz lokalny tag po udanej budowie")
    args = parser.parse_args(argv)
    root = root or Path(__file__).resolve().parents[1]
    try:
        if command(["git", "status", "--porcelain", "--untracked-files=all"], root).strip():
            raise ValueError("repozytorium nie jest czyste (także pliki nieśledzone)")
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError("VERSION musi mieć format X.Y.Z")
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        if not re.search(rf"^## {re.escape(version)}(?:\s+—[^\n]+)?\s*$", changelog, re.MULTILINE):
            raise ValueError("brak dokładnego nagłówka VERSION w CHANGELOG.md")
        command([sys.executable, str(root / "scripts/ci.py"), "--stage", "all"], root)
        (root / ".ci").mkdir(exist_ok=True)
        # Setuptools zapisuje egg-info i build przy źródłach; budujemy kopie.
        with tempfile.TemporaryDirectory(dir=root / ".ci", prefix="release-") as temporary:
            staging = Path(temporary)
            output = staging / "dist"
            for relative in ("packages/contracts", "apps/backend"):
                source = staging / relative
                shutil.copytree(
                    root / relative,
                    source,
                    ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", "build"),
                )
                command([sys.executable, "-m", "build", "--outdir", str(output), str(source)], root)
            artifacts = sorted(output.glob("*"))
            if not artifacts or not any(p.suffix == ".whl" for p in artifacts):
                raise ValueError("budowanie nie utworzyło pakietów pip")
            # Wersje pakietów muszą zgadzać się z tagiem, nie tylko z changelogiem.
            if any(
                not (
                    f"-{version}-" in path.name
                    if path.suffix == ".whl"
                    else path.name.endswith(f"-{version}.tar.gz")
                )
                for path in artifacts
            ):
                raise ValueError(
                    "wersja zbudowanego pakietu różni się od VERSION; popraw __version__ pakietów"
                )
            destination = root / "dist"
            destination.mkdir(exist_ok=True)
            for artifact in artifacts:
                target = destination / artifact.name
                with tempfile.NamedTemporaryFile(dir=destination, delete=False) as stream:
                    temporary_path = Path(stream.name)
                    try:
                        stream.write(artifact.read_bytes())
                        stream.flush()
                        os.fsync(stream.fileno())
                    except BaseException:
                        temporary_path.unlink(missing_ok=True)
                        raise
                try:
                    os.replace(temporary_path, target)
                finally:
                    temporary_path.unlink(missing_ok=True)
                print(f"SHA-256 {hashlib.sha256(target.read_bytes()).hexdigest()}  {target.name}")
        if command(["git", "status", "--porcelain", "--untracked-files=all"], root).strip():
            raise ValueError("stan Git zmienił się podczas wydania")
        if args.tag:
            command(["git", "tag", f"v{version}"], root)
        else:
            print(f"OK dry-run: pakiety w dist/, tag v{version} nie został utworzony")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError) and error.stdout:
            print(error.stdout)
        print(
            f"FAIL wydanie: {error}; instalacja narzędzi: python -m pip install -r requirements-dev.txt"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
