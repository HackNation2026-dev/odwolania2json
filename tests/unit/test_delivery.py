"""Testy dostarczenia: zależności, skrypty startowe i czysta instalacja (Z03)."""

from __future__ import annotations

import http.client
import importlib.util
import json
import os
import shutil
import socket
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEV_ONLY = ("pytest", "datamodel-code-generator", "openapi-spec-validator", "mypy", "ruff")


def _load_verify_install():
    path = ROOT / "scripts/verify_install.py"
    spec = importlib.util.spec_from_file_location("verify_install", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_install"] = module
    spec.loader.exec_module(module)
    return module


def _requirement_lines(path: Path) -> list[str]:
    lines = [line.split("#")[0].strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line]


def _expand(path: Path) -> list[str]:
    result: list[str] = []
    for line in _requirement_lines(path):
        if line.startswith("-r "):
            result.extend(_expand(path.parent / line[3:].strip()))
        else:
            result.append(line)
    return result


def test_runtime_requirements_are_pinned_and_without_dev_tools():
    lines = _expand(ROOT / "requirements.txt")
    external = [line for line in lines if not line.startswith(("./", "-e"))]
    assert external
    for line in external:
        assert "==" in line, line
        assert line.split("==")[0].split("[")[0].lower() not in DEV_ONLY, line


def test_runtime_requirements_install_local_packages_without_editable_mode():
    lines = _requirement_lines(ROOT / "requirements.txt")
    assert "./packages/contracts" in lines
    assert "./apps/backend" in lines
    assert not any(line.startswith("-e") for line in lines)


def test_ocr_is_part_of_the_main_requirements():
    names = {line.split("==")[0].lower() for line in _expand(ROOT / "requirements.txt")}
    assert {"rapidocr", "onnxruntime"} <= names
    assert "onnxruntime-gpu" not in names
    assert not (ROOT / "apps/backend/requirements-ocr.txt").exists()


def test_dev_requirements_hold_the_tools_for_development():
    names = {line.split("==")[0].lower() for line in _expand(ROOT / "requirements-dev.txt")}
    assert {"pytest", "datamodel-code-generator", "openapi-spec-validator", "ruff"} <= names


def test_package_requires_python_313():
    config = tomllib.loads((ROOT / "apps/backend/pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["requires-python"] == ">=3.13"


def test_input_and_output_directories_are_kept_but_contents_ignored():
    assert (ROOT / "input/.gitkeep").is_file()
    assert (ROOT / "output/.gitkeep").is_file()
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for name in ("input", "output"):
        assert f"/{name}/*" in ignore
        assert f"!/{name}/.gitkeep" in ignore


def test_run_script_creates_venv_installs_and_runs_process():
    text = (ROOT / "run.sh").read_text(encoding="utf-8")
    for fragment in (
        "python3.13",
        "-m venv .venv",
        "-m pip install",
        "-r requirements.txt",
        "mkdir -p input output",
        "-m odwolania2json process input output",
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "LLM_MODEL",
    ):
        assert fragment in text, fragment


def test_start_bat_mirrors_run_script():
    text = (ROOT / "start.bat").read_text(encoding="utf-8")
    for fragment in (
        "-m venv .venv",
        "-m pip install",
        "-r requirements.txt",
        "input",
        "output",
        "-m odwolania2json process input output",
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "exit /b",
    ):
        assert fragment in text, fragment


def test_sample_pdfs_are_valid_and_distinct(tmp_path: Path):
    module = _load_verify_install()
    paths = module.write_sample_pdfs(tmp_path, count=3)
    assert len(paths) == 3
    contents = {path.read_bytes() for path in paths}
    assert len(contents) == 3
    for path in paths:
        data = path.read_bytes()
        assert data.startswith(b"%PDF-1.4")
        assert data.rstrip().endswith(b"%%EOF")
        startxref = int(data.rsplit(b"startxref", 1)[1].split()[0])
        assert data[startxref : startxref + 4] == b"xref"


def test_mock_llm_answers_chat_completions():
    module = _load_verify_install()
    with module.MockLlm() as mock:
        connection = http.client.HTTPConnection("127.0.0.1", mock.port, timeout=5)
        connection.request(
            "POST",
            "/chat/completions",
            body=json.dumps({"model": "x", "messages": []}),
            headers={"Content-Type": "application/json"},
        )
        body = json.loads(connection.getresponse().read())
        connection.close()
    assert body["choices"][0]["message"]["role"] == "assistant"
    json.loads(body["choices"][0]["message"]["content"])
    assert mock.requests == 1


def test_mock_llm_is_closed_after_context():
    module = _load_verify_install()
    with module.MockLlm() as mock:
        port = mock.port
    with (
        pytest.raises(ConnectionRefusedError),
        socket.create_connection(("127.0.0.1", port), timeout=1),
    ):
        pass


def test_check_outputs_reports_missing_and_invalid_files(tmp_path: Path):
    module = _load_verify_install()
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    (tmp_path / "b.json").write_text("nie json", encoding="utf-8")
    problems = module.check_outputs(tmp_path, ["a", "b", "c"])
    assert any("b.json" in problem for problem in problems)
    assert any("c.json" in problem for problem in problems)
    assert not any("a.json" in problem for problem in problems)


def test_python_version_gate_rejects_old_interpreter():
    module = _load_verify_install()
    assert module.python_is_supported((3, 13)) is True
    assert module.python_is_supported((3, 12)) is False
    assert module.python_is_supported((3, 12, 9)) is False


def _pypi_reachable() -> bool:
    try:
        with urllib.request.urlopen("https://pypi.org/simple/", timeout=5):
            return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


@pytest.mark.slow_install
def test_clean_install_end_to_end(monkeypatch):
    """Pełna czysta instalacja (minuty, ~1 GB): tylko z O2J_VERIFY_INSTALL=1 i Pythonem 3.13."""
    module = _load_verify_install()
    if os.environ.get("O2J_VERIFY_INSTALL") != "1":
        pytest.skip("SKIP: czysta instalacja trwa minuty; ustaw O2J_VERIFY_INSTALL=1")
    if not _pypi_reachable():
        pytest.skip("SKIP: brak sieci do PyPI, czystej instalacji nie sprawdzono")
    current = sys.executable if sys.version_info[:2] == (3, 13) else None
    python = shutil.which("python3.13") or current
    if python is None:
        pytest.skip("SKIP: brak interpretera Python 3.13 (koła onnxruntime są dla 3.13)")
    assert module.main(["--python", python]) == 0
