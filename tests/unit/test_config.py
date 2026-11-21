"""Testy konfiguracji aplikacji, normalizacji adresu bazy i poleceń CLI."""

from pathlib import Path

import pytest

from odwolania2json.cli import APP_NAME, build_parser, main
from odwolania2json.config import Settings
from odwolania2json.db.repository import is_configured, normalize_url


def test_settings_from_env_reads_database_url():
    settings = Settings.from_env({"DATABASE_URL": "postgresql://u:p@h:5432/d"})
    assert settings.database_url == "postgresql://u:p@h:5432/d"


def test_settings_without_database_url_is_usable():
    settings = Settings.from_env({})
    assert settings.database_url is None
    assert settings.docs_enabled is False


def test_normalize_url_switches_to_pg8000_driver():
    assert normalize_url("postgresql://u:p@h/db") == "postgresql+pg8000://u:p@h/db"


def test_settings_from_env_without_argument_reads_process_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:5433/d")
    monkeypatch.setenv("INPUT_DIR", "przykladowy-input")
    monkeypatch.setenv("OUTPUT_DIR", "przykladowy-output")
    monkeypatch.setenv("OCR_ENABLED", "1")
    monkeypatch.setenv("O2J_DOCS_ENABLED", "1")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("LLM_MODEL", "model-lokalny")
    monkeypatch.setenv("LLM_API_KEY", "tajny-klucz")

    settings = Settings.from_env()

    assert settings.database_url == "postgresql://u:p@h:5433/d"
    assert settings.input_dir == Path("przykladowy-input")
    assert settings.output_dir == Path("przykladowy-output")
    assert settings.ocr_enabled is True
    assert settings.docs_enabled is True
    assert settings.llm_base_url == "http://127.0.0.1:11434/v1"
    assert settings.llm_model == "model-lokalny"
    assert settings.llm_api_key == "tajny-klucz"


def test_settings_defaults_are_applied():
    settings = Settings.from_env({})

    assert settings.input_dir == Path("input")
    assert settings.output_dir == Path("output")
    assert settings.llm_base_url is None
    assert settings.llm_model is None
    assert settings.llm_api_key is None
    assert settings.ocr_enabled is False


def test_settings_web_dir_points_to_apps_web():
    settings = Settings.from_env({})

    assert settings.web_dir.name == "web"
    assert settings.web_dir.parent.name == "apps"


def test_settings_web_dir_can_be_overridden():
    settings = Settings.from_env({"O2J_WEB_DIR": "/tmp/przykladowy-web"})

    assert settings.web_dir == Path("/tmp/przykladowy-web")


def test_settings_are_immutable():
    settings = Settings.from_env({})

    try:
        settings.database_url = "postgresql://u:p@h/db"  # type: ignore[misc]
    except Exception as error:  # noqa: BLE001 - frozen dataclass blokuje zapis
        assert "frozen" in str(type(error)).lower() or "attribute" in str(error).lower()
    else:  # pragma: no cover - zapis nie powinien być możliwy
        raise AssertionError("Ustawienia powinny być niezmienne")


def test_normalize_url_accepts_postgres_scheme():
    assert normalize_url("postgres://u:p@h/db") == "postgresql+pg8000://u:p@h/db"


def test_normalize_url_keeps_explicit_driver():
    assert normalize_url("postgresql+pg8000://u:p@h/db") == "postgresql+pg8000://u:p@h/db"


def test_normalize_url_keeps_other_schemes():
    assert normalize_url("sqlite:///tmp/o2j.db") == "sqlite:///tmp/o2j.db"


def test_is_configured_tells_about_database_url():
    assert is_configured("postgresql://u:p@h/db") is True
    assert is_configured(None) is False
    assert is_configured("") is False
    assert is_configured("   ") is False


def test_cli_exposes_application_name():
    assert APP_NAME == "Odwołania2JSON"


def test_cli_without_arguments_prints_help(capsys):
    assert main([]) == 0
    assert "Odwołania2JSON" in capsys.readouterr().out


def test_cli_help_exits_with_zero(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])
    assert exit_info.value.code == 0
    assert "Odwołania2JSON" in capsys.readouterr().out


def test_cli_migrate_without_database_url_is_skipped(monkeypatch, capsys):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert main(["migrate"]) == 0
    assert "pominięto: baza nie skonfigurowana" in capsys.readouterr().out


def test_cli_migrate_applies_migrations(monkeypatch, capsys):
    calls: list[str] = []

    def fake_migrate(database_url: str) -> list[str]:
        calls.append(database_url)
        return ["0001_initial"]

    monkeypatch.setattr("odwolania2json.db.migrate.migrate", fake_migrate)
    assert main(["migrate", "--database-url", "postgresql://u:p@h/db"]) == 0
    assert calls == ["postgresql://u:p@h/db"]
    assert "0001_initial" in capsys.readouterr().out


def test_cli_migrate_takes_database_url_from_environment(monkeypatch, capsys):
    calls: list[str] = []

    def fake_migrate(database_url: str) -> list[str]:
        calls.append(database_url)
        return []

    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:5432/d")
    monkeypatch.setattr("odwolania2json.db.migrate.migrate", fake_migrate)
    assert main(["migrate"]) == 0
    assert calls == ["postgresql://u:p@h:5432/d"]


def test_build_parser_knows_migrate_command():
    parser = build_parser()
    arguments = parser.parse_args(["migrate"])
    assert arguments.command == "migrate"
    assert arguments.database_url is None
