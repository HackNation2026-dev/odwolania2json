"""Testy konfiguracji LLM: klucz, protokół, lista hostów, limity, brak sekretów w repr."""

from __future__ import annotations

from pathlib import Path

import pytest
from odwolania2json import __version__
from odwolania2json.config import (
    DEFAULT_ALLOWED_HOSTS,
    SESSION_PLACEHOLDER,
    Settings,
    build_fallback_settings,
    build_llm_settings,
    resolve_api_key,
)
from odwolania2json.errors import ProcessingError

KEY = "KANAREK-klucz-konfiguracji"
BASE = {
    "LLM_API_KEY": KEY,
    "LLM_BASE_URL": "https://api.minimax.io/anthropic/v1/messages",
    "LLM_MODEL": "model-testowy",
}


def _never(prompt: str) -> str:
    raise AssertionError("nie wolno pytać o klucz")


def test_api_key_is_hidden_in_repr() -> None:
    settings = Settings.from_env(BASE)

    assert settings.llm_api_key == KEY
    assert KEY not in repr(settings)
    assert KEY not in repr(build_llm_settings(settings, KEY))


def test_defaults_for_llm_options() -> None:
    settings = Settings.from_env({})

    assert settings.llm_allowed_hosts == DEFAULT_ALLOWED_HOSTS == ("api.minimax.io",)
    assert settings.llm_protocol is None
    assert settings.llm_api_key_file is None
    assert settings.error_export == "empty_json"
    assert (settings.llm_max_output_tokens, settings.llm_timeout_s, settings.llm_max_calls) == (
        None,
        None,
        None,
    )


def test_llm_options_are_read_from_environment() -> None:
    settings = Settings.from_env(
        {
            **BASE,
            "LLM_PROTOCOL": "openai",
            "LLM_ALLOWED_HOSTS": " Api.Example.eu , drugi.example ,",
            "LLM_API_KEY_FILE": "~/klucz",
            "LLM_MAX_OUTPUT_TOKENS": "4000",
            "LLM_TIMEOUT_S": "30.5",
            "LLM_MAX_CALLS": "7",
            "ERROR_EXPORT": "no_file",
        }
    )

    assert settings.llm_protocol == "openai"
    assert settings.llm_allowed_hosts == ("api.example.eu", "drugi.example")
    assert settings.llm_api_key_file == Path("~/klucz").expanduser()
    assert (settings.llm_max_output_tokens, settings.llm_timeout_s, settings.llm_max_calls) == (
        4000,
        30.5,
        7,
    )
    assert settings.error_export == "no_file"


@pytest.mark.parametrize(
    ("name", "value", "fragment"),
    [
        ("LLM_MAX_CALLS", "duzo", "LLM_MAX_CALLS musi być liczbą"),
        ("LLM_MAX_CALLS", "0", "LLM_MAX_CALLS musi być dodatnie"),
        ("LLM_TIMEOUT_S", "-1", "LLM_TIMEOUT_S musi być dodatnie"),
        ("LLM_MAX_OUTPUT_TOKENS", "1.5", "LLM_MAX_OUTPUT_TOKENS musi być liczbą"),
        ("LLM_MAX_RETRIES", "-1", "LLM_MAX_RETRIES nie może być mniejsze niż 0"),
        ("LLM_PROVIDER_COOLDOWN_S", "0", "LLM_PROVIDER_COOLDOWN_S musi być dodatnie"),
    ],
)
def test_bad_numeric_option_is_invalid_configuration(name: str, value: str, fragment: str) -> None:
    with pytest.raises(ProcessingError) as caught:
        Settings.from_env({name: value})

    assert caught.value.code == "invalid_configuration"
    assert fragment in caught.value.message


def test_key_from_environment_wins_over_file(tmp_path: Path) -> None:
    key_file = tmp_path / "klucz"
    key_file.write_text("klucz-z-pliku\n", encoding="utf-8")
    settings = Settings.from_env({**BASE, "LLM_API_KEY_FILE": str(key_file)})

    assert resolve_api_key(settings, interactive=False, prompt=_never) == KEY


def test_key_is_read_from_file_without_whitespace(tmp_path: Path) -> None:
    key_file = tmp_path / "klucz"
    key_file.write_text("  klucz-z-pliku \n\n", encoding="utf-8")
    settings = Settings.from_env({"LLM_API_KEY_FILE": str(key_file)})

    assert resolve_api_key(settings, interactive=True, prompt=_never) == "klucz-z-pliku"


def test_missing_key_file_is_explicit_error_without_path_content(tmp_path: Path) -> None:
    settings = Settings.from_env({"LLM_API_KEY_FILE": str(tmp_path / "brak")})

    with pytest.raises(ProcessingError) as caught:
        resolve_api_key(settings, interactive=True, prompt=_never)

    assert caught.value.code == "llm_authorization"
    assert "FileNotFoundError" in caught.value.message


