"""Loader zestawu skanów dla grup A–D: zawsze przechodzi przez strażnika przecieku."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from guard import assert_manifest_clean

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ScanItem:
    id: str
    variant: str
    profile: str
    case_id: str
    document_class: str
    input_kind: str
    pdf: Path
    ref: Path
    entry: dict

    def reference(self) -> dict:
        return json.loads(self.ref.read_text(encoding="utf-8"))


def load_zestaw(variants: list[str] | None = None) -> list[ScanItem]:
    m = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert_manifest_clean(m)
    out = []
    for e in m["entries"]:
        if variants and e["variant"] not in variants:
            continue
        out.append(ScanItem(e["id"], e["variant"], e["profile"], e["case_id"], e["document_class"], e["input_kind"],
                            ROOT / e["pdf"], ROOT / e["ref"], e))
    return out
