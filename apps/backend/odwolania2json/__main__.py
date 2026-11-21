"""Punkt wejścia modułu: ``python -m odwolania2json``.

Parser i funkcja ``main`` mieszkają w :mod:`odwolania2json.cli`; ten moduł
jedynie je udostępnia, żeby ``python -m odwolania2json`` i testy szkieletu
widziały to samo API.
"""

import sys

from .cli import APP_NAME, build_parser, main

__all__ = ["APP_NAME", "build_parser", "main"]


def _use_utf8_output() -> None:
    """Wymusza UTF-8 na wyjściu procesu, aby polskie znaki nie przerywały pracy konsoli."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


if __name__ == "__main__":
    _use_utf8_output()
    raise SystemExit(main())