def test_empty_key_file_is_explicit_error(tmp_path: Path) -> None:
    key_file = tmp_path / "klucz"
    key_file.write_text(" \n", encoding="utf-8")
    settings = Settings.from_env({"LLM_API_KEY_FILE": str(key_file)})

    with pytest.raises(ProcessingError) as caught:
        resolve_api_key(settings, interactive=False, prompt=_never)

    assert (caught.value.code, caught.value.message) == (
        "llm_authorization",
        "plik z LLM_API_KEY_FILE jest pusty",
    )


def test_missing_key_non_interactive_never_prompts() -> None:
    with pytest.raises(ProcessingError) as caught:
        resolve_api_key(Settings.from_env({}), interactive=False, prompt=_never)

    assert caught.value.code == "llm_authorization"
    assert "LLM_API_KEY" in caught.value.message


def test_missing_key_interactive_prompts_once() -> None:
    prompts: list[str] = []

    def typed(prompt: str) -> str:
        prompts.append(prompt)
        return "  wpisany-klucz  "

    assert resolve_api_key(Settings.from_env({}), interactive=True, prompt=typed) == "wpisany-klucz"
    assert len(prompts) == 1


def test_empty_interactive_answer_is_an_error() -> None:
    with pytest.raises(ProcessingError) as caught:
        resolve_api_key(Settings.from_env({}), interactive=True, prompt=lambda _prompt: "  ")

    assert caught.value.code == "llm_authorization"


def test_build_llm_settings_infers_anthropic_protocol_from_url() -> None:
    llm = build_llm_settings(Settings.from_env(BASE), KEY)

    assert llm.protocol == "anthropic"
    assert (llm.base_url, llm.model, llm.api_key) == (BASE["LLM_BASE_URL"], "model-testowy", KEY)
    assert llm.allowed_hosts == ("api.minimax.io",)
    assert llm.allow_http_localhost is True
    assert (llm.max_output_tokens, llm.retry_output_tokens, llm.max_calls) == (12000, 6000, 1000)


def test_build_llm_settings_defaults_to_openai_for_other_urls() -> None:
    settings = Settings.from_env({**BASE, "LLM_BASE_URL": "http://127.0.0.1:8080"})

    assert build_llm_settings(settings, KEY).protocol == "openai"


def test_explicit_protocol_overrides_inference() -> None:
    for protocol in ("anthropic", "openai"):
        settings = Settings.from_env({**BASE, "LLM_PROTOCOL": protocol})
        assert build_llm_settings(settings, KEY).protocol == protocol


def test_limits_from_environment_reach_client_settings() -> None:
    settings = Settings.from_env(
        {**BASE, "LLM_MAX_OUTPUT_TOKENS": "3000", "LLM_TIMEOUT_S": "20", "LLM_MAX_CALLS": "5"}
    )

    llm = build_llm_settings(settings, KEY)

    assert (llm.max_output_tokens, llm.retry_output_tokens) == (3000, 3000)
    assert (llm.timeout_s, llm.max_calls) == (20.0, 5)


def test_large_output_limit_keeps_default_retry_limit() -> None:
    settings = Settings.from_env({**BASE, "LLM_MAX_OUTPUT_TOKENS": "20000"})

    llm = build_llm_settings(settings, KEY)

    assert (llm.max_output_tokens, llm.retry_output_tokens) == (20000, 6000)


@pytest.mark.parametrize(
    ("changes", "fragment"),
    [
        ({"LLM_BASE_URL": ""}, "LLM_BASE_URL"),
        ({"LLM_MODEL": ""}, "LLM_MODEL"),
        ({"LLM_PROTOCOL": "grpc"}, "LLM_PROTOCOL"),
        ({"ERROR_EXPORT": "skasuj"}, "ERROR_EXPORT"),
    ],
)
def test_incomplete_configuration_is_explicit_error(changes: dict[str, str], fragment: str) -> None:
    settings = Settings.from_env({**BASE, **changes})

    with pytest.raises(ProcessingError) as caught:
        build_llm_settings(settings, KEY)

    assert caught.value.code == "invalid_configuration"
    assert fragment in caught.value.message
    assert KEY not in str(caught.value)


# --- dostawca zapasowy ---

FALLBACK_KEY = "KANAREK-klucz-zapasowy"
SESSION = "11111111-2222-3333-4444-555555555555"
FALLBACK = {
    **BASE,
    "LLM_ALLOWED_HOSTS": "api.minimax.io,zapas.example.eu",
    "LLM_FALLBACK_BASE_URL": "https://zapas.example.eu/openai/v1",
    "LLM_FALLBACK_MODEL": "model-zapasowy",
    "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
}


def test_fallback_is_absent_without_base_url() -> None:
    settings = Settings.from_env({**BASE, "LLM_FALLBACK_MODEL": "m", "LLM_FALLBACK_API_KEY": "k"})

    assert settings.llm_fallback_base_url is None
    assert build_fallback_settings(settings, SESSION) is None


