"""Ustawia ścieżki importu: moduły harnessu są płaskie, a backend produkcyjny tylko do odczytu."""

import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
for p in (HARNESS, HARNESS.parents[2] / "apps" / "backend"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
