"""Testy polecenia `process`: wejście PDF-ów → wyniki JSON na atrapie silnika."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from odwolania2json.cli import main
from odwolania2json.engine import StubEngine, run_process


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n")


class _BrokenEngine(StubEngine):
    """Atrapa, która zawodzi dla jednego pliku, jak uszkodzony PDF."""

    def __init__(self, broken_name: str) -> None:
        self._broken_name = broken_name

    def process(self, pdf: Path) -> tuple[dict[str, object], None]:
        if pdf.name == self._broken_name:
            raise ValueError("uszkodzony PDF")
        return super().process(pdf)


def test_tree_is_recreated(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "a" / "b.pdf")
    _touch(input_dir / "a" / "c.pdf")
    _touch(input_dir / "d" / "e.pdf")

    assert run_process(input_dir, output_dir, StubEngine()) == 0

    assert (output_dir / "a" / "b.json").is_file()
    assert (output_dir / "a" / "c.json").is_file()
    assert (output_dir / "d" / "e.json").is_file()


def test_foreign_document_gets_empty_json_named_after_input(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "n.pdf")

    assert run_process(input_dir, output_dir, StubEngine()) == 0

    assert json.loads((output_dir / "n.json").read_text(encoding="utf-8")) == {}


def test_result_name_follows_input_for_transfer(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "potwierdzenie_przelewu.pdf")

    assert run_process(input_dir, output_dir, StubEngine()) == 0

    assert (output_dir / "potwierdzenie_przelewu.json").is_file()


def test_document_error_does_not_stop_others(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "bad" / "broken.pdf")
    _touch(input_dir / "good" / "ok.pdf")

    exit_code = run_process(input_dir, output_dir, _BrokenEngine("broken.pdf"))

    assert exit_code == 1
    assert (output_dir / "good" / "ok.json").is_file()
    assert not (output_dir / "bad" / "broken.json").exists()
    assert "broken.pdf" in capsys.readouterr().err


def test_exit_code_zero_when_all_ok(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    _touch(input_dir / "x.pdf")

    assert main(["process", str(input_dir), str(tmp_path / "out")]) == 0


def test_exit_code_two_on_missing_input_dir(tmp_path: Path) -> None:
    assert main(["process", str(tmp_path / "brak"), str(tmp_path / "out")]) == 2


def test_atomic_write_leaves_no_partial_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "x.pdf")

    real_replace = os.replace
    calls = {"count": 0}

    def failing_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("zapis przerwany")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)

    assert run_process(input_dir, output_dir, StubEngine()) == 1

    assert not (output_dir / "x.json").exists()
    assert list(output_dir.rglob("*")) == []
    assert "zapis przerwany" in capsys.readouterr().err
