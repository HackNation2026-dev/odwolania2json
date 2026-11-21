"""Testy odczytu PDF: słowa, bbox po /Rotate (sprawdzane renderem), diagnoza, błędy techniczne."""

import numpy as np
import pytest

from common import HarnessError
from pdfs import image_pdf, text_pdf
from reading import (NoOcr, PdfiumReader, display_mapping, diagnose_document, diagnose_page, make_ocr,
                     ocr_page_to_reading, read_document)

R = PdfiumReader()


def read(data: bytes, **kw):
    kw.setdefault("ocr", NoOcr())
    return read_document(data, reader=R, ocr_policy=kw.pop("ocr_policy", "if_needed"), ocr_dpi=100,
                         max_pages=kw.pop("max_pages", 50), **kw)


def test_words_and_lines_text_pdf():
    reading, diag, m = read(text_pdf(["Hello World"]))
    pg = reading["pages"][0]
    assert [w["text"] for w in pg["words"]] == ["Hello", "World"]
    assert pg["lines"][0]["text"] == "Hello World" and pg["lines"][0]["words"] == ["p1w1", "p1w2"]
    assert pg["source"] == "pdf" and all(w["confidence"] is None for w in pg["words"])
    assert all(w["line_id"] == "p1l1" for w in pg["words"])
    assert diag["text_source"] == "pdf" and not diag["requires_ocr"]
    assert len(reading["document_sha256"]) == 64


@pytest.mark.parametrize("rotate", [0, 90, 180, 270])
def test_bbox_matches_rendered_ink_after_rotate(rotate):
    """Piksele tuszu wyrenderowanej strony muszą leżeć w sumie bbox słów (układ po /Rotate)."""
    data = text_pdf(["HELLO WORLD"], rotate=rotate)
    reading, _, _ = read(data)
    pg = reading["pages"][0]
    assert (pg["width_pt"], pg["height_pt"]) == ((300, 200) if rotate in (0, 180) else (200, 300))
    doc = R.open(data)
    img = np.asarray(R.render_page(doc, 0, 72).convert("L"))
    ys, xs = np.where(img < 128)
    ink = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    x0 = min(w["bbox"][0] for w in pg["words"]); y0 = min(w["bbox"][1] for w in pg["words"])
    x1 = max(w["bbox"][2] for w in pg["words"]); y1 = max(w["bbox"][3] for w in pg["words"])
    # tolerancja 3 pt: bbox znaków obejmuje zapas pod/nad glifem
    assert abs(ink[0] - x0) <= 3 and abs(ink[2] - x1) <= 3, (ink, (x0, x1))
    assert ink[1] >= y0 - 3 and ink[3] <= y1 + 3
    assert y1 - y0 < 30 or rotate in (90, 270)  # w orientacji pionowej tekst biegnie wzdłuż y


@pytest.mark.parametrize("rotate", [0, 90, 180, 270])
def test_to_pdf_matrix_maps_display_corners_to_user_space(rotate):
    fwd, (wd, hd), inv = display_mapping(rotate, (0, 0, 300, 200))
    for ux, uy in ((0, 0), (300, 0), (0, 200), (300, 200), (50, 100)):
        dx, dy = fwd(ux, uy)
        bx = inv[0] * dx + inv[1] * dy + inv[2]
        by = inv[3] * dx + inv[4] * dy + inv[5]
        assert (round(bx, 6), round(by, 6)) == (ux, uy)
        assert 0 <= dx <= wd and 0 <= dy <= hd


def test_scan_is_diagnosed_and_ocr_unavailable_is_explicit():
    reading, diag, m = read(image_pdf())
    assert reading["pages"][0]["words"] == [] and reading["pages"][0]["source"] == "none"
    assert diag["requires_ocr"] and "scan" in diag["codes"] and "ocr_unavailable" in diag["codes"]
    assert diag["pages"][0]["text_source"] == "none"
    assert m["unprocessed_pages"] == [1] and m["ocr_errors"][0]["code"] == "ocr_unavailable"


def test_blank_text_page_not_requiring_ocr():
    d = diagnose_page({"number": 1, "width_pt": 100, "height_pt": 100, "words": [], "images": []}, ocr_available=False)
    assert d["text_source"] == "none" and not d["requires_ocr"] and d["codes"] == []


