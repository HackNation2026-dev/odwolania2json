"""Testy czytnika PDF: tekst, linie, obrót, diagnoza strony, błędy i limity."""

from __future__ import annotations

import pytest
from odwolania2json.errors import ProcessingError
from odwolania2json.pdf.reader import (
    PageReading,
    PdfDocument,
    Word,
    diagnose_page,
    display_point,
    group_lines,
)
from support.pdfs import Run, build_pdf, encrypted_pdf, image_pdf, text_pdf


def _read(data: bytes, index: int = 0) -> PageReading:
    with PdfDocument(data) as document:
        return document.read_page(index)


def _page(**changes: object) -> PageReading:
    base: dict[str, object] = {
        "number": 1,
        "width_pt": 300.0,
        "height_pt": 200.0,
        "rotation": 0,
        "words": (Word("a", (1.0, 1.0, 2.0, 2.0)),),
        "lines": (),
        "image_coverage": 0.0,
        "invisible_share": 0.0,
        "object_count": 1,
    }
    base.update(changes)
    return PageReading(**base)  # type: ignore[arg-type]  # słownik testowy pól dataclass


def test_reads_text_and_page_size() -> None:
    page = _read(text_pdf(["Hello World"]))

    assert page.text == "Hello World"
    assert (page.number, page.width_pt, page.height_pt, page.rotation) == (1, 300.0, 200.0, 0)
    assert [word.text for word in page.words] == ["Hello", "World"]
    assert page.lines[0].id == "p1l1"


def test_word_bbox_uses_top_left_origin() -> None:
    page = _read(text_pdf(["Hello World"]))

    x0, y0, x1, y1 = page.words[0].bbox
    # Linia bazowa na y=100 od dołu strony 200 pt: po odwróceniu osi słowo leży nad y=100.
    assert 50 <= x0 < x1 < 110
    assert 80 < y0 < y1 <= 100.5


def test_lines_keep_reading_order_top_to_bottom() -> None:
    data = build_pdf([[Run("First line", y=160), Run("Second line", y=120), Run("Third", y=80)]])

    page = _read(data)

    assert [line.text for line in page.lines] == ["First line", "Second line", "Third"]
    assert [line.id for line in page.lines] == ["p1l1", "p1l2", "p1l3"]
    assert page.lines[0].bbox[1] < page.lines[1].bbox[1] < page.lines[2].bbox[1]


def test_page_numbers_and_ids_follow_pages() -> None:
    with PdfDocument(text_pdf(["One", "Two"])) as document:
        assert document.page_count == 2
        second = document.read_page(1)

    assert second.number == 2
    assert second.lines[0].id == "p2l1"
    assert second.text == "Two"


@pytest.mark.parametrize(
    ("rotate", "expected_size", "expected_origin"),
    [
        (90, (200.0, 300.0), (100.0, 50.0)),
        (180, (300.0, 200.0), (250.0, 100.0)),
        (270, (200.0, 300.0), (100.0, 250.0)),
    ],
)
def test_rotation_maps_bbox_to_displayed_page(
    rotate: int, expected_size: tuple[float, float], expected_origin: tuple[float, float]
) -> None:
    page = _read(text_pdf(["Hello"], rotate=rotate))

    assert page.rotation == rotate
    assert (page.width_pt, page.height_pt) == expected_size
    x0, y0, x1, y1 = page.words[0].bbox
    assert 0 <= x0 < x1 <= page.width_pt
    assert 0 <= y0 < y1 <= page.height_pt
    # Początek linii bazowej (50, 100) musi leżeć na krawędzi obrysu po obrocie.
    origin_x, origin_y = expected_origin
    assert x0 - 2 <= origin_x <= x1 + 2
    assert y0 - 2 <= origin_y <= y1 + 2
    assert page.text == "Hello"


