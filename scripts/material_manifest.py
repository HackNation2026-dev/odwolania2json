#!/usr/bin/env python3
"""Zapisuje sumy oryginalnych materiałów; nie zmienia źródeł."""

import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = [root / "docs/01-zadanie/zrodla"] + [
    p for p in (root / "docs/02-materialy").glob("organizator*") if p.is_dir()
]
files = []
for folder in paths:
    for p in sorted(folder.rglob("*")):
        if p.is_file():
            files.append(
                {
                    "path": p.relative_to(root).as_posix(),
                    "bytes": p.stat().st_size,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                }
            )
p = root / "docs/02-materialy/manifest.json"
p.write_text(json.dumps({"format_version": 1, "files": files}, ensure_ascii=False, indent=2) + "\n")
print(f"Manifest: {len(files)} plików")