def test_mixed_document_flag():
    a = diagnose_page({"number": 1, "width_pt": 100, "height_pt": 100, "words": [{"source": "pdf"}] * 9, "images": []}, ocr_available=False)
    b = diagnose_page({"number": 2, "width_pt": 100, "height_pt": 100, "words": [], "images": [{"bbox": [0, 0, 100, 100]}]}, ocr_available=False)
    doc = diagnose_document([a, b])
    assert "mixed_document" in doc["codes"] and doc["text_source"] == "mixed"


def test_corrupted_and_non_pdf():
    for blob in (b"to nie jest pdf", b"%PDF-1.4\nuciety", b""):
        with pytest.raises(HarnessError) as e:
            read(blob)
        assert e.value.code == "pdf_corrupted"


def test_page_limit_and_zero_pages():
    with pytest.raises(HarnessError) as e:
        read(text_pdf(["a b c d e"] * 3), max_pages=2)
    assert e.value.code == "page_limit"


def test_deadline_gives_time_limit():
    with pytest.raises(HarnessError) as e:
        read(text_pdf(["a"] * 3), deadline=0.0)
    assert e.value.code == "time_limit"


def test_none_ocr_info_and_factory():
    assert make_ocr("none").info() == {"available": False, "name": "none", "version": None, "parameter_count": None,
                                       "license": None, "location": None, "models": []}
    with pytest.raises(HarnessError) as e:
        make_ocr("tesseract")
    assert e.value.code == "invalid_configuration"
    with pytest.raises(HarnessError) as e:
        make_ocr("none").ocr_image(None, 100)
    assert e.value.code == "ocr_unavailable"


def test_ocr_pixels_to_points_and_drops_degenerate_boxes():
    ocr = {"lines": [{"id": "l1", "text": "Kwota 200", "bbox": [100, 100, 300, 140], "confidence": 0.9}],
           "words": [{"id": "l1w1", "line_id": "l1", "text": "Kwota", "confidence": 0.9, "bbox": [100, 100, 200, 140]},
                     {"id": "l1w2", "line_id": "l1", "text": "200", "confidence": 0.8, "bbox": [210, 100, 300, 140]},
                     {"id": "l1w3", "line_id": "l1", "text": "zero", "confidence": 0.8, "bbox": [5, 5, 5, 9]}]}
    out = ocr_page_to_reading(1, ocr, 144, 595, 842)  # 144 dpi => x0.5
    assert [w["bbox"] for w in out["words"]] == [[50.0, 50.0, 100.0, 70.0], [105.0, 50.0, 150.0, 70.0]]
    assert out["lines"][0]["words"] == [w["id"] for w in out["words"]] and out["text"] == "Kwota 200"
    assert all(w["source"] == "ocr" and 0 <= w["confidence"] <= 1 for w in out["words"])


@pytest.mark.slow
def test_rapidocr_reads_rendered_scan():
    ocr = make_ocr("rapidocr")
    if not ocr.info()["available"]:
        pytest.skip("rapidocr niedostępny")
    reading, diag, m = read_document(image_pdf(text="SKAN TEST 123", dpi=100), reader=R, ocr=ocr, ocr_policy="if_needed",
                                     ocr_dpi=150, max_pages=5)
    pg = reading["pages"][0]
    assert "123" in pg["text"] and pg["source"] == "ocr" and m["ocr_pages"] == 1
    assert all(w["source"] == "ocr" for w in pg["words"]) and "ocr_unavailable" not in diag["codes"]


def test_ocr_numpy_scalars_are_json_serializable():
    """Regresja: rapidocr zwraca numpy.float32; surowy float32 w bbox psuł zapis JSON (internal_error na skanie)."""
    import json

    f = np.float32
    ocr = {"lines": [{"id": "l1", "text": "A", "bbox": [f(10), f(10), f(50), f(30)], "confidence": 0.9}],
           "words": [{"id": "l1w1", "line_id": "l1", "text": "A", "confidence": f(0.9), "bbox": [f(10), f(10), f(50), f(30)]}]}
    out = ocr_page_to_reading(1, ocr, 72, 595, 842)
    assert json.loads(json.dumps(out))["words"][0]["bbox"] == [10.0, 10.0, 50.0, 30.0]
