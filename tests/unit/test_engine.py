"""Testy silnika: strony, OCR opcjonalny, błędy dokumentu, limity (fałszywy LLM)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from odwolania2json.engine import Engine, EngineLimits, Issue
from odwolania2json.errors import ProcessingError
from odwolania2json.extract.ports import OcrLine
from PIL import Image
from support.llm import FakeLlmServer, answer, field
from support.pdfs import Run, build_pdf, encrypted_pdf, image_pdf, text_pdf

TRANSFER = answer("bank_transfer", field("/przelew_bankowy/tytul", "WPIS"))


class FakeOcr:
    """Dostawca OCR zwracający stały tekst; zapamiętuje rozmiary obrazów."""

    def __init__(self, lines: Sequence[str] = ("SKAN LINIA 1", "SKAN LINIA 2")) -> None:
        self._lines = lines
        self.sizes: list[tuple[int, int]] = []

    def recognize(self, image: Image.Image) -> Sequence[OcrLine]:
        self.sizes.append(image.size)
        return [OcrLine(text, (0.0, 0.0, 10.0, 10.0)) for text in self._lines]


class BrokenOcr:
    def __init__(self, code: str) -> None:
        self._code = code

    def recognize(self, image: Image.Image) -> Sequence[OcrLine]:
        raise ProcessingError(self._code, "awaria OCR")


def _write(tmp_path: Path, data: bytes, name: str = "doc.pdf") -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _mixed_pdf() -> bytes:
    """Strona 1: tekst; strona 2: warstwa niewidoczna (jak błędna warstwa OCR skanu)."""
    return build_pdf(
        [
            [Run("Widoczny tekst strony", y=150, size=12)],
            [Run("UKRYTA WARSTWA 999", y=150, size=12, render_mode=3)],
        ]
    )


def test_text_document_is_extracted_with_one_call(tmp_path: Path) -> None:
    server = FakeLlmServer([TRANSFER])

    outcome = Engine(server.client()).process_document(
        _write(tmp_path, text_pdf(["Pierwsza", "Druga"]))
    )

    assert outcome.document_class == "przelew"
    assert outcome.payload["przelew_bankowy"]["tytul"] == "WPIS"  # type: ignore[index]
    assert (outcome.pages, outcome.issues, outcome.unprocessed, outcome.flags) == (2, (), (), ())
    assert server.user_texts == ["[[strona 1]]\nPierwsza\n[[strona 2]]\nDruga"]


def test_process_returns_payload_and_class_like_stub(tmp_path: Path) -> None:
    server = FakeLlmServer([answer("foreign")])

    assert Engine(server.client()).process(_write(tmp_path, text_pdf(["Wyrok"]))) == ({}, "obcy")


def test_page_requiring_ocr_without_provider_is_reported_and_skipped(tmp_path: Path) -> None:
    server = FakeLlmServer([TRANSFER])

    outcome = Engine(server.client()).process_document(_write(tmp_path, _mixed_pdf()))

    assert outcome.document_class == "przelew"
    assert outcome.unprocessed == (2,)
    assert outcome.issues == (
        Issue("ocr_unavailable", "strona wymaga OCR, a dostawca OCR nie jest skonfigurowany", 2),
    )
    # Niewidoczna warstwa tekstu nie trafia do modelu (S5), zostaje tylko znacznik strony.
    assert server.user_texts == ["[[strona 1]]\nWidoczny tekst strony\n[[strona 2]]\n"]


def test_scan_only_document_without_ocr_is_technical_error_without_llm_call(
    tmp_path: Path,
) -> None:
    server = FakeLlmServer([])

    with pytest.raises(ProcessingError) as caught:
        Engine(server.client()).process_document(_write(tmp_path, image_pdf(pages=2)))

    assert (caught.value.code, caught.value.page) == ("ocr_unavailable", 1)
    assert server.requests == []


def test_ocr_provider_supplies_text_for_scan_pages(tmp_path: Path) -> None:
    server = FakeLlmServer([TRANSFER])
    ocr = FakeOcr()

    outcome = Engine(server.client(), ocr).process_document(_write(tmp_path, _mixed_pdf()))

    assert (outcome.issues, outcome.unprocessed) == ((), ())
    assert server.user_texts == [
        "[[strona 1]]\nWidoczny tekst strony\n[[strona 2]]\nSKAN LINIA 1\nSKAN LINIA 2"
    ]
    assert len(ocr.sizes) == 1


def test_ocr_render_is_bounded_by_configured_side(tmp_path: Path) -> None:
    server = FakeLlmServer([TRANSFER])
    ocr = FakeOcr()
    limits = EngineLimits(ocr_max_side=500)

    Engine(server.client(), ocr, limits).process_document(_write(tmp_path, image_pdf()))

    assert max(ocr.sizes[0]) == 500


@pytest.mark.parametrize("code", ["ocr_error", "ocr_unavailable"])
def test_failing_ocr_marks_page_and_keeps_other_pages(tmp_path: Path, code: str) -> None:
    server = FakeLlmServer([TRANSFER])

    outcome = Engine(server.client(), BrokenOcr(code)).process_document(
        _write(tmp_path, _mixed_pdf())
    )

    assert outcome.issues == (Issue(code, "awaria OCR", 2),)
    assert outcome.unprocessed == (2,)
    assert outcome.document_class == "przelew"


def test_unexpected_ocr_failure_code_fails_the_document(tmp_path: Path) -> None:
    server = FakeLlmServer([])

    with pytest.raises(ProcessingError) as caught:
        Engine(server.client(), BrokenOcr("internal_error")).process_document(
            _write(tmp_path, _mixed_pdf())
        )

    assert caught.value.code == "internal_error"


def test_ocr_returning_nothing_for_only_page_is_empty_document(tmp_path: Path) -> None:
    server = FakeLlmServer([])

    with pytest.raises(ProcessingError) as caught:
        Engine(server.client(), FakeOcr(lines=())).process_document(_write(tmp_path, image_pdf()))

    assert caught.value.code == "empty_document"
    assert server.requests == []


def test_blank_document_is_empty_document(tmp_path: Path) -> None:
    server = FakeLlmServer([])

    with pytest.raises(ProcessingError) as caught:
        Engine(server.client()).process_document(_write(tmp_path, build_pdf([[], []])))

    assert caught.value.code == "empty_document"


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"zwykly tekst", "not_a_pdf"),
        (b"%PDF-1.4\nuszkodzony", "pdf_corrupted"),
        (encrypted_pdf(), "pdf_encrypted"),
    ],
)
def test_unreadable_pdf_fails_with_code_and_no_llm_call(
    tmp_path: Path, data: bytes, code: str
) -> None:
    server = FakeLlmServer([])

    with pytest.raises(ProcessingError) as caught:
        Engine(server.client()).process_document(_write(tmp_path, data))

    assert caught.value.code == code
    assert server.requests == []


def test_page_limit_fails_document(tmp_path: Path) -> None:
    server = FakeLlmServer([])
    engine = Engine(server.client(), limits=EngineLimits(max_pages=1))

    with pytest.raises(ProcessingError) as caught:
        engine.process_document(_write(tmp_path, text_pdf(["1", "2"])))

    assert caught.value.code == "page_limit"


def test_file_size_limit_fails_document(tmp_path: Path) -> None:
    server = FakeLlmServer([])
    engine = Engine(server.client(), limits=EngineLimits(max_file_bytes=10))

    with pytest.raises(ProcessingError) as caught:
        engine.process_document(_write(tmp_path, text_pdf(["1"])))

    assert caught.value.code == "file_too_large"
    assert server.requests == []


def test_file_at_size_limit_is_processed(tmp_path: Path) -> None:
    data = text_pdf(["1"])
    server = FakeLlmServer([TRANSFER])
    engine = Engine(server.client(), limits=EngineLimits(max_file_bytes=len(data)))

    assert engine.process_document(_write(tmp_path, data)).document_class == "przelew"


def test_missing_file_is_read_failure(tmp_path: Path) -> None:
    server = FakeLlmServer([])

    with pytest.raises(ProcessingError) as caught:
        Engine(server.client()).process_document(tmp_path / "brak.pdf")

    assert caught.value.code == "read_failed"
    assert "FileNotFoundError" in caught.value.message


def test_long_text_is_truncated_with_flag(tmp_path: Path) -> None:
    server = FakeLlmServer([TRANSFER])
    engine = Engine(server.client(), limits=EngineLimits(max_text_chars=20))

    outcome = engine.process_document(_write(tmp_path, text_pdf(["Bardzo dlugi tekst strony"])))

    assert outcome.flags == ("text_truncated",)
    assert server.user_texts == ["[[strona 1]]\nBardzo "]


def test_text_at_limit_is_not_flagged(tmp_path: Path) -> None:
    server = FakeLlmServer([TRANSFER])
    engine = Engine(server.client(), limits=EngineLimits(max_text_chars=len("[[strona 1]]\nAbc")))

    assert engine.process_document(_write(tmp_path, text_pdf(["Abc"]))).flags == ()


def test_llm_failure_after_retry_is_raised_not_invented(tmp_path: Path) -> None:
    server = FakeLlmServer(["bzdura", "druga bzdura"])

    with pytest.raises(ProcessingError) as caught:
        Engine(server.client()).process_document(_write(tmp_path, text_pdf(["Tekst"])))

    assert caught.value.code == "llm_invalid_response"
    assert len(server.requests) == 2


def test_ambiguous_flags_are_kept_in_outcome(tmp_path: Path) -> None:
    server = FakeLlmServer([answer("ambiguous"), answer("ambiguous")])

    outcome = Engine(server.client()).process_document(_write(tmp_path, text_pdf(["Tekst"])))

    assert (outcome.document_class, outcome.payload) == (None, {})
    assert outcome.flags == ("class_ambiguous",)
