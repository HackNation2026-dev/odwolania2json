"""Test integracyjny `process` na dokumentach organizatora z fałszywym LLM.

Fałszywy model odpowiada polami z referencji organizatora, więc wynik `process`
musi odtworzyć referencję co do kluczy, kolejności i typów (czytnik PDF, pipeline,
serializer i zapis działają razem; sieci nie ma).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from odwolania2json import cli
from odwolania2json.cli import main
from odwolania2json.config import Settings
from odwolania2json.engine import REPORT_NAME
from odwolania2json.llm.client import LlmClient
from odwolania2json.loader import MATERIALS_DIR
from support.llm import FakeLlmServer, answer, fields_from_reference

CASE = MATERIALS_DIR / "dane" / "przyklad_01"
FOREIGN = MATERIALS_DIR / "dane" / "negatywne" / "KIO_KIO 2617-21.pdf"
# (plik wejściowy, referencja, etykieta klasy modelu, fraza rozpoznawcza w tekście PDF)
DOCUMENTS = (
    ("odwolanie.pdf", "odwolanie.json", "appeal", "Prezes Krajowej Izby Odwoławczej"),
    ("pelnomocnictwo.pdf", "pelnomocnictwo.json", "power_of_attorney", "PEŁNOMOCNICTWO"),
    ("potwierdzenie_przelewu.pdf", "przelew.json", "bank_transfer", "POLECENIE PRZELEWU"),
)


def _reference(name: str) -> dict[str, object]:
    loaded = json.loads((CASE / name).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _respond(text: str) -> dict[str, object] | str:
    if not text.startswith("[[strona 1]]"):
        return "OK"  # wywołanie próbne self-check
    for _pdf, reference, label, phrase in DOCUMENTS:
        if phrase in text.split("[[strona 2]]")[0][:400]:
            return answer(label, *fields_from_reference(_reference(reference)))
    return answer("foreign")


def _shape(value: object) -> object:
    """Struktura bez wartości: klucze w kolejności i nazwy typów liści."""
    if isinstance(value, dict):
        return [(key, _shape(item)) for key, item in value.items()]
    if isinstance(value, list):
        return [_shape(item) for item in value]
    return type(value).__name__


@pytest.fixture
def processed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, FakeLlmServer, int]:
    input_dir = tmp_path / "input"
    (input_dir / "przyklad_01").mkdir(parents=True)
    for pdf, _reference_name, _label, _phrase in DOCUMENTS:
        shutil.copy(CASE / pdf, input_dir / "przyklad_01" / pdf)
    (input_dir / "negatywne").mkdir()
    shutil.copy(FOREIGN, input_dir / "negatywne" / "WYROK.PDF")
    server = FakeLlmServer(_respond)

    def build(settings: Settings) -> LlmClient:
        return server.client()

    monkeypatch.setattr(cli, "build_llm_client", build)
    exit_code = main(["process", str(input_dir), str(tmp_path / "output")])
    return tmp_path / "output", server, exit_code


def test_process_reproduces_reference_json_for_three_classes(
    processed: tuple[Path, FakeLlmServer, int],
) -> None:
    output_dir, _server, exit_code = processed

    assert exit_code == 0
    for pdf, reference_name, _label, _phrase in DOCUMENTS:
        result_path = output_dir / "przyklad_01" / f"{Path(pdf).stem}.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        reference = _reference(reference_name)
        assert _shape(result) == _shape(reference), pdf
        assert result == reference, pdf
        assert json.dumps(result, ensure_ascii=False) == json.dumps(reference, ensure_ascii=False)


def test_process_gives_empty_json_for_foreign_document_with_uppercase_extension(
    processed: tuple[Path, FakeLlmServer, int],
) -> None:
    output_dir, _server, _exit_code = processed

    assert json.loads((output_dir / "negatywne" / "WYROK.json").read_text(encoding="utf-8")) == {}


def test_process_makes_one_llm_call_per_document_plus_self_check(
    processed: tuple[Path, FakeLlmServer, int],
) -> None:
    _output_dir, server, _exit_code = processed

    assert len(server.requests) == 1 + 4
    appeal_text = next(text for text in server.user_texts if "Prezes Krajowej Izby" in text)
    assert appeal_text.startswith("[[strona 1]]\nPrezes Krajowej Izby Odwoławczej\n")
    assert "[[strona 2]]" in appeal_text


def test_process_report_has_classes_and_no_document_content(
    processed: tuple[Path, FakeLlmServer, int],
) -> None:
    output_dir, _server, _exit_code = processed

    report_text = (output_dir / REPORT_NAME).read_text(encoding="utf-8")
    records = [json.loads(line) for line in report_text.splitlines()]
    assert {
        record["input"]: (record["status"], record["document_class"]) for record in records
    } == {
        "negatywne/WYROK.PDF": ("foreign", "obcy"),
        "przyklad_01/odwolanie.pdf": ("ok", "odwolanie"),
        "przyklad_01/pelnomocnictwo.pdf": ("ok", "pelnomocnictwo"),
        "przyklad_01/potwierdzenie_przelewu.pdf": ("ok", "przelew"),
    }
    # Raport nie niesie treści dokumentów: nazwy stron, numery i nazwiska zostają w wyniku.
    for fragment in ("Belmoria", "9999405188", "Kaczmarek"):
        assert fragment not in report_text
