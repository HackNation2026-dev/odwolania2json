#!/usr/bin/env python3
"""Lokalne kontrole jakości; artefakty trafiają wyłącznie do .ci/."""

from __future__ import annotations

import argparse
import ast
import configparser
from collections.abc import Iterator
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def environment(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(root / "apps/backend"), str(root / "packages/contracts"), env.get("PYTHONPATH", "")]
    )
    env["TMPDIR"] = str(root / ".ci/tmp")
    env["XDG_CACHE_HOME"] = str(root / ".ci/cache")
    return env


def execute(command: list[str], root: Path) -> bool:
    try:
        result = subprocess.run(command, cwd=root, env=environment(root), check=False)
    except OSError as error:
        print(f"FAIL uruchomienie: {error}")
        return False
    return result.returncode == 0


def require(module: str) -> bool:
    if importlib.util.find_spec(module) is not None:
        return True
    print(
        f"FAIL brak {module}; instalacja: python -m pip install -r requirements-dev.txt "
        "-r apps/backend/requirements.txt"
    )
    return False


def declarative_variants(source: str) -> Iterator[str]:
    """Mutmut 3 pomija poziom modułu; uzupełniamy wzorce i deklaracje typów."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "re":
                if node.func.attr == "compile" and node.args:
                    literal = node.args[0]
                    if isinstance(literal, ast.Constant) and isinstance(literal.value, str):
                        value = literal.value
                        # Każda zmiana dotyczy jednej cyfry, litery etykiety lub formatu.
                        for index, char in enumerate(value):
                            changed = (
                                str((int(char) + 1) % 10)
                                if char.isascii() and char.isdigit()
                                else ("X" if char.isalpha() else "*" if char == "+" else "")
                            )
                            if changed != char:
                                candidate = value[:index] + changed + value[index + 1 :]
                                try:
                                    re.compile(candidate)
                                except re.error:
                                    # Niepoprawny wzorzec nie bada odporności dopasowania.
                                    continue
                                replacement = ast.Constant(candidate)
                                old = node.args[0]
                                node.args[0] = replacement
                                yield ast.unparse(tree)
                                node.args[0] = old
        if isinstance(node, ast.Name) and node.id in ("str", "int", "float", "bool"):
            old_name = node.id
            node.id = "int" if old_name == "str" else "str"
            yield ast.unparse(tree)
            node.id = old_name
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                value = keyword.value
                if (
                    keyword.arg == "pattern"
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    original = value.value
                    for index, char in enumerate(original):
                        if char.isascii() and char.isdigit():
                            value.value = (
                                original[:index] + str((int(char) + 1) % 10) + original[index + 1 :]
                            )
                            yield ast.unparse(tree)
                    value.value = original


def check_declarative_mutations(root: Path) -> bool:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit",
        "tests/contract",
        "-m",
        "not eval",
        "-o",
        "cache_dir=.ci/pytest",
    ]
    if not execute(command, root):
        print("FAIL mutacje deklaracji: testy bazowe nie przechodzą")
        return False
    total = 0
    failed = 0
    for relative in (
        "apps/backend/odwolania2json/domain/normalize.py",
        "packages/contracts/odwolania2json_contracts/models.py",
    ):
        path = root / relative
        original = path.read_text(encoding="utf-8")
        try:
            for source in declarative_variants(original):
                path.write_text(source, encoding="utf-8")
                result = subprocess.run(
                    command,
                    cwd=root,
                    env=environment(root),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                total += 1
                # Błąd importu lub składni nie dowodzi wykrycia zmiany przez asercję.
                if result.returncode != 1:
                    failed += 1
                    print(f"FAIL mutant deklaracji {relative} #{total}: kod {result.returncode}")
        finally:
            path.write_text(original, encoding="utf-8")
    print(f"Mutanty deklaracji: {total}, niewykryte lub błędne: {failed}")
    return total > 0 and failed == 0


def mutation(root: Path) -> bool:
    if not require("mutmut"):
        return False
    # Mutmut zapisuje kopie źródeł i metadane względem cwd; izolujemy cały przebieg.
    with tempfile.TemporaryDirectory(dir=root / ".ci", prefix="mutation-") as temporary:
        workspace = Path(temporary)
        for name in ("apps", "packages", "tests", "scripts"):
            shutil.copytree(
                root / name,
                workspace / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", "build"),
            )
        for name in ("pyproject.toml", "pytest.ini"):
            shutil.copy2(root / name, workspace / name)
        # Testy kontraktowe czytają wzorce JSON i słownik; oryginały tylko odczytujemy.
        materials = root / "docs/02-materialy"
        for source in materials.rglob("*"):
            if source.is_file() and source.suffix in (".json", ".md"):
                destination = workspace / source.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        (workspace / ".ci/tmp").mkdir(parents=True)
        config = configparser.ConfigParser()
        config.read(workspace / "pytest.ini")
        if not config.has_section("pytest"):
            config.add_section("pytest")
        config["pytest"]["addopts"] = '-q -m "not eval" -o cache_dir=.ci/pytest'
        config["pytest"]["pythonpath"] = "apps/backend packages/contracts"
        with (workspace / "pytest.ini").open("w", encoding="utf-8") as stream:
            config.write(stream)
        # Mutmut 3 rozpoznaje prefiks src/ przy budowaniu identyfikatorów modułów.
        for relative, package in (
            ("apps/backend", "odwolania2json"),
            ("packages/contracts", "odwolania2json_contracts"),
        ):
            shutil.copytree(workspace / relative / package, workspace / "src" / package)
        config["pytest"]["pythonpath"] = "src"
        with (workspace / "pytest.ini").open("w", encoding="utf-8") as stream:
            config.write(stream)
        if not execute([sys.executable, "-m", "mutmut", "run"], workspace):
            return False
        # Sam kod wyjścia mutmut run nie stanowi dowodu zabicia mutantów.
        codes: list[int | None] = []
        for path in (workspace / "mutants").rglob("*.meta"):
            data = json.loads(path.read_text(encoding="utf-8"))
            codes.extend(data["exit_code_by_key"].values())
        print(f"Mutanty: {len(codes)}, zabite: {codes.count(1)}")
        config["pytest"]["pythonpath"] = "apps/backend packages/contracts"
        with (workspace / "pytest.ini").open("w", encoding="utf-8") as stream:
            config.write(stream)
        declarations_ok = check_declarative_mutations(workspace)
        return bool(codes) and all(code == 1 for code in codes) and declarations_ok


def run_stage(stage: str, root: Path, *, fast: bool) -> bool:
    python = sys.executable
    if stage == "docs":
        return execute([python, "scripts/verify_docs.py"], root)
    if stage == "lint":
        if not require("ruff"):
            return False
        return execute([python, "-m", "ruff", "check", "--no-cache", "."], root) and execute(
            [python, "-m", "ruff", "format", "--check", "--no-cache", "."], root
        )
    if stage == "types":
        return require("mypy") and execute(
            [python, "-m", "mypy", "--strict", "--cache-dir", ".ci/mypy", "apps/", "packages/"],
            root,
        )
    if stage == "api":
        return all(
            require(name) for name in ("yaml", "openapi_spec_validator", "datamodel_code_generator")
        ) and execute(
            [python, "scripts/validate_api.py", "--stage", "spec" if fast else "all"], root
        )
    if stage == "test":
        return require("pytest") and execute(
            [
                python,
                "-m",
                "pytest",
                "-m",
                "not eval",
                "-o",
                "cache_dir=.ci/pytest",
                "--basetemp",
                str(root / ".ci/pytest-tmp"),
            ],
            root,
        )
    return mutation(root)


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    stages = ("docs", "lint", "types", "api", "test", "mutation")
    parser.add_argument("--stage", choices=(*stages, "all"), default="all")
    parser.add_argument("--fast", action="store_true", help="docs, lint, types, api spec")
    parser.add_argument("--keep-going", action="store_true", help="kontynuuj po błędzie")
    args = parser.parse_args(argv)
    if args.fast and args.stage != "all":
        parser.error("--fast wymaga --stage all (domyślny)")
    root = root or Path(__file__).resolve().parents[1]
    selected = stages[:4] if args.fast else stages if args.stage == "all" else (args.stage,)
    (root / ".ci/tmp").mkdir(parents=True, exist_ok=True)
    failed = False
    for stage in stages:
        if stage not in selected or (failed and not args.keep_going):
            print(f"SKIP {stage:8} 0.00 s — niewybrany lub zatrzymany po błędzie", flush=True)
            continue
        started = time.monotonic()
        try:
            ok = run_stage(stage, root, fast=args.fast)
        except (OSError, ValueError, KeyError) as error:
            print(f"FAIL {error}")
            ok = False
        print(f"{'OK' if ok else 'FAIL'} {stage:8} {time.monotonic() - started:.2f} s", flush=True)
        failed = failed or not ok
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
