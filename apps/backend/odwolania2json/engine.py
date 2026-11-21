"""Pętla `process`: PDF-y z katalogu wejściowego → wyniki JSON w katalogu wyjściowym.

Atrapa silnika nie czyta treści PDF-a, więc klasyfikacja i ekstrakcja przychodzą
dopiero w późniejszych zadaniach. CLI obsługuje już oba wyniki, a dokument obcy
albo bez klasyfikacji dostaje `{}` pod nazwą wejścia, żeby każde wejście miało wynik.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from .loader import DocumentClass, result_name_for

__all__ = ["StubEngine", "run_process", "write_json_atomic"]

EXIT_OK = 0
EXIT_DOCUMENT_ERRORS = 1
EXIT_USAGE = 2


class StubEngine:
    """Atrapa silnika: zawsze zwraca pusty wynik bez klasyfikacji."""

    def process(self, pdf: Path) -> tuple[dict[str, object], DocumentClass | None]:
        return {}, None


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    """Zapisuje JSON przez plik tymczasowy, `fsync` i `os.replace`.

    Dlaczego: przerwany zapis nie może zostawić częściowego pliku wyniku, który
    wyglądałby jak poprawny. Plik tymczasowy leży w tym samym katalogu, bo
    `os.replace` jest atomowe tylko w obrębie jednego systemu plików.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        tmp_path.unlink(missing_ok=True)


def run_process(input_dir: Path, output_dir: Path, engine: StubEngine) -> int:
    """Przetwarza wszystkie PDF-y z `input_dir` i zwraca kod wyjścia procesu.

    Dlaczego błąd jednego pliku nie przerywa pętli: jeden uszkodzony dokument
    nie powinien blokować wyników pozostałych spraw. Błąd trafia do stderr, a plik
    wyniku dla tego dokumentu nie powstaje, zamiast być zastąpiony zmyśleniem.
    """
    if not input_dir.is_dir():
        print(f"błąd: katalog wejściowy nie istnieje: {input_dir}", file=sys.stderr)
        return EXIT_USAGE
    failures = 0
    for pdf in sorted(input_dir.rglob("*.pdf")):
        target = output_dir / pdf.relative_to(input_dir).parent / result_name_for(pdf.name)
        try:
            payload, document_class = engine.process(pdf)
            if document_class in (None, "obcy"):
                payload = {}
            write_json_atomic(target, payload)
        except Exception as error:
            failures += 1
            print(f"błąd: {pdf}: {error}", file=sys.stderr)
    return EXIT_DOCUMENT_ERRORS if failures else EXIT_OK