@pytest.mark.parametrize(
    ("rotation", "expected"),
    [(0, (10.0, 180.0)), (90, (20.0, 10.0)), (180, (290.0, 20.0)), (270, (180.0, 290.0))],
)
def test_display_point_for_each_rotation(rotation: int, expected: tuple[float, float]) -> None:
    assert display_point(rotation, (0.0, 0.0, 300.0, 200.0), 10.0, 20.0) == expected


def test_display_point_respects_mediabox_offset() -> None:
    assert display_point(0, (100.0, 50.0, 400.0, 250.0), 110.0, 70.0) == (10.0, 180.0)


def test_group_lines_splits_on_vertical_position_and_backward_jump() -> None:
    words = [
        Word("A", (10.0, 10.0, 20.0, 20.0)),
        Word("B", (25.0, 11.0, 35.0, 21.0)),
        Word("C", (10.0, 30.0, 20.0, 40.0)),
        Word("D", (5.0, 31.0, 8.0, 39.0)),
    ]

    lines = group_lines(words, 3)

    assert [line.text for line in lines] == ["A B", "C", "D"]
    assert lines[0].id == "p3l1"
    assert lines[0].bbox == (10.0, 10.0, 35.0, 21.0)


def test_empty_page_is_blank() -> None:
    page = _read(build_pdf([[]]))

    diagnosis = diagnose_page(page)

    assert page.words == ()
    assert page.text == ""
    assert (diagnosis.kind, diagnosis.requires_ocr, diagnosis.word_count) == ("blank", False, 0)


def test_text_page_is_diagnosed_as_text() -> None:
    diagnosis = diagnose_page(_read(text_pdf(["Hello World"])))

    assert (diagnosis.kind, diagnosis.requires_ocr) == ("text", False)
    assert diagnosis.word_count == 2
    assert diagnosis.image_coverage == 0.0
    assert diagnosis.reasons == ()


def test_image_only_page_requires_ocr() -> None:
    page = _read(image_pdf())

    diagnosis = diagnose_page(page)

    assert page.words == ()
    assert page.image_coverage == pytest.approx(1.0)
    assert (diagnosis.kind, diagnosis.requires_ocr) == ("scan", True)
    assert "image_dominant" in diagnosis.reasons


@pytest.mark.parametrize(
    "hidden",
    [
        Run("Hidden words here now", y=60, render_mode=3),
        Run("Hidden words here now", y=60, color=(1, 1, 1)),
        Run("Hidden words here now", y=60, size=1),
        Run("Hidden words here now", x=400, y=60),
    ],
    ids=["render_mode_3", "white", "one_point", "outside_mediabox"],
)
def test_mostly_invisible_text_layer_is_not_trusted(hidden: Run) -> None:
    page = _read(build_pdf([[Run("Seen", y=150), hidden]]))

    diagnosis = diagnose_page(page)

    assert page.invisible_share > 0.5
    assert diagnosis.requires_ocr is True
    assert "invisible_text" in diagnosis.reasons


@pytest.mark.parametrize(
    "hidden",
    [
        Run("Hidden", y=60, render_mode=3),
        Run("Hidden", y=60, size=1),
        Run("Hidden", x=400, y=60),
    ],
    ids=["render_mode_3", "one_point", "outside_mediabox"],
)
def test_unseeable_text_never_reaches_page_text(hidden: Run) -> None:
    page = _read(build_pdf([[Run("Visible words on this page are many", y=150, size=10), hidden]]))

    assert "Hidden" not in page.text
    assert page.text == "Visible words on this page are many"
    assert 0.0 < page.invisible_share < 0.5
    assert diagnose_page(page).kind == "text"


def test_unit_font_scaled_by_text_matrix_is_visible() -> None:
    # Regresja z materiałów organizatora: `/F1 1 Tf` i macierz skalująca to zwykły tekst.
    page = _read(build_pdf([[Run("Scaled text", y=150, size=12, scaled_unit_font=True)]]))

    assert page.text == "Scaled text"
    assert page.invisible_share == 0.0
    assert diagnose_page(page).kind == "text"


