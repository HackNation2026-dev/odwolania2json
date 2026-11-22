"""Testy portów: atrapy spełniają protokoły używane przez silnik."""

from __future__ import annotations

from collections.abc import Sequence

from odwolania2json.extract.ports import OcrLine, OcrWord, PageOcr
from odwolania2json.llm.client import LlmClient, LlmSettings
from PIL import Image


class _FakeOcr:
    def recognize(self, image: Image.Image) -> Sequence[OcrLine]:
        word = OcrWord("SKAN", (1.0, 2.0, 30.0, 12.0), 0.9)
        return [OcrLine("SKAN", word.bbox, (word,))]


def test_fake_provider_satisfies_page_ocr_protocol() -> None:
    provider = _FakeOcr()

    assert isinstance(provider, PageOcr)
    line = provider.recognize(Image.new("RGB", (40, 20), "white"))[0]
    assert (line.text, line.words[0].confidence) == ("SKAN", 0.9)


def test_object_without_recognize_is_not_a_provider() -> None:
    assert not isinstance(object(), PageOcr)


def test_ocr_line_defaults_to_no_words() -> None:
    assert OcrLine("x", (0.0, 0.0, 1.0, 1.0)).words == ()
    assert OcrWord("x", (0.0, 0.0, 1.0, 1.0)).confidence is None


def test_llm_client_exposes_the_json_port_method() -> None:
    settings = LlmSettings(
        protocol="anthropic",
        base_url="https://api.example.test/v1/messages",
        model="m",
        api_key="k",
        allowed_hosts=("api.example.test",),
    )

    assert callable(LlmClient(settings).complete_json)
