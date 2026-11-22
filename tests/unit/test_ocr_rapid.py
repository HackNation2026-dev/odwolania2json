"""Adapter OCR: atrapa silnika bez wag; prawdziwy silnik tylko w teście wolnym."""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pytest
from odwolania2json.errors import ProcessingError
from odwolania2json.ocr import (
    OcrLine,
    OcrProvider,
    OcrResult,
    OcrWord,
    RapidOcr,
    UnavailableOcr,
)
from PIL import Image, ImageDraw, ImageFont

MARKER = (255, 0, 0)


@dataclass
class FakeOutput:
    boxes: list[list[list[float]]] | None
    txts: list[str] | None
    scores: list[float] | None
    word_results: list[list[tuple[str, float, list[list[float]]]]] | None = None


def _box(x0: float, y0: float, x1: float, y1: float) -> list[list[float]]:
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


class FakeEngine:
    """Zapisuje wywołania i zwraca z góry ustalony wynik."""

    def __init__(self, output: FakeOutput | Exception) -> None:
        self.output = output
        self.calls: list[dict[str, object]] = []

    def __call__(self, image: object, **kwargs: object) -> FakeOutput:
        self.calls.append({"shape": np.asarray(image).shape, **kwargs})
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


def _factory(
    engine: FakeEngine | None = None, params: list[dict[str, object]] | None = None
) -> Callable[[dict[str, object]], FakeEngine]:
    def build(config: dict[str, object]) -> FakeEngine:
        if params is not None:
            params.append(config)
        return engine if engine is not None else FakeEngine(FakeOutput(None, None, None))

    return build


def _simple_output() -> FakeOutput:
    return FakeOutput(
        boxes=[_box(10, 20, 110, 40), _box(10, 60, 90, 80)],
        txts=["Ala ma", "kota"],
        scores=[0.9, 0.8],
        word_results=[
            [("Ala", 0.95, _box(10, 20, 40, 40)), ("ma", 0.85, _box(50, 20, 110, 40))],
            [("kota", 0.8, _box(10, 60, 90, 80))],
        ],
    )


