"""Odświeża migawkę schematów UI z niezmienionego kontraktu silnika."""

import json
from pathlib import Path
from typing import cast

import yaml

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "packages/contracts/odwolania2json_contracts/openapi.yaml"
TARGET = ROOT / "apps/web/src/lib/api/contract.generated.json"

type Schemas = dict[str, object]


def load_schemas(source: Path) -> Schemas:
    """Czyta schematy komponentów z OpenAPI bez ich zmieniania."""
    document = cast(
        "dict[str, dict[str, Schemas]]",
        yaml.safe_load(source.read_text(encoding="utf-8")),
    )
    return document["components"]["schemas"]


def main() -> None:
    """Zapisuje migawkę schematów jako JSON używany przez GUI."""
    schemas = load_schemas(SOURCE)
    text = json.dumps(schemas, ensure_ascii=False, indent=2)
    TARGET.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
