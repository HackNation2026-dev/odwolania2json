"""Wspólna konfiguracja testów: katalog `tests/` na ścieżce importu.

Dzięki temu testy jednostkowe i integracyjne korzystają z tych samych pomocników
(`support.pdfs`, `support.llm`) bez kopiowania ich między katalogami.
"""

from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)