class MarkerEngine:
    """Atrapa „czyta” poprawnie tylko obraz, w którym czerwony znacznik jest w lewym górnym rogu.

    Obraz boczny (znacznik w lewym dolnym albo prawym górnym rogu) daje pola pionowe.
    Pole zwrócone przez atrapę otacza znacznik, więc po obrocie wstecz musi trafić w miejsce
    znacznika na obrazie wejściowym.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(
        self,
        image: object,
        *,
        use_det: bool,
        use_cls: bool,
        use_rec: bool,
        return_word_box: bool = False,
    ) -> FakeOutput:
        array = np.asarray(image)
        self.calls.append({"use_det": use_det, "use_cls": use_cls, "use_rec": use_rec})
        mask = (array[..., 0] > 200) & (array[..., 1] < 50) & (array[..., 2] < 50)
        ys, xs = np.nonzero(mask)
        x0, x1, y0, y1 = float(xs.min()), float(xs.max() + 1), float(ys.min()), float(ys.max() + 1)
        height, width = array.shape[:2]
        left, top = x0 < width / 2, y0 < height / 2
        sideways = left != top
        box = _box(x0, y0, x1, y1)
        if not use_rec:
            tall = _box(0, 0, 20, 100) if sideways else _box(0, 0, 100, 20)
            return FakeOutput([tall, tall], None, None)
        upright = left and top
        score = 0.95 if upright else 0.2
        return FakeOutput(
            [box],
            ["Tekst odwołania"],
            [score],
            [[("Tekst", score, box)]],
        )


def _marked_image() -> Image.Image:
    image = Image.new("RGB", (400, 300), "white")
    ImageDraw.Draw(image).rectangle((20, 10, 59, 29), fill=MARKER)
    return image


def test_unavailable_ocr_raises_ocr_unavailable() -> None:
    provider: OcrProvider = UnavailableOcr()
    with pytest.raises(ProcessingError) as error:
        provider.recognize(Image.new("RGB", (10, 10)))
    assert error.value.code == "ocr_unavailable"
    assert provider.name == "none"


def test_rapid_ocr_provider_name() -> None:
    assert RapidOcr(engine_factory=_factory()).name == "rapidocr"


def test_default_parameters_pass_threads_and_max_side_in_pixels() -> None:
    params: list[dict[str, object]] = []
    ocr = RapidOcr(engine_factory=_factory(FakeEngine(_simple_output()), params))
    ocr.recognize(Image.new("RGB", (100, 100), "white"))
    assert params == [
        {
            "EngineConfig.onnxruntime.intra_op_num_threads": 4,
            "EngineConfig.onnxruntime.inter_op_num_threads": 1,
            "Global.max_side_len": 2000,
            "Global.log_level": "warning",
        }
    ]


def test_threads_and_max_side_are_configurable() -> None:
    params: list[dict[str, object]] = []
    ocr = RapidOcr(threads=2, max_side=1500, engine_factory=_factory(None, params))
    ocr.recognize(Image.new("RGB", (50, 50), "white"))
    assert params[0]["EngineConfig.onnxruntime.intra_op_num_threads"] == 2
    assert params[0]["Global.max_side_len"] == 1500


@pytest.mark.parametrize(("threads", "max_side"), [(0, 2000), (-1, 2000), (4, 0), (4, 63)])
def test_invalid_configuration_is_rejected(threads: int, max_side: int) -> None:
    with pytest.raises(ValueError, match=r"threads|max_side"):
        RapidOcr(threads=threads, max_side=max_side, engine_factory=_factory())


def test_engine_is_created_lazily_and_once() -> None:
    params: list[dict[str, object]] = []
    ocr = RapidOcr(engine_factory=_factory(FakeEngine(_simple_output()), params))
    assert params == []
    ocr.recognize(Image.new("RGB", (50, 50), "white"))
    ocr.recognize(Image.new("RGB", (50, 50), "white"))
    assert len(params) == 1


def test_engine_start_failure_is_ocr_unavailable_without_details() -> None:
    def broken(_: dict[str, object]) -> FakeEngine:
        raise ModuleNotFoundError("No module named 'rapidocr' /secret/path")

    with pytest.raises(ProcessingError) as error:
        RapidOcr(engine_factory=broken).recognize(Image.new("RGB", (10, 10)))
    assert error.value.code == "ocr_unavailable"
    assert "ModuleNotFoundError" in error.value.message
    assert "secret" not in error.value.message


def test_missing_rapidocr_package_is_ocr_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(__import__("sys").modules, "rapidocr", None)
    with pytest.raises(ProcessingError) as error:
        RapidOcr().recognize(Image.new("RGB", (10, 10)))
    assert error.value.code == "ocr_unavailable"


def test_engine_failure_is_ocr_error_without_document_content() -> None:
    engine = FakeEngine(RuntimeError("treść dokumentu 12345678903"))
    with pytest.raises(ProcessingError) as error:
        RapidOcr(engine_factory=_factory(engine)).recognize(Image.new("RGB", (10, 10)))
    assert error.value.code == "ocr_error"
    assert "RuntimeError" in error.value.message
    assert "12345678903" not in error.value.message


def test_recognize_returns_lines_with_words_in_pixels() -> None:
    engine = FakeEngine(_simple_output())
    result = RapidOcr(engine_factory=_factory(engine)).recognize(Image.new("RGB", (200, 100)))
    assert result.rotation == 0
    assert (result.width_px, result.height_px) == (200, 100)
    assert result.text == "Ala ma\nkota"
    first, second = result.lines
    assert first == OcrLine(
        text="Ala ma",
        confidence=0.9,
        bbox=(10.0, 20.0, 110.0, 40.0),
        words=(
            OcrWord("Ala", 0.95, (10.0, 20.0, 40.0, 40.0)),
            OcrWord("ma", 0.85, (50.0, 20.0, 110.0, 40.0)),
        ),
    )
    assert second.words == (OcrWord("kota", 0.8, (10.0, 60.0, 90.0, 80.0)),)
    assert [word.text for word in result.words] == ["Ala", "ma", "kota"]


def test_recognition_requests_word_boxes_with_detection_classification_recognition() -> None:
    engine = FakeEngine(_simple_output())
    RapidOcr(engine_factory=_factory(engine)).recognize(Image.new("RGB", (200, 100)))
    final = engine.calls[-1]
    assert final["return_word_box"] is True
    assert (final["use_det"], final["use_cls"], final["use_rec"]) == (True, True, True)
    assert final["shape"] == (100, 200, 3)


def test_grayscale_and_rgba_images_are_converted_to_rgb() -> None:
    engine = FakeEngine(_simple_output())
    ocr = RapidOcr(engine_factory=_factory(engine))
    ocr.recognize(Image.new("L", (30, 20)))
    ocr.recognize(Image.new("RGBA", (30, 20)))
    assert {call["shape"] for call in engine.calls} == {(20, 30, 3)}


def test_missing_word_boxes_give_lines_without_words() -> None:
    output = FakeOutput([_box(1, 2, 30, 12)], ["Ala"], [0.7], None)
    result = RapidOcr(engine_factory=_factory(FakeEngine(output))).recognize(
        Image.new("RGB", (40, 20))
    )
    assert result.text == "Ala"
    assert result.lines[0].words == ()
    assert result.words == ()


def test_word_results_shorter_than_lines_leave_trailing_lines_without_words() -> None:
    output = _simple_output()
    assert output.word_results is not None
    output.word_results = output.word_results[:1]
    result = RapidOcr(engine_factory=_factory(FakeEngine(output))).recognize(
        Image.new("RGB", (200, 100))
    )
    assert len(result.lines[0].words) == 2
    assert result.lines[1].words == ()


def test_empty_engine_output_gives_empty_result() -> None:
    result = RapidOcr(engine_factory=_factory()).recognize(Image.new("RGB", (40, 20)))
    assert result.lines == ()
    assert result.text == ""
    assert result.rotation == 0


def test_blank_lines_and_words_are_dropped() -> None:
    output = FakeOutput(
        [_box(1, 1, 20, 10), _box(1, 20, 20, 30)],
        ["Ala", "   "],
        [0.9, 0.9],
        [[("Ala", 0.9, _box(1, 1, 20, 10)), (" ", 0.9, _box(21, 1, 25, 10))], []],
    )
    result = RapidOcr(engine_factory=_factory(FakeEngine(output))).recognize(
        Image.new("RGB", (40, 40))
    )
    assert [line.text for line in result.lines] == ["Ala"]
    assert [word.text for word in result.lines[0].words] == ["Ala"]


def test_polygon_boxes_become_enclosing_rectangles() -> None:
    skew = [[10.0, 22.0], [100.0, 18.0], [102.0, 40.0], [12.0, 44.0]]
    output = FakeOutput([skew], ["Ala"], [0.9], None)
    result = RapidOcr(engine_factory=_factory(FakeEngine(output))).recognize(
        Image.new("RGB", (120, 60))
    )
    assert result.lines[0].bbox == (10.0, 18.0, 102.0, 44.0)


def test_to_page_points_scales_pixels_to_points() -> None:
    engine = FakeEngine(_simple_output())
    result = RapidOcr(engine_factory=_factory(engine)).recognize(Image.new("RGB", (200, 100)))
    page = result.to_page_points(100.0, 50.0)
    assert page.lines[0].bbox == (5.0, 10.0, 55.0, 20.0)
    assert page.lines[0].words[1].bbox == (25.0, 10.0, 55.0, 20.0)
    assert page.lines[1].bbox == (5.0, 30.0, 45.0, 40.0)
    assert (page.width_px, page.height_px) == (200, 100)
    assert page.rotation == result.rotation
    assert page.lines[0].words[0].text == "Ala"
    assert page.lines[0].words[0].confidence == 0.95


def test_to_page_points_uses_separate_horizontal_and_vertical_scale() -> None:
    output = FakeOutput(
        [_box(100, 100, 200, 150)], ["x"], [1.0], [[("x", 1.0, _box(100, 100, 200, 150))]]
    )
    result = RapidOcr(engine_factory=_factory(FakeEngine(output))).recognize(
        Image.new("RGB", (400, 200))
    )
    page = result.to_page_points(200.0, 400.0)
    assert page.lines[0].words[0].bbox == (50.0, 200.0, 100.0, 300.0)


def test_to_page_points_clips_to_page_and_drops_words_outside() -> None:
    output = FakeOutput(
        [_box(-10, -5, 210, 105)],
        ["Ala ma"],
        [0.9],
        [[("Ala", 0.9, _box(-10, -5, 40, 20)), ("ma", 0.9, _box(300, 10, 350, 20))]],
    )
    result = RapidOcr(engine_factory=_factory(FakeEngine(output))).recognize(
        Image.new("RGB", (200, 100))
    )
    page = result.to_page_points(100.0, 50.0)
    assert page.lines[0].bbox == (0.0, 0.0, 100.0, 50.0)
    assert [word.text for word in page.lines[0].words] == ["Ala"]
    assert page.lines[0].words[0].bbox == (0.0, 0.0, 20.0, 10.0)


def test_to_page_points_drops_line_with_degenerate_box() -> None:
    output = FakeOutput([_box(300, 10, 350, 20)], ["poza"], [0.9], None)
    result = RapidOcr(engine_factory=_factory(FakeEngine(output))).recognize(
        Image.new("RGB", (200, 100))
    )
    assert result.to_page_points(100.0, 50.0).lines == ()


@pytest.mark.parametrize("size", [(0.0, 10.0), (10.0, 0.0), (-1.0, 10.0)])
def test_to_page_points_rejects_non_positive_page_size(size: tuple[float, float]) -> None:
    result = OcrResult(lines=(), rotation=0, width_px=10, height_px=10)
    with pytest.raises(ValueError, match="rozmiar"):
        result.to_page_points(*size)


@pytest.mark.parametrize("stored_rotation", [0, 90, 180, 270])
def test_detected_rotation_restores_orientation_and_maps_boxes_back(stored_rotation: int) -> None:
    upright = _marked_image()
    stored = upright.rotate(stored_rotation, expand=True)
    engine = MarkerEngine()
    result = RapidOcr(engine_factory=_factory(engine)).recognize(stored)  # type: ignore[arg-type]
    assert result.rotation == (360 - stored_rotation) % 360
    assert result.text == "Tekst odwołania"
    assert (result.width_px, result.height_px) == stored.size
    # Pole zwrócone w obrazie obróconym wraca na miejsce znacznika w obrazie wejściowym.
    mask = np.asarray(stored)
    ys, xs = np.nonzero((mask[..., 0] > 200) & (mask[..., 1] < 50))
    expected = (float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1))
    assert result.lines[0].bbox == expected
    assert result.lines[0].words[0].bbox == expected


def test_upright_image_needs_no_rotation_and_two_recognitions() -> None:
    engine = MarkerEngine()
    result = RapidOcr(engine_factory=_factory(engine)).recognize(_marked_image())  # type: ignore[arg-type]
    assert result.rotation == 0
    # sonda detekcji, dwa kandydaci obrotu i odczyt końcowy
    assert [(c["use_det"], c["use_cls"], c["use_rec"]) for c in engine.calls] == [
        (True, False, False),
        (True, True, True),
        (True, True, True),
        (True, True, True),
    ]


def test_rotation_probe_is_downscaled_to_1000_pixels() -> None:
    engine = FakeEngine(FakeOutput(None, None, None))
    RapidOcr(engine_factory=_factory(engine)).recognize(Image.new("RGB", (3000, 2000), "white"))
    assert engine.calls[0]["shape"] == (667, 1000, 3)
    assert engine.calls[-1]["shape"] == (2000, 3000, 3)


class SequenceEngine:
    """Zwraca kolejne z góry ustalone wyniki: sonda, kandydaci obrotu, odczyt końcowy."""

    def __init__(self, outputs: list[FakeOutput]) -> None:
        self.outputs = outputs

    def __call__(self, image: object, **kwargs: object) -> FakeOutput:
        return self.outputs.pop(0)


def _scored(score: float) -> FakeOutput:
    return FakeOutput([_box(0, 0, 50, 10)], ["ABCDEFGHIJ"], [score], None)


def _probe() -> FakeOutput:
    return FakeOutput([_box(0, 0, 100, 20)], None, None)


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        (0.90, 0.92, 0),  # różnica 2%: szum klasyfikatora linii, zostaje 0
        (0.90, 0.98, 0),  # 8,9%: nadal poniżej marginesu 10%
        (0.90, 1.00, 180),  # 11%: wyraźnie lepsza orientacja
        (0.90, 0.90, 0),  # remis zostaje przy pierwszym kandydacie
        (0.90, 0.10, 0),
    ],
)
def test_second_orientation_must_clearly_beat_the_first(
    first: float, second: float, expected: int
) -> None:
    engine = SequenceEngine([_probe(), _scored(first), _scored(second), _scored(0.5)])
    ocr = RapidOcr(engine_factory=_factory(engine))  # type: ignore[arg-type]
    assert ocr.detect_rotation(Image.new("RGB", (100, 100))) == expected


def test_no_boxes_in_probe_means_no_rotation() -> None:
    engine = FakeEngine(FakeOutput([], None, None))
    result = RapidOcr(engine_factory=_factory(engine)).recognize(Image.new("RGB", (50, 50)))
    assert result.rotation == 0
    assert len(engine.calls) == 2


def test_rotation_detection_is_not_deskew_or_binarization() -> None:
    """E03: obraz do odczytu to oryginał albo jego obrót o 90/180/270, bez zmiany pikseli."""
    image = _marked_image()
    engine = FakeEngine(_simple_output())
    RapidOcr(engine_factory=_factory(engine)).recognize(image)
    assert engine.calls[-1]["shape"] == (300, 400, 3)


def _generated_page() -> Image.Image:
    image = Image.new("RGB", (900, 260), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=64)
    draw.text((30, 40), "ODWOLANIE 2026", fill="black", font=font)
    draw.text((30, 140), "KIO 1234", fill="black", font=font)
    return image


requires_rapidocr = pytest.mark.skipif(
    importlib.util.find_spec("rapidocr") is None, reason="brak pakietu rapidocr (wolny test)"
)


@requires_rapidocr
@pytest.mark.slow_ocr
def test_real_rapidocr_reads_generated_image() -> None:
    result = RapidOcr().recognize(_generated_page())
    assert "2026" in result.text.replace(" ", "")
    assert result.rotation == 0
    page = result.to_page_points(450.0, 130.0)
    assert page.words
    for word in page.words:
        x0, y0, x1, y1 = word.bbox
        assert 0 <= x0 < x1 <= 450
        assert 0 <= y0 < y1 <= 130


@requires_rapidocr
@pytest.mark.slow_ocr
@pytest.mark.parametrize("stored_rotation", [90, 180, 270])
def test_real_rapidocr_boxes_stay_in_input_image_coordinates(stored_rotation: int) -> None:
    stored = _generated_page().rotate(stored_rotation, expand=True)
    result = RapidOcr().recognize(stored)
    assert "2026" in result.text.replace(" ", "")
    word = next(word for word in result.words if "2026" in word.text)
    x0, y0, x1, y1 = (round(value) for value in word.bbox)
    assert 0 <= x0 < x1 <= stored.width
    assert 0 <= y0 < y1 <= stored.height
    # W obrysie słowa, w obrazie wejściowym, leży atrament (ciemne piksele).
    crop = np.asarray(stored.convert("L").crop((x0, y0, x1, y1)))
    assert (crop < 128).mean() > 0.05
