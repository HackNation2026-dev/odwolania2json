#!/usr/bin/env python3
"""Waliduje kontrakt danych: specyfikację OpenAPI, modele i aplikację FastAPI.

Uruchomienie:

    python scripts/validate_api.py [--stage spec|app|all]

Skrypt nigdy nie zapisuje w repozytorium — wyłącznie czyta i porównuje.
Raporty ``OK``/``FAIL`` trafiają na standardowe wyjście.
Kody wyjścia: 0 — zgodność, 1 — niezgodność.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "packages" / "contracts" / "odwolania2json_contracts" / "openapi.yaml"
MODELS_PATH = ROOT / "packages" / "contracts" / "odwolania2json_contracts" / "models.py"
GENERATE_SCRIPT = ROOT / "scripts" / "generate_contracts.py"
APP_MODULE = "odwolania2json.api.app"
HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")

# Raporty zawierają polskie znaki; bez tego konsola Windows (cp1252) zgłosiłaby błąd kodowania.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _ok(description: str) -> None:
    print(f"OK {description}")


def _fail(description: str, reason: str) -> None:
    print(f"FAIL {description} {reason}")


def _load_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def _operations(spec: dict) -> dict[tuple[str, str], dict]:
    operations: dict[tuple[str, str], dict] = {}
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method in HTTP_METHODS and isinstance(operation, dict):
                operations[(path, method)] = operation
    return operations


def _schema_refs(spec: dict) -> set[str]:
    """Nazwy schematów składowych, do których odwołuje się dokumentacja."""
    refs: set[str] = set()
    prefix = "#/components/schemas/"
    stack: list[object] = [spec]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith(prefix):
                refs.add(ref[len(prefix) :])
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return refs


def check_spec() -> bool:
    """Sprawdza specyfikację i zgodność modeli; True — wszystko zgodne."""
    try:
        spec = _load_spec()
        validate(spec)
        _ok(f"specyfikacja {SPEC_PATH.relative_to(ROOT).as_posix()} jest poprawnym OpenAPI 3.1")
    except Exception as error:  # noqa: BLE001 - raportujemy dowolny błąd walidacji
        _fail("walidacja specyfikacji", f"{error}")
        return False

    with tempfile.TemporaryDirectory() as temporary:
        regenerated = Path(temporary) / "models.py"
        result = subprocess.run(
            [sys.executable, str(GENERATE_SCRIPT), "--output", str(regenerated)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            details = (result.stdout + result.stderr).strip()
            _fail("regeneracja modeli", details)
            return False
        if regenerated.read_bytes() != MODELS_PATH.read_bytes():
            _fail(
                "modele zgodne ze specyfikacją",
                "modele nie zgadzają się ze specyfikacją, uruchom scripts/generate_contracts.py",
            )
            return False
    _ok(f"modele zgodne ze specyfikacją ({MODELS_PATH.relative_to(ROOT).as_posix()})")
    return True


def check_app() -> bool:
    """Porównuje ``app.openapi()`` aplikacji FastAPI ze specyfikacją."""
    try:
        exists = importlib.util.find_spec(APP_MODULE) is not None
    except (ImportError, ModuleNotFoundError):
        exists = False
    except Exception as error:  # noqa: BLE001 - pakiet aplikacji istnieje, ale nie działa
        _fail("import aplikacji", f"{type(error).__name__}: {error}")
        return False
    if not exists:
        print("pominięto: aplikacja niedostępna")
        return True

    try:
        from odwolania2json.api.app import app  # noqa: PLC0415 - import warunkowy
    except Exception as error:  # noqa: BLE001 - aplikacja istnieje, ale nie działa
        _fail("import aplikacji", f"{type(error).__name__}: {error}")
        return False

    spec = _load_spec()
    app_spec = app.openapi()
    problems: list[str] = []

    spec_operations = _operations(spec)
    app_operations = _operations(app_spec)
    for key in sorted(set(spec_operations) | set(app_operations)):
        path, method = key
        if key not in app_operations:
            problems.append(f"brak ścieżki {path} [{method.upper()}]")
        elif key not in spec_operations:
            problems.append(f"nadmiarowa ścieżka {path} [{method.upper()}]")
        else:
            expected = spec_operations[key].get("operationId")
            actual = app_operations[key].get("operationId")
            if expected != actual:
                problems.append(f"różny operationId dla {path} [{method.upper()}]")

    spec_schemas = set((spec.get("components") or {}).get("schemas") or {})
    app_schemas = set((app_spec.get("components") or {}).get("schemas") or {})
    for name in sorted(spec_schemas - app_schemas):
        problems.append(f"brak schematu składowego {name}")
    for name in sorted(_schema_refs(app_spec) - app_schemas):
        problems.append(f"odwołanie do nieznanego schematu {name}")

    if problems:
        _fail("zgodność aplikacji ze specyfikacją", "; ".join(problems))
        return False
    _ok("aplikacja jest zgodna ze specyfikacją")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Waliduje kontrakt danych Odwołania2JSON.")
    parser.add_argument(
        "--stage",
        choices=("spec", "app", "all"),
        default="spec",
        help="etap walidacji: spec (domyślnie), app, all",
    )
    args = parser.parse_args(argv)

    ok = True
    if args.stage in ("spec", "all"):
        ok = check_spec() and ok
    if args.stage in ("app", "all"):
        ok = check_app() and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
