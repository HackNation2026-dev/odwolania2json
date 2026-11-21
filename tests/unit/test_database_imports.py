"""Sterowniki są szczegółem jednego adaptera, a nie kodu aplikacji."""

import ast
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "apps/backend/odwolania2json/db/engine.py"


def forbidden_imports(source: str) -> list[str]:
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return [
        name
        for name in names
        if name.split(".")[0] in {"sqlite3", "pg8000"} or name.split(".")[0].startswith("psycopg")
    ]


@pytest.mark.parametrize(
    "source",
    [
        "import sqlite3 as db",
        "from sqlite3.dbapi2 import connect",
        "import pg8000.native",
        "from psycopg import connect",
        "import psycopg2",
        "import psycopg_binary",
        "from psycopg_pool import ConnectionPool",
    ],
)
def test_import_scan_recognizes_driver_aliases_and_submodules(source):
    assert forbidden_imports(source)


def test_backend_uses_drivers_only_in_engine_adapter():
    roots = [ROOT / "apps/backend/odwolania2json", ROOT / "packages/contracts"]
    violations = [
        str(path.relative_to(ROOT))
        for root in roots
        for path in root.rglob("*.py")
        if path != ADAPTER and forbidden_imports(path.read_text(encoding="utf-8"))
    ]
    assert violations == []


def test_engine_adapter_is_the_single_place_that_imports_a_driver():
    assert forbidden_imports(ADAPTER.read_text(encoding="utf-8")) == ["sqlite3"]


def test_ruff_bans_drivers_everywhere_except_engine_adapter():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["ruff"]
    banned = set(config["lint"]["flake8-tidy-imports"]["banned-api"])
    assert {"sqlite3", "pg8000", "psycopg", "psycopg2"} <= banned
    assert "TID" in config["lint"]["select"]
    exceptions = {
        path for path, rules in config["lint"]["per-file-ignores"].items() if "TID251" in rules
    }
    assert exceptions == {"apps/backend/odwolania2json/db/engine.py"}


def test_requirements_do_not_pull_postgres_drivers():
    for name in ("apps/backend/requirements.txt", "requirements.txt", "requirements-dev.txt"):
        path = ROOT / name
        if path.exists():
            lowered = path.read_text(encoding="utf-8").lower()
            assert "pg8000" not in lowered
            assert "psycopg" not in lowered
