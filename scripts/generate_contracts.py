#!/usr/bin/env python3
"""Generuje modele pydantic z ``packages/contracts/openapi.yaml``.

Uruchomienie:

    python scripts/generate_contracts.py [--output PLIK] [--spec PLIK]

Skrypt waliduje specyfikację, uruchamia ``datamodel-code-generator`` i zapisuje
wynik (domyślnie ``packages/contracts/odwolania2json_contracts/models.py``).
Kod wyjścia: 0 — sukces, 1 — błąd.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "packages" / "contracts" / "openapi.yaml"
PACKAGE_DIR = ROOT / "packages" / "contracts" / "odwolania2json_contracts"
PACKAGED_SPEC_PATH = PACKAGE_DIR / "openapi.yaml"
MODELS_PATH = PACKAGE_DIR / "models.py"

GENERATOR_FLAGS = (
    "--input-file-type",
    "openapi",
    "--output-model-type",
    "pydantic_v2.BaseModel",
    "--enum-field-as-literal",
    "all",
    "--allow-population-by-field-name",
    "--target-python-version",
    "3.13",
    "--use-standard-collections",
    "--field-constraints",
    "--use-annotated",
    "--disable-timestamp",
    "--formatters",
    "builtin",
)


def _fail(message: str) -> int:
    print(f"FAIL {message}", file=sys.stderr)
    return 1


def validate_spec(spec_path: Path) -> int:
    """Waliduje specyfikację OpenAPI; 0 — poprawna."""
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        validate(spec)
    except Exception as error:  # noqa: BLE001 - skrypt raportuje dowolny błąd walidacji
        return _fail(f"specyfikacja {spec_path} jest niepoprawna: {error}")
    return 0


def sync_packaged_spec(spec_path: Path) -> int:
    """Kopiuje specyfikację do pakietu, aby trafiła do koła (package-data)."""
    content = spec_path.read_bytes()
    if PACKAGED_SPEC_PATH.is_file() and PACKAGED_SPEC_PATH.read_bytes() == content:
        return 0
    PACKAGED_SPEC_PATH.write_bytes(content)
    return 0


def generate(spec_path: Path, output_path: Path) -> int:
    """Uruchamia generator i zapisuje modele; 0 — sukces."""
    command = [
        sys.executable,
        "-m",
        "datamodel_code_generator",
        "--input",
        str(spec_path),
        *GENERATOR_FLAGS,
        "--output",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        details = (result.stdout + result.stderr).strip()
        return _fail(f"generowanie modeli nie powiodło się: {details}")
    # Generator zapisuje plik z końcami linii systemu operacyjnego; repo wymaga LF.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = output_path.read_bytes().replace(b"\r\n", b"\n")
    output_path.write_bytes(content)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generuje modele pydantic ze specyfikacji OpenAPI.")
    parser.add_argument("--spec", type=Path, default=SPEC_PATH, help="plik ze specyfikacją OpenAPI")
    parser.add_argument("--output", type=Path, default=MODELS_PATH, help="plik z wygenerowanymi modelami")
    args = parser.parse_args(argv)

    spec_path: Path = args.spec.resolve()
    output_path: Path = args.output.resolve()
    if not spec_path.is_file():
        return _fail(f"brak specyfikacji: {spec_path}")
    if validate_spec(spec_path) != 0:
        return 1
    if generate(spec_path, output_path) != 0:
        return 1
    if spec_path == SPEC_PATH.resolve() and sync_packaged_spec(spec_path) != 0:
        return 1
    print(f"OK modele zapisane w {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
