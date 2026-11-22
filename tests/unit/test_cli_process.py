"""Testy polecenia `process`: pętla wsadu, polityka eksportu (ADR-006), self-check LLM."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from odwolania2json import cli
from odwolania2json.cli import main
from odwolania2json.config import Settings
from odwolania2json.engine import (
    REPORT_NAME,
    Engine,
    StubEngine,
    find_pdfs,
    run_process,
    write_json_atomic,
)
from odwolania2json.llm.chain import LlmChain
from odwolania2json.llm.client import LlmBudget, LlmClient
from support.llm import API_KEY, FALLBACK_KEY, TIMEOUT, FakeLlmServer, answer, field
from support.pdfs import image_pdf, text_pdf

TRANSFER = answer("bank_transfer", field("/przelew_bankowy/tytul", "WPIS"))
PROBE = "OK"


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n")


def _pdf(path: Path, text: str = "Tekst dokumentu") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text_pdf([text]))


def _report(output_dir: Path) -> list[dict[str, object]]:
    lines = (output_dir / REPORT_NAME).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _all_text(*roots: Path) -> str:
    return "".join(
        path.read_text(encoding="utf-8", errors="replace")
        for root in roots
        for path in root.rglob("*")
        if path.is_file() and path.suffix != ".pdf"
    )


class _BrokenEngine(StubEngine):
    """Atrapa, która zawodzi dla jednego pliku nieoczekiwanym wyjątkiem z treścią."""

    def __init__(self, broken_name: str) -> None:
        self._broken_name = broken_name

    def process(self, pdf: Path) -> tuple[dict[str, object], None]:
        if pdf.name == self._broken_name:
            raise ValueError("TRESC-DOKUMENTU 99010112345")
        return super().process(pdf)


FALLBACK_ENV = {
    "LLM_API_KEY": API_KEY,
    "LLM_BASE_URL": "https://api.minimax.io/anthropic/v1/messages",
    "LLM_MODEL": "model-glowny",
    "LLM_ALLOWED_HOSTS": "api.minimax.io,zapas.example.test",
    "LLM_FALLBACK_BASE_URL": "https://zapas.example.test/v1",
    "LLM_FALLBACK_MODEL": "model-zapasowy",
    "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    "LLM_MAX_CALLS": "9",
    "LLM_MAX_TOTAL_TOKENS": "5000",
}


def _use_server(monkeypatch: pytest.MonkeyPatch, server: FakeLlmServer) -> None:
    def build(settings: Settings) -> LlmClient:
        return server.client()

    monkeypatch.setattr(cli, "build_llm_client", build)


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

    assert _load(output_dir / "n.json") == {}


def test_result_name_follows_input_for_transfer(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "potwierdzenie_przelewu.pdf")

    assert run_process(input_dir, output_dir, StubEngine()) == 0

    assert (output_dir / "potwierdzenie_przelewu.json").is_file()


def test_uppercase_pdf_extension_gets_a_result(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "SKAN.PDF")
    _touch(input_dir / "sub" / "Mixed.Pdf")
    (input_dir / "notatka.txt").write_text("to nie PDF", encoding="utf-8")
    (input_dir / "katalog.pdf").mkdir()

    assert [path.name for path in find_pdfs(input_dir)] == ["SKAN.PDF", "Mixed.Pdf"]
    assert run_process(input_dir, output_dir, StubEngine()) == 0

    assert (output_dir / "SKAN.json").is_file()
    assert (output_dir / "sub" / "Mixed.json").is_file()
    assert not (output_dir / "notatka.json").exists()


def test_document_error_writes_empty_json_and_does_not_stop_others(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "bad" / "broken.pdf")
    _touch(input_dir / "good" / "ok.pdf")

    exit_code = run_process(input_dir, output_dir, _BrokenEngine("broken.pdf"))

    assert exit_code == 1
    assert (output_dir / "good" / "ok.json").is_file()
    assert _load(output_dir / "bad" / "broken.json") == {}
    captured = capsys.readouterr().err
    assert "bad/broken.pdf: internal_error" in captured
    assert "dokumenty z błędami: 1" in captured


def test_report_lists_every_input_with_status_and_code(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "bad" / "broken.pdf")
    _touch(input_dir / "good" / "ok.pdf")

    run_process(input_dir, output_dir, _BrokenEngine("broken.pdf"))

    assert _report(output_dir) == [
        {
            "input": "bad/broken.pdf",
            "output": "bad/broken.json",
            "status": "technical_error",
            "document_class": None,
            "pages": 0,
            "unprocessed": [],
            "errors": [
                {
                    "code": "internal_error",
                    "message": "nieoczekiwany błąd (ValueError)",
                    "page": None,
                }
            ],
            "flags": [],
            "llm": None,
        },
        {
            "input": "good/ok.pdf",
            "output": "good/ok.json",
            "status": "unclassified",
            "document_class": None,
            "pages": 0,
            "unprocessed": [],
            "errors": [],
            "flags": [],
            "llm": None,
        },
    ]


def test_unexpected_exception_text_never_reaches_report_or_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "broken.pdf")

    run_process(input_dir, output_dir, _BrokenEngine("broken.pdf"))

    captured = capsys.readouterr()
    assert "99010112345" not in captured.err + captured.out + _all_text(output_dir)


def test_error_overwrites_previous_result_with_empty_json_by_default(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "bad" / "broken.pdf")
    stale = output_dir / "bad" / "broken.json"
    stale.parent.mkdir(parents=True)
    stale.write_text('{"stary": true}\n', encoding="utf-8")

    assert run_process(input_dir, output_dir, _BrokenEngine("broken.pdf")) == 1

    # Stary wynik nie może uchodzić za wynik nowego przebiegu: zastępuje go `{}`.
    assert _load(stale) == {}


def test_no_file_export_leaves_previous_result_untouched(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "bad" / "broken.pdf")
    _touch(input_dir / "good.pdf")
    stale = output_dir / "bad" / "broken.json"
    stale.parent.mkdir(parents=True)
    stale.write_text('{"stary": true}\n', encoding="utf-8")

    exit_code = run_process(
        input_dir, output_dir, _BrokenEngine("broken.pdf"), error_export="no_file"
    )

    assert exit_code == 1
    # Przełącznik `no_file`: brak nowego pliku, ale poprzedniego nie usuwamy.
    assert _load(stale) == {"stary": True}
    assert (output_dir / "good.json").is_file()
    record = _report(output_dir)[0]
    assert (record["input"], record["output"], record["status"]) == (
        "bad/broken.pdf",
        None,
        "technical_error",
    )


def test_failed_write_keeps_previous_result_and_reports_write_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "x.pdf")
    _touch(input_dir / "y.pdf")
    stale = output_dir / "x.json"
    stale.parent.mkdir(parents=True)
    stale.write_text('{"stary": true}\n', encoding="utf-8")
    real_replace = os.replace

    def failing_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        if Path(dst).name == "x.json":
            raise OSError("zapis przerwany")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)

    assert run_process(input_dir, output_dir, StubEngine()) == 1

    assert _load(stale) == {"stary": True}
    assert (output_dir / "y.json").is_file()
    assert [path.name for path in output_dir.iterdir() if path.name.startswith(".")] == []
    first = _report(output_dir)[0]
    assert (first["status"], first["output"]) == ("technical_error", None)
    assert first["errors"] == [
        {"code": "write_failed", "message": "błąd zapisu (OSError)", "page": None}
    ]
    assert "x.pdf: write_failed" in capsys.readouterr().err


def test_failed_empty_json_write_is_reported_next_to_the_primary_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "broken.pdf")
    real_replace = os.replace

    def failing_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        if Path(dst).name == "broken.json":
            raise PermissionError("brak uprawnień")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)

    assert run_process(input_dir, output_dir, _BrokenEngine("broken.pdf")) == 1

    record = _report(output_dir)[0]
    assert record["output"] is None
    assert [error["code"] for error in record["errors"]] == ["internal_error", "write_failed"]  # type: ignore[index, union-attr]
    assert not (output_dir / "broken.json").exists()


def test_unwritable_report_does_not_change_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "x.pdf")
    real_replace = os.replace

    def failing_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        if Path(dst).name == REPORT_NAME:
            raise OSError("dysk pełny")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)

    assert run_process(input_dir, output_dir, StubEngine()) == 0

    assert (output_dir / "x.json").is_file()
    assert "nie zapisano raportu (OSError)" in capsys.readouterr().err


def test_inputs_with_the_same_result_name_do_not_overwrite_each_other(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _touch(input_dir / "a.PDF")
    _touch(input_dir / "a.pdf")
    if len(list(input_dir.iterdir())) < 2:
        pytest.skip("system plików nie rozróżnia wielkości liter")

    assert run_process(input_dir, output_dir, StubEngine()) == 1

    records = _report(output_dir)
    assert [record["status"] for record in records] == ["unclassified", "technical_error"]
    assert records[1]["errors"][0]["code"] == "write_failed"  # type: ignore[index, call-overload]
    assert (output_dir / "a.json").is_file()


def test_result_json_uses_two_space_indent_and_trailing_newline(tmp_path: Path) -> None:
    target = tmp_path / "x.json"
    payload: dict[str, object] = {"klucz": "wartość", "lista": [1, 2]}

    write_json_atomic(target, payload)

    expected = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    assert target.read_text(encoding="utf-8") == expected


def test_cleanup_error_does_not_mask_primary_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "x.json"

    def failing_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        raise OSError("zapis przerwany")

    real_unlink = Path.unlink

    def locked_unlink(self: Path, missing_ok: bool = False) -> None:
        if self.name.startswith("."):
            raise OSError("sprzątanie zablokowane")
        real_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(os, "replace", failing_replace)
    monkeypatch.setattr(Path, "unlink", locked_unlink)

    with pytest.raises(OSError, match="zapis przerwany"):
        write_json_atomic(target, {})


def test_missing_input_dir_is_usage_error(tmp_path: Path) -> None:
    assert run_process(tmp_path / "brak", tmp_path / "out", StubEngine()) == 2
    assert main(["process", str(tmp_path / "brak"), str(tmp_path / "out")]) == 2


def test_real_engine_batch_report_and_exit_codes(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    _pdf(input_dir / "a_przelew.pdf")
    _pdf(input_dir / "b_obcy.pdf")
    (input_dir / "c_skan.pdf").write_bytes(image_pdf())
    (input_dir / "d_zepsuty.pdf").write_bytes(b"%PDF-1.4\nzepsuty")
    _pdf(input_dir / "e_llm.pdf")
    _pdf(input_dir / "f_niejasny.pdf")
    server = FakeLlmServer(
        [TRANSFER, answer("foreign"), "nie JSON", "{}", answer("ambiguous"), answer("ambiguous")]
    )

    exit_code = run_process(input_dir, output_dir, Engine(server.client()))

    assert exit_code == 1
    records = {str(record["input"]): record for record in _report(output_dir)}
    assert [record["status"] for record in records.values()] == [
        "ok",
        "foreign",
        "technical_error",
        "technical_error",
        "technical_error",
        "ambiguous",
    ]
    codes = [
        [error["code"] for error in record["errors"]]  # type: ignore[union-attr, index]
        for record in records.values()
    ]
    assert codes == [[], [], ["ocr_unavailable"], ["pdf_corrupted"], ["llm_invalid_response"], []]
    assert records["a_przelew.pdf"]["document_class"] == "przelew"
    assert records["a_przelew.pdf"]["pages"] == 1
    assert records["f_niejasny.pdf"]["flags"] == ["class_ambiguous"]
    assert _load(output_dir / "a_przelew.json")["przelew_bankowy"]["tytul"] == "WPIS"  # type: ignore[index]
    for name in ("b_obcy", "c_skan", "d_zepsuty", "e_llm", "f_niejasny"):
        assert _load(output_dir / f"{name}.json") == {}


def test_partial_document_is_exported_reported_and_fails_the_batch(tmp_path: Path) -> None:
    from support.pdfs import Run, build_pdf

    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    (input_dir / "mieszany.pdf").write_bytes(
        build_pdf([[Run("Widoczny", size=12)], [Run("UKRYTY", size=12, render_mode=3)]])
    )
    server = FakeLlmServer([TRANSFER])

    assert run_process(input_dir, output_dir, Engine(server.client())) == 1

    record = _report(output_dir)[0]
    assert (record["status"], record["unprocessed"]) == ("partial", [2])
    assert record["errors"][0]["code"] == "ocr_unavailable"  # type: ignore[index, call-overload]
    assert _load(output_dir / "mieszany.json")["przelew_bankowy"]["tytul"] == "WPIS"  # type: ignore[index]


def test_rejected_key_stops_llm_calls_but_every_input_gets_a_file(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    for name in ("a.pdf", "b.pdf", "c.pdf"):
        _pdf(input_dir / name)
    server = FakeLlmServer([401])

    assert run_process(input_dir, output_dir, Engine(server.client())) == 1

    assert len(server.requests) == 1
    records = _report(output_dir)
    assert [record["status"] for record in records] == ["technical_error"] * 3
    assert {record["errors"][0]["code"] for record in records} == {"llm_authorization"}  # type: ignore[index, call-overload]
    assert "pominięto po błędzie wsadu" in records[2]["errors"][0]["message"]  # type: ignore[index, call-overload]
    assert all(_load(output_dir / f"{stem}.json") == {} for stem in "abc")


def test_cli_process_runs_self_check_then_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_dir = tmp_path / "in"
    _pdf(input_dir / "x.pdf")
    server = FakeLlmServer([PROBE, TRANSFER])
    _use_server(monkeypatch, server)

    assert main(["process", str(input_dir), str(tmp_path / "out")]) == 0

    assert len(server.requests) == 2
    assert server.requests[0]["max_tokens"] == 16
    assert _load(tmp_path / "out" / "x.json")["przelew_bankowy"]["tytul"] == "WPIS"  # type: ignore[index]


def test_cli_prints_llm_usage_after_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _pdf(tmp_path / "in" / "x.pdf")
    _use_server(monkeypatch, FakeLlmServer([PROBE, TRANSFER]))

    main(["process", str(tmp_path / "in"), str(tmp_path / "out")])

    assert "LLM: wywołania=2 tokeny_wejścia=20 tokeny_wyjścia=10" in capsys.readouterr().out


def test_cooldown_from_environment_reaches_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = cli.build_llm_client(
        Settings.from_env({**FALLBACK_ENV, "LLM_PROVIDER_COOLDOWN_S": "7"})
    )

    assert chain.cooldown_s == 7.0
    assert cli.build_llm_client(Settings.from_env(FALLBACK_ENV)).cooldown_s == 300.0


def test_cli_process_defaults_to_input_and_output_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("INPUT_DIR", raising=False)
    monkeypatch.delenv("OUTPUT_DIR", raising=False)
    _pdf(tmp_path / "input" / "x.pdf")
    _use_server(monkeypatch, FakeLlmServer([PROBE, answer("foreign")]))

    assert main(["process"]) == 0

    assert _load(tmp_path / "output" / "x.json") == {}


def test_cli_process_reads_directories_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INPUT_DIR", str(tmp_path / "wejscie"))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "wyjscie"))
    _pdf(tmp_path / "wejscie" / "x.pdf")
    _use_server(monkeypatch, FakeLlmServer([PROBE, answer("foreign")]))

    assert main(["process"]) == 0

    assert (tmp_path / "wyjscie" / "x.json").is_file()


def test_cli_without_pdfs_needs_no_llm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "in").mkdir()
    server = FakeLlmServer([])
    _use_server(monkeypatch, server)

    assert main(["process", str(tmp_path / "in"), str(tmp_path / "out")]) == 0

    assert server.requests == []
    assert "brak plików PDF" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("status", "code"),
    [(401, "llm_authorization"), (403, "llm_authorization"), (429, "llm_rate_limit")],
)
def test_self_check_failure_exits_2_without_processing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    status: int,
    code: str,
) -> None:
    input_dir = tmp_path / "in"
    _pdf(input_dir / "x.pdf")
    server = FakeLlmServer([status])
    _use_server(monkeypatch, server)

    assert main(["process", str(input_dir), str(tmp_path / "out")]) == 2

    captured = capsys.readouterr()
    assert f"błąd: {code}" in captured.err
    assert "wskazówka:" in captured.err
    assert "wsad nie został przetworzony" in captured.err
    assert len(server.requests) == 1
    assert not (tmp_path / "out").exists()
    assert API_KEY not in captured.err + captured.out


def test_self_check_retries_network_failure_then_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_dir = tmp_path / "in"
    _pdf(input_dir / "x.pdf")
    server = FakeLlmServer([503, PROBE, answer("foreign")])
    _use_server(monkeypatch, server)
    delays: list[float] = []

    assert main(["process", str(input_dir), str(tmp_path / "out")], sleep=delays.append) == 0

    assert delays == [2.0]
    assert len(server.requests) == 3


def test_self_check_gives_up_after_three_network_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    _pdf(input_dir / "x.pdf")
    server = FakeLlmServer([500, 500, 500])
    _use_server(monkeypatch, server)
    delays: list[float] = []

    assert main(["process", str(input_dir), str(tmp_path / "out")], sleep=delays.append) == 2

    assert delays == [2.0, 4.0]
    assert len(server.requests) == 3
    assert "błąd: llm_unavailable" in capsys.readouterr().err


def test_missing_key_without_terminal_is_explicit_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    _pdf(input_dir / "x.pdf")
    for name in ("LLM_API_KEY", "LLM_API_KEY_FILE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "https://api.minimax.io/anthropic/v1/messages")
    monkeypatch.setenv("LLM_MODEL", "model")

    assert main(["process", str(input_dir), str(tmp_path / "out")]) == 2

    captured = capsys.readouterr().err
    assert "błąd: llm_authorization: brak klucza API LLM" in captured
    assert not (tmp_path / "out").exists()


def test_invalid_configuration_is_reported_before_any_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    _pdf(input_dir / "x.pdf")
    monkeypatch.setenv("LLM_API_KEY", API_KEY)
    monkeypatch.setenv("LLM_BASE_URL", "https://obcy-host.example/v1")
    monkeypatch.setenv("LLM_MODEL", "model")
    monkeypatch.delenv("LLM_ALLOWED_HOSTS", raising=False)

    assert main(["process", str(input_dir), str(tmp_path / "out")]) == 2

    captured = capsys.readouterr()
    assert "błąd: invalid_configuration" in captured.err
    assert "LLM_ALLOWED_HOSTS" in captured.err
    assert API_KEY not in captured.err + captured.out


def test_build_llm_client_uses_environment_settings() -> None:
    settings = Settings.from_env(
        {
            "LLM_API_KEY": API_KEY,
            "LLM_BASE_URL": "https://api.minimax.io/anthropic/v1/messages",
            "LLM_MODEL": "model-testowy",
        }
    )

    chain = cli.build_llm_client(settings)

    assert isinstance(chain, LlmChain)
    assert chain.has_fallback is False
    assert chain.budget.max_calls == 1000


def test_no_file_export_from_environment_is_passed_to_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_dir = tmp_path / "in"
    (input_dir).mkdir()
    (input_dir / "zly.pdf").write_bytes(b"%PDF-1.4\nzepsuty")
    monkeypatch.setenv("ERROR_EXPORT", "no_file")
    _use_server(monkeypatch, FakeLlmServer([PROBE]))

    assert main(["process", str(input_dir), str(tmp_path / "out")]) == 1

    assert not (tmp_path / "out" / "zly.json").exists()
    assert _report(tmp_path / "out")[0]["output"] is None


def test_api_key_canary_never_appears_in_any_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    for name in ("a.pdf", "b.pdf", "c.pdf", "d.pdf"):
        _pdf(input_dir / name)
    # Serwer wkleja klucz do treści błędów; program nie może go nigdzie przepisać.
    server = FakeLlmServer([PROBE, TRANSFER, 500, 500, 500, 500, 400, 403])
    _use_server(monkeypatch, server)

    assert main(["process", str(input_dir), str(output_dir)]) == 1

    captured = capsys.readouterr()
    artifacts = _all_text(output_dir)
    assert "llm_unavailable" in artifacts
    assert "llm_request_rejected" in artifacts
    assert "llm_authorization" in artifacts
    assert API_KEY not in captured.err + captured.out + artifacts
    assert "KANAREK" not in captured.err + captured.out + artifacts


# --- łańcuch dostawców: główny i zapasowy ---


def _fallback_server(replies: list[object]) -> FakeLlmServer:
    return FakeLlmServer(
        replies,  # type: ignore[arg-type]
        protocol="openai",
        api_key=FALLBACK_KEY,
        host="zapas.example.test",
        model="model-zapasowy",
    )


def _use_chain(
    monkeypatch: pytest.MonkeyPatch, primary: FakeLlmServer, fallback: FakeLlmServer | None
) -> None:
    def build(settings: Settings) -> LlmChain:
        budget = LlmBudget(max_calls=50)
        return LlmChain(
            primary.client(budget=budget),
            fallback.client(budget=budget) if fallback is not None else None,
        )

    monkeypatch.setattr(cli, "build_llm_client", build)


def test_report_names_provider_and_model_that_answered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pdf(tmp_path / "in" / "x.pdf")
    _use_chain(monkeypatch, FakeLlmServer([PROBE, TRANSFER]), None)

    assert main(["process", str(tmp_path / "in"), str(tmp_path / "out")]) == 0

    assert _report(tmp_path / "out")[0]["llm"] == {
        "provider": "primary",
        "model": "atrapa",
        "switch_reason": None,
        "warnings": [],
    }


@pytest.mark.parametrize(
    ("failure", "calls", "reason"),
    [
        (429, 4, "llm_rate_limit"),
        (402, 1, "llm_payment_required"),
        (500, 4, "llm_unavailable"),
        (TIMEOUT, 4, "llm_unavailable"),
    ],
)
def test_fallback_provider_answers_when_primary_fails_mid_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: object,
    calls: int,
    reason: str,
) -> None:
    for name in ("a.pdf", "b.pdf"):
        _pdf(tmp_path / "in" / name)
    primary = FakeLlmServer([PROBE, *([failure] * calls)])  # type: ignore[list-item]
    fallback = _fallback_server([PROBE, TRANSFER, TRANSFER])
    _use_chain(monkeypatch, primary, fallback)

    assert main(["process", str(tmp_path / "in"), str(tmp_path / "out")]) == 0

    records = _report(tmp_path / "out")
    assert [record["status"] for record in records] == ["ok", "ok"]
    assert [record["llm"] for record in records] == [
        {
            "provider": "fallback",
            "model": "model-zapasowy",
            "switch_reason": reason,
            "warnings": [],
        }
    ] * 2
    # Drugi dokument nie czeka na ponowienia głównego: ten odpoczywa albo jest wyłączony.
    assert len(primary.requests) == 1 + calls
    assert _load(tmp_path / "out" / "b.json")["przelew_bankowy"]["tytul"] == "WPIS"  # type: ignore[index]
    captured = capsys.readouterr().err
    assert captured.count(f"uwaga: dostawca główny LLM zawiódł ({reason}); pytam zapasowego") == 1


def test_rejected_primary_key_is_visible_in_report_and_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _pdf(tmp_path / "in" / "x.pdf")
    primary = FakeLlmServer([PROBE, 401])
    _use_chain(monkeypatch, primary, _fallback_server([PROBE, TRANSFER]))

    assert main(["process", str(tmp_path / "in"), str(tmp_path / "out")]) == 0

    record = _report(tmp_path / "out")[0]
    assert record["status"] == "ok"
    assert record["llm"] == {
        "provider": "fallback",
        "model": "model-zapasowy",
        "switch_reason": "llm_authorization",
        "warnings": ["llm_primary_unauthorized"],
    }
    assert "uwaga: llm_primary_unauthorized" in capsys.readouterr().err


def test_both_providers_failing_is_technical_error_with_empty_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pdf(tmp_path / "in" / "x.pdf")
    primary = FakeLlmServer([PROBE, 429, 429, 429, 429])
    fallback = _fallback_server([PROBE, 500, 500, 500, 500])
    _use_chain(monkeypatch, primary, fallback)

    assert main(["process", str(tmp_path / "in"), str(tmp_path / "out")]) == 1

    record = _report(tmp_path / "out")[0]
    assert record["status"] == "technical_error"
    assert record["errors"] == [
        {
            "code": "llm_unavailable",
            "message": (
                "obaj dostawcy LLM zawiedli (główny: llm_rate_limit, zapasowy: llm_unavailable)"
            ),
            "page": None,
        }
    ]
    assert record["llm"] == {
        "provider": None,
        "model": None,
        "switch_reason": "llm_rate_limit",
        "warnings": [],
    }
    assert _load(tmp_path / "out" / "x.json") == {}


def test_self_check_with_exhausted_primary_proceeds_on_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _pdf(tmp_path / "in" / "x.pdf")
    primary = FakeLlmServer([429])
    _use_chain(monkeypatch, primary, _fallback_server([PROBE, TRANSFER]))

    assert main(["process", str(tmp_path / "in"), str(tmp_path / "out")]) == 0

    assert len(primary.requests) == 1
    assert "ostrzeżenie: dostawca główny LLM nie działa (llm_rate_limit)" in capsys.readouterr().err
    assert _report(tmp_path / "out")[0]["llm"]["provider"] == "fallback"  # type: ignore[index, call-overload]


def test_self_check_with_both_providers_down_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _pdf(tmp_path / "in" / "x.pdf")
    _use_chain(monkeypatch, FakeLlmServer([429]), _fallback_server([402]))

    assert main(["process", str(tmp_path / "in"), str(tmp_path / "out")]) == 2

    captured = capsys.readouterr().err
    assert "błąd: llm_rate_limit" in captured
    assert "dostawca zapasowy też zawiódł (llm_payment_required)" in captured
    assert not (tmp_path / "out").exists()


def test_both_api_key_canaries_never_appear_in_any_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in ("a.pdf", "b.pdf", "c.pdf"):
        _pdf(tmp_path / "in" / name)
    # Oba serwery wklejają swój klucz do treści błędów.
    primary = FakeLlmServer([PROBE, 401])
    fallback = _fallback_server([PROBE, TRANSFER, 400, 500, 500, 500, 500])
    _use_chain(monkeypatch, primary, fallback)

    assert main(["process", str(tmp_path / "in"), str(tmp_path / "out")]) == 1

    captured = capsys.readouterr()
    artifacts = _all_text(tmp_path / "out")
    assert "llm_primary_unauthorized" in artifacts
    assert "llm_request_rejected" in artifacts
    for secret in (API_KEY, FALLBACK_KEY, "KANAREK"):
        assert secret not in captured.err + captured.out + artifacts


def test_build_llm_client_creates_chain_with_shared_budget() -> None:
    chain = cli.build_llm_client(Settings.from_env(FALLBACK_ENV))

    assert isinstance(chain, LlmChain)
    assert chain.has_fallback is True
    assert (chain.budget.max_calls, chain.budget.max_total_tokens) == (9, 5000)


def test_build_llm_client_without_fallback_configuration_has_no_fallback() -> None:
    env = {name: value for name, value in FALLBACK_ENV.items() if "FALLBACK" not in name}

    assert cli.build_llm_client(Settings.from_env(env)).has_fallback is False


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"LLM_FALLBACK_API_KEY": ""}, "llm_authorization"),
        ({"LLM_FALLBACK_MODEL": ""}, "invalid_configuration"),
        ({"LLM_FALLBACK_BASE_URL": "https://obcy.example/v1"}, "invalid_configuration"),
        ({"LLM_FALLBACK_BASE_URL": "http://zapas.example.test/v1"}, "invalid_configuration"),
    ],
)
def test_broken_fallback_configuration_is_a_warning_not_an_error(
    capsys: pytest.CaptureFixture[str], changes: dict[str, str], code: str
) -> None:
    chain = cli.build_llm_client(Settings.from_env({**FALLBACK_ENV, **changes}))

    assert chain.has_fallback is False
    captured = capsys.readouterr().err
    assert f"ostrzeżenie: dostawca zapasowy LLM pominięty: {code}" in captured
    assert FALLBACK_KEY not in captured