def test_white_text_stays_in_text_but_counts_as_invisible() -> None:
    # Biały tekst bywa widoczny na ciemnym tle (nagłówki tabel), więc zostaje w treści.
    page = _read(
        build_pdf([[Run("Visible words on this page", y=150), Run("Bialy", y=60, color=(1, 1, 1))]])
    )

    assert "Bialy" in page.text
    assert 0.0 < page.invisible_share < 0.5


def test_diagnosis_thresholds() -> None:
    assert diagnose_page(_page(image_coverage=0.5)).reasons == ("image_dominant",)
    assert diagnose_page(_page(image_coverage=0.49)).kind == "text"
    assert diagnose_page(_page(invisible_share=0.5)).reasons == ("invisible_text",)
    assert diagnose_page(_page(invisible_share=0.49)).kind == "text"
    no_layer = diagnose_page(_page(words=(), object_count=2))
    assert (no_layer.kind, no_layer.reasons) == ("scan", ("no_text_layer",))
    assert diagnose_page(_page(words=(), object_count=0)).kind == "blank"


def test_not_a_pdf_is_rejected() -> None:
    with pytest.raises(ProcessingError) as caught:
        PdfDocument(b"to nie jest PDF")

    assert caught.value.code == "not_a_pdf"


def test_corrupted_pdf_is_rejected() -> None:
    with pytest.raises(ProcessingError) as caught:
        PdfDocument(b"%PDF-1.4\n1 0 obj << uszkodzone")

    assert caught.value.code == "pdf_corrupted"


def test_truncated_pdf_is_rejected() -> None:
    data = text_pdf(["Hello"])

    with pytest.raises(ProcessingError) as caught:
        PdfDocument(data[: len(data) // 3])

    assert caught.value.code == "pdf_corrupted"


def test_encrypted_pdf_is_rejected_with_code() -> None:
    with pytest.raises(ProcessingError) as caught:
        PdfDocument(encrypted_pdf())

    assert caught.value.code == "pdf_encrypted"
    assert "tajne-haslo" not in str(caught.value)


def test_pdf_without_pages_is_empty_document() -> None:
    with pytest.raises(ProcessingError) as caught:
        PdfDocument(build_pdf([]))

    # pdfium odrzuca drzewo stron bez stron już przy otwarciu.
    assert caught.value.code == "pdf_corrupted"


def test_page_limit_is_enforced() -> None:
    data = text_pdf(["1", "2", "3"])

    with pytest.raises(ProcessingError) as caught:
        PdfDocument(data, max_pages=2)

    assert caught.value.code == "page_limit"
    with PdfDocument(data, max_pages=3) as document:
        assert document.page_count == 3


def test_render_respects_longest_side_and_rotation() -> None:
    with PdfDocument(text_pdf(["Hello"], rotate=90)) as document:
        image = document.render_page(0, max_side=150)

    assert image.mode == "RGB"
    assert image.size == (100, 150)


def test_render_does_not_upscale_beyond_300_dpi() -> None:
    with PdfDocument(text_pdf(["Hello"], size=(72, 36))) as document:
        image = document.render_page(0, max_side=4000)

    assert image.size == (300, 150)


def test_render_pixel_limit_is_enforced() -> None:
    with PdfDocument(text_pdf(["Hello"])) as document, pytest.raises(ProcessingError) as caught:
        document.render_page(0, max_side=1000, max_pixels=1000)

    assert caught.value.code == "pixel_limit"
    assert caught.value.page == 1


def test_reading_missing_page_is_reported_as_corruption() -> None:
    with PdfDocument(text_pdf(["Hello"])) as document, pytest.raises(ProcessingError) as caught:
        document.read_page(5)

    assert caught.value.code == "pdf_corrupted"
    assert caught.value.page == 6
