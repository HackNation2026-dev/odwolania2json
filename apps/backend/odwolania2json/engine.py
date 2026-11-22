"""Silnik `process`: PDF-y z katalogu wejściowego → wyniki JSON i raport wsadu.

Polityka eksportu (ADR-006):
- dla każdego PDF-a wejściowego powstaje plik wyniku, także przy błędzie;
- dokument obcy to `{}`; błąd techniczny to `{}` (przełącznik `error_export`),
  wpis w `report.jsonl` i niezerowy kod wyjścia wsadu; nigdy zmyślone dane;
- dokument niejednoznaczny dostaje najlepszą klasę; cytat i walidacja pól nie
  blokują eksportu, tylko zostawiają flagi w raporcie;
- poprzedni plik wyniku nie jest usuwany, gdy nowy zapis się nie powiódł.

Raport nie zawiera treści dokumentów ani sekretów: tylko ścieżki plików, kody,
opisy składane przez program i ścieżki pól.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from .errors import ProcessingError
from .extract.pipeline import PageText, document_text, extract
from .extract.ports import JsonLlm, PageOcr
from .loader import DocumentClass, result_name_for
from .pdf.reader import DEFAULT_MAX_PAGES, PdfDocument, diagnose_page

__all__ = [
    "EXIT_DOCUMENT_ERRORS",
    "EXIT_OK",
    "EXIT_USAGE",
    "REPORT_NAME",
    "DocumentEngine",
    "DocumentOutcome",
    "Engine",
    "EngineLimits",
    "ErrorExport",
    "Issue",
    "StubEngine",
    "find_pdfs",
    "run_process",
    "write_json_atomic",
]

EXIT_OK = 0
EXIT_DOCUMENT_ERRORS = 1
EXIT_USAGE = 2
REPORT_NAME = "report.jsonl"

ErrorExport = Literal["empty_json", "no_file"]

# Błędy, po których kolejne wywołania LLM w tym wsadzie nie mają sensu: reszta
# dokumentów dostaje ten sam kod bez wywołania (zły klucz, wyczerpany limit wsadu).
_BATCH_FATAL_CODES = frozenset({"llm_authorization", "llm_call_limit"})
_FAILURE_STATUSES = frozenset({"partial", "technical_error"})
# Błędy jednej strony, które nie przekreślają pozostałych stron dokumentu.
_PAGE_ERROR_CODES = frozenset({"ocr_unavailable", "ocr_error", "pixel_limit"})


@dataclass(frozen=True)
class Issue:
    """Wpis raportu: kod maszynowy, opis bez treści dokumentu, opcjonalnie strona."""

    code: str
    message: str
    page: int | None = None


@dataclass(frozen=True)
class DocumentOutcome:
    """Wynik jednego dokumentu wraz z tym, co trafia do raportu."""

    payload: dict[str, object]
    document_class: DocumentClass | None
    issues: tuple[Issue, ...] = ()
    flags: tuple[str, ...] = ()
    pages: int = 0
    unprocessed: tuple[int, ...] = ()


@dataclass(frozen=True)
class EngineLimits:
    """Limity zasobów dokumentu; przekroczenie to jawny błąd albo flaga."""

    max_file_bytes: int = 100 * 1024 * 1024
    max_pages: int = DEFAULT_MAX_PAGES
    # Render do OCR: dłuższy bok ok. 2000 px wystarcza i nie szkodzi (E02, E03).
    ocr_max_side: int = 2000
    # Twardy limit tekstu wysyłanego do modelu; nadmiar jest ucinany z flagą.
    max_text_chars: int = 150_000


class DocumentEngine(Protocol):
    """Najmniejszy interfejs silnika: PDF → (wynik, klasa dokumentu)."""

    def process(self, pdf: Path) -> tuple[dict[str, object], DocumentClass | None]: ...


class StubEngine:
    """Atrapa silnika dla testów pętli wsadu: zawsze pusty wynik bez klasyfikacji."""

    def process(self, pdf: Path) -> tuple[dict[str, object], DocumentClass | None]:
        return {}, None


class Engine:
    """Prawdziwa ekstrakcja: czytnik PDF, diagnoza stron, opcjonalny OCR, jedno wywołanie LLM.

    Bez dostawcy OCR strona wymagająca OCR trafia do raportu (`ocr_unavailable`)
    i na listę `unprocessed`, a wynik powstaje z pozostałych stron. Warstwy tekstu
    takiej strony nie przekazujemy modelowi: bywa błędna (Z06, S5).
    """

    def __init__(
        self, llm: JsonLlm, ocr: PageOcr | None = None, limits: EngineLimits | None = None
    ) -> None:
        self._llm = llm
        self._ocr = ocr
        self._limits = limits or EngineLimits()

    def process(self, pdf: Path) -> tuple[dict[str, object], DocumentClass | None]:
        outcome = self.process_document(pdf)
        return outcome.payload, outcome.document_class

    def process_document(self, pdf: Path) -> DocumentOutcome:
        """Przetwarza jeden PDF; błąd całego dokumentu to `ProcessingError`."""
        data = self._read(pdf)
        pages, issues = self._read_pages(data)
        unprocessed = tuple(sorted({issue.page for issue in issues if issue.page is not None}))
        if not any(page.text.strip() for page in pages):
            # Brak tekstu to nie jest rozpoznanie dokumentu obcego: jawny błąd techniczny.
            if issues:
                raise ProcessingError(issues[0].code, issues[0].message, page=issues[0].page)
            raise ProcessingError("empty_document", "dokument nie zawiera tekstu")
        text = document_text(pages)
        flags: list[str] = []
        if len(text) > self._limits.max_text_chars:
            text = text[: self._limits.max_text_chars]
            flags.append("text_truncated")
        extraction = extract(text, self._llm)
        return DocumentOutcome(
            payload=extraction.payload,
            document_class=extraction.document_class,
            issues=tuple(issues),
            flags=(*flags, *extraction.flags),
            pages=len(pages),
            unprocessed=unprocessed,
        )

    def _read(self, pdf: Path) -> bytes:
        try:
            if pdf.stat().st_size > self._limits.max_file_bytes:
                raise ProcessingError(
                    "file_too_large", f"plik przekracza limit {self._limits.max_file_bytes} bajtów"
                )
            return pdf.read_bytes()
        except OSError as error:
            raise ProcessingError(
                "read_failed", f"nie odczytano pliku ({type(error).__name__})"
            ) from None

    def _read_pages(self, data: bytes) -> tuple[list[PageText], list[Issue]]:
        pages: list[PageText] = []
        issues: list[Issue] = []
        with PdfDocument(data, max_pages=self._limits.max_pages) as document:
            for index in range(document.page_count):
                reading = document.read_page(index)
                if not diagnose_page(reading).requires_ocr:
                    pages.append(PageText(reading.number, reading.text))
                    continue
                try:
                    text = self._ocr_text(document, index)
                except ProcessingError as error:
                    if error.code not in _PAGE_ERROR_CODES:
                        raise
                    issues.append(Issue(error.code, error.message, reading.number))
                    text = ""
                pages.append(PageText(reading.number, text))
        return pages, issues

    def _ocr_text(self, document: PdfDocument, index: int) -> str:
        if self._ocr is None:
            raise ProcessingError(
                "ocr_unavailable", "strona wymaga OCR, a dostawca OCR nie jest skonfigurowany"
            )
        image = document.render_page(index, self._limits.ocr_max_side)
        return "\n".join(line.text for line in self._ocr.recognize(image))


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    """Zapisuje JSON przez plik tymczasowy, `fsync` i `os.replace`.

    Dlaczego: przerwany zapis nie może zostawić częściowego pliku wyniku, który
    wyglądałby jak poprawny. Plik tymczasowy leży w tym samym katalogu, bo
    `os.replace` jest atomowe tylko w obrębie jednego systemu plików.
    """
    _write_text_atomic(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        with contextlib.suppress(OSError):
            tmp_path.unlink(missing_ok=True)


def find_pdfs(input_dir: Path) -> list[Path]:
    """PDF-y z katalogu i podkatalogów; rozszerzenie bez rozróżniania wielkości liter.

    `rglob("*.pdf")` na Linuksie pomija `.PDF`, a plik bez wyniku to zero punktów.
    """
    return sorted(
        path for path in input_dir.rglob("*") if path.suffix.lower() == ".pdf" and path.is_file()
    )


def _outcome(engine: DocumentEngine, pdf: Path) -> DocumentOutcome:
    if isinstance(engine, Engine):
        return engine.process_document(pdf)
    payload, document_class = engine.process(pdf)
    return DocumentOutcome(payload=payload, document_class=document_class)


def _as_processing_error(error: Exception) -> ProcessingError:
    if isinstance(error, ProcessingError):
        return error
    if isinstance(error, OSError):
        return ProcessingError("write_failed", f"błąd zapisu ({type(error).__name__})")
    # Tylko nazwa klasy: tekst wyjątku mógłby zawierać treść dokumentu.
    return ProcessingError("internal_error", f"nieoczekiwany błąd ({type(error).__name__})")


def _status(outcome: DocumentOutcome) -> str:
    """Stan dokumentu w raporcie; `partial` i `technical_error` dają niezerowy kod wsadu."""
    if outcome.issues:
        return "partial"
    if outcome.document_class == "obcy":
        return "foreign"
    if outcome.document_class is None:
        return "ambiguous" if "class_ambiguous" in outcome.flags else "unclassified"
    return "ok"


def _issue_record(issue: Issue) -> dict[str, object]:
    return {"code": issue.code, "message": issue.message, "page": issue.page}


class _Batch:
    """Stan jednego wsadu: raport, liczniki i zapamiętany błąd przerywający LLM."""

    def __init__(
        self, input_dir: Path, output_dir: Path, engine: DocumentEngine, error_export: ErrorExport
    ) -> None:
        self._input_dir = input_dir
        self._output_dir = output_dir
        self._engine = engine
        self._error_export = error_export
        self._fatal: ProcessingError | None = None
        self._targets: set[Path] = set()
        self._records: list[dict[str, object]] = []
        self.failures = 0

    def run(self, pdf: Path) -> None:
        relative = pdf.relative_to(self._input_dir)
        target = self._output_dir / relative.parent / result_name_for(pdf.name)
        record: dict[str, object] = {"input": relative.as_posix(), "output": None}
        try:
            if target in self._targets:
                raise ProcessingError(
                    "write_failed", "inny plik wejściowy ma tę samą nazwę wyniku; pominięto"
                )
            self._targets.add(target)
            record.update(self._process(pdf, target))
        except Exception as error:
            record.update(self._fail(_as_processing_error(error), relative, target))
        if record["status"] in _FAILURE_STATUSES:
            self.failures += 1
        self._records.append(record)
        self._write_report()

    def _process(self, pdf: Path, target: Path) -> dict[str, object]:
        if self._fatal is not None:
            raise ProcessingError(
                self._fatal.code, f"pominięto po błędzie wsadu: {self._fatal.message}"
            )
        outcome = _outcome(self._engine, pdf)
        payload = {} if outcome.document_class in (None, "obcy") else outcome.payload
        write_json_atomic(target, payload)
        return {
            "output": target.relative_to(self._output_dir).as_posix(),
            "status": _status(outcome),
            "document_class": outcome.document_class,
            "pages": outcome.pages,
            "unprocessed": list(outcome.unprocessed),
            "errors": [_issue_record(issue) for issue in outcome.issues],
            "flags": list(outcome.flags),
        }

    def _fail(self, error: ProcessingError, relative: Path, target: Path) -> dict[str, object]:
        if error.code in _BATCH_FATAL_CODES and self._fatal is None:
            self._fatal = error
        errors = [Issue(error.code, error.message, error.page)]
        output: str | None = None
        if self._error_export == "empty_json" and error.code != "write_failed":
            try:
                write_json_atomic(target, {})
                output = target.relative_to(self._output_dir).as_posix()
            except OSError as failure:
                errors.append(Issue("write_failed", f"błąd zapisu ({type(failure).__name__})"))
        for issue in errors:
            print(f"błąd: {relative.as_posix()}: {issue.code}: {issue.message}", file=sys.stderr)
        return {
            "output": output,
            "status": "technical_error",
            "document_class": None,
            "pages": 0,
            "unprocessed": [],
            "errors": [_issue_record(issue) for issue in errors],
            "flags": [],
        }

    def _write_report(self) -> None:
        """Raport po każdym dokumencie: przerwany wsad zostawia stan do tej chwili."""
        lines = [json.dumps(record, ensure_ascii=False) for record in self._records]
        try:
            _write_text_atomic(self._output_dir / REPORT_NAME, "\n".join(lines) + "\n")
        except OSError as error:
            print(f"błąd: nie zapisano raportu ({type(error).__name__})", file=sys.stderr)


def run_process(
    input_dir: Path,
    output_dir: Path,
    engine: DocumentEngine,
    *,
    error_export: ErrorExport = "empty_json",
) -> int:
    """Przetwarza wszystkie PDF-y z `input_dir` i zwraca kod wyjścia procesu.

    Dlaczego błąd jednego pliku nie przerywa pętli: jeden uszkodzony dokument
    nie powinien blokować wyników pozostałych spraw. Błąd trafia do raportu
    i na stderr, a dokument dostaje `{}` zamiast zmyślenia (ADR-006).
    """
    if not input_dir.is_dir():
        print(f"błąd: katalog wejściowy nie istnieje: {input_dir}", file=sys.stderr)
        return EXIT_USAGE
    batch = _Batch(input_dir, output_dir, engine, error_export)
    for pdf in find_pdfs(input_dir):
        batch.run(pdf)
    if batch.failures:
        print(
            f"błąd: dokumenty z błędami: {batch.failures} (szczegóły: {output_dir / REPORT_NAME})",
            file=sys.stderr,
        )
        return EXIT_DOCUMENT_ERRORS
    return EXIT_OK
