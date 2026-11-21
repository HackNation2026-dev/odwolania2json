"""Test słownika przyczyn odwołania (organizator, rewizja main-7590db8)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from odwolania2json_contracts import APPEAL_REASONS
from odwolania2json_contracts.powody import APPEAL_REASONS as POWODY_REASONS

REPO_ROOT = Path(__file__).resolve().parents[2]
DICT_PATH = (
    REPO_ROOT
    / "docs"
    / "02-materialy"
    / "organizator-uzp-aktualizacje"
    / "main-7590db8"
    / "oczekiwane-json"
    / "czynnosc_powod_id_dict.md"
)
SPEC_PATH = REPO_ROOT / "packages" / "contracts" / "odwolania2json_contracts" / "openapi.yaml"


def _organizer_reasons() -> dict[int, str]:
    reasons: dict[int, str] = {}
    for line in DICT_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.fullmatch(r"(\d+)=(.*)", line)
        assert match is not None, f"Nieparsowalna linia słownika: {line!r}"
        reasons[int(match.group(1))] = match.group(2).strip()
    return reasons


def test_powody_match_organizer_dictionary():
    assert _organizer_reasons() == APPEAL_REASONS


def test_powod_ids_are_1_to_12():
    assert sorted(APPEAL_REASONS) == list(range(1, 13))


def test_powody_exported_from_package_match_module():
    assert POWODY_REASONS is APPEAL_REASONS


def test_spec_enum_matches_powody():
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    schema = spec["components"]["schemas"]["OdwolanieKIO"]
    enum = schema["properties"]["czynnosc_opis"]["enum"]
    assert None in enum
    assert [value for value in enum if value is not None] == list(APPEAL_REASONS.values())
