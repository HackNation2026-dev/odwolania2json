"""Punkt wejścia modułu: ``python -m odwolania2json``."""

import argparse
import sys

APP_NAME = "Odwołania2JSON"

__all__ = ["APP_NAME", "build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Buduje parser argumentów CLI."""
    parser = argparse.ArgumentParser(
        prog="odwolania2json",
        description=f"{APP_NAME} — konwerter PDF-ów spraw odwoławczych do ścisłego JSON.",
    )
    return parser


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


def main(argv: list[str] | None = None) -> int:
    """Uruchamia CLI i zwraca kod wyjścia procesu."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not arguments:
        parser.print_help()
        return 0
    parser.parse_args(arguments)
    return 0


if __name__ == "__main__":
    _use_utf8_output()
    raise SystemExit(main())