def test_fallback_settings_are_built_from_environment() -> None:
    settings = Settings.from_env(FALLBACK)

    llm = build_fallback_settings(settings, SESSION)

    assert llm is not None
    assert (llm.protocol, llm.base_url, llm.model) == (
        "openai",
        "https://zapas.example.eu/openai/v1",
        "model-zapasowy",
    )
    assert llm.api_key == FALLBACK_KEY
    assert llm.allowed_hosts == ("api.minimax.io", "zapas.example.eu")
    assert llm.user_agent == f"odwolania2json/{__version__}"
    assert llm.extra_headers == ()
    assert llm.allow_http_localhost is True


def test_fallback_secrets_are_hidden_in_repr() -> None:
    settings = Settings.from_env(
        {**FALLBACK, "LLM_FALLBACK_HEADERS": '{"x-token": "tajny-naglowek"}'}
    )

    llm = build_fallback_settings(settings, SESSION)

    for text in (repr(settings), repr(llm)):
        assert FALLBACK_KEY not in text
        assert "tajny-naglowek" not in text


def test_fallback_headers_user_agent_protocol_and_session_placeholder() -> None:
    settings = Settings.from_env(
        {
            **FALLBACK,
            "LLM_FALLBACK_PROTOCOL": "anthropic",
            "LLM_FALLBACK_USER_AGENT": "moj-klient/1.0",
            "LLM_FALLBACK_HEADERS": '{"x-sesja": "{session}", "x-org": "stale"}',
        }
    )

    llm = build_fallback_settings(settings, SESSION)

    assert llm is not None
    assert SESSION_PLACEHOLDER == "{session}"
    assert llm.protocol == "anthropic"
    assert llm.user_agent == "moj-klient/1.0"
    assert llm.extra_headers == (("x-sesja", SESSION), ("x-org", "stale"))


def test_fallback_key_is_read_from_file(tmp_path: Path) -> None:
    key_file = tmp_path / "klucz-zapasowy"
    key_file.write_text(f"{FALLBACK_KEY}\n", encoding="utf-8")
    env = {**FALLBACK, "LLM_FALLBACK_API_KEY": "", "LLM_FALLBACK_KEY_FILE": str(key_file)}

    llm = build_fallback_settings(Settings.from_env(env), SESSION)

    assert llm is not None
    assert llm.api_key == FALLBACK_KEY


def test_fallback_shares_limits_with_primary() -> None:
    env = {**FALLBACK, "LLM_MAX_CALLS": "5", "LLM_TIMEOUT_S": "20", "LLM_MAX_TOTAL_TOKENS": "900"}
    settings = Settings.from_env(env)

    llm = build_fallback_settings(settings, SESSION)

    assert llm is not None
    assert (llm.max_calls, llm.timeout_s) == (5, 20.0)
    assert settings.llm_max_total_tokens == 900


@pytest.mark.parametrize(
    ("changes", "code", "fragment"),
    [
        ({"LLM_FALLBACK_MODEL": ""}, "invalid_configuration", "LLM_FALLBACK_MODEL"),
        ({"LLM_FALLBACK_API_KEY": ""}, "llm_authorization", "LLM_FALLBACK_KEY_FILE"),
        ({"LLM_FALLBACK_PROTOCOL": "grpc"}, "invalid_configuration", "LLM_FALLBACK_PROTOCOL"),
        (
            {"LLM_FALLBACK_API_KEY": "", "LLM_FALLBACK_KEY_FILE": "/nie/ma/takiego/pliku"},
            "llm_authorization",
            "LLM_FALLBACK_KEY_FILE (FileNotFoundError)",
        ),
    ],
)
def test_incomplete_fallback_configuration_is_explicit_error(
    changes: dict[str, str], code: str, fragment: str
) -> None:
    settings = Settings.from_env({**FALLBACK, **changes})

    with pytest.raises(ProcessingError) as caught:
        build_fallback_settings(settings, SESSION)

    assert caught.value.code == code
    assert fragment in caught.value.message
    assert FALLBACK_KEY not in str(caught.value)


@pytest.mark.parametrize(
    "raw", ["to nie JSON", '["lista"]', '{"x": 1}', '{"x": {"y": "z"}}', '"tekst"']
)
def test_fallback_headers_must_be_json_object_of_text(raw: str) -> None:
    with pytest.raises(ProcessingError) as caught:
        Settings.from_env({"LLM_FALLBACK_HEADERS": raw})

    assert caught.value.code == "invalid_configuration"
    assert "LLM_FALLBACK_HEADERS musi być obiektem JSON" in caught.value.message
    assert "lista" not in caught.value.message


def test_retry_count_and_cooldown_are_configurable() -> None:
    env = {**FALLBACK, "LLM_MAX_RETRIES": "0", "LLM_PROVIDER_COOLDOWN_S": "86400"}
    settings = Settings.from_env(env)

    fallback = build_fallback_settings(settings, SESSION)

    assert build_llm_settings(settings, KEY).max_retries == 0
    assert fallback is not None
    assert fallback.max_retries == 0
    assert settings.llm_provider_cooldown_s == 86400.0
    assert build_llm_settings(Settings.from_env(BASE), KEY).max_retries == 3
