"""Strażnik przecieku: zestaw skanów powstaje wyłącznie ze spraw rozwojowych (plan 0.2, P0 pkt 2)."""
from __future__ import annotations

import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2] / "harness"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

import common  # noqa: E402,F401  (dodaje backend do sys.path)
from odwolania2json.dataset import load_split  # noqa: E402


class LeakError(RuntimeError):
    """Próba użycia sprawy spoza zbioru rozwojowego."""


def assert_dev_case(case_id: str) -> None:
    sp = load_split()
    if case_id in sp.kontrolny:
        raise LeakError(f"sprawa kontrolna zablokowana: {case_id}")
    if case_id not in sp.rozwojowy:
        raise LeakError(f"sprawa spoza zbioru rozwojowego: {case_id}")


def assert_manifest_clean(manifest: dict) -> None:
    for e in manifest["entries"]:
        assert_dev_case(e["case_id"])
        if e["parent_split"] != "rozwojowy":
            raise LeakError(f"zły podział rodzica: {e['id']}")
