"""Odświeża migawkę schematów UI z niezmienionego kontraktu silnika."""
import json
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[3]
source = root / "packages/contracts/odwolania2json_contracts/openapi.yaml"
target = root / "apps/web/src/lib/api/contract.generated.json"
target.write_text(json.dumps(yaml.safe_load(source.read_text())["components"]["schemas"], ensure_ascii=False, indent=2) + "\n")
