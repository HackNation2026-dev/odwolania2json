"""Testy klienta LLM na atrapie HTTP: kody błędów, ponowienia, limity, brak wycieku klucza."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest
from odwolania2json.errors import ProcessingError
from odwolania2json.llm.client import (
    Image,
    LlmClient,
    LlmSettings,
    estimate_tokens,
    parse_json_object,
    validate_base_url,
)

CANARY = "sk-KANAREK-7f3a9c1e5b2d4f60"
URL = "https://api.minimax.io/anthropic/v1/messages"

Handler = Callable[[httpx.Request], httpx.Response]


def _settings(**overrides: object) -> LlmSettings:
    values: dict[str, object] = {
        "protocol": "anthropic",
        "base_url": URL,
        "model": "model-testowy",
        "api_key": CANARY,
        "allowed_hosts": ("api.minimax.io",),
    }
    values.update(overrides)
    return LlmSettings(**values)  # type: ignore[arg-type]


def _anthropic(text: str, **extra: object) -> httpx.Response:
    body: dict[str, object] = {
        "id": "x",
        "model": "model-zwrocony",
        "stop_reason": "end_turn",
        "content": [{"type": "thinking", "thinking": "..."}, {"type": "text", "text": text}],
        "usage": {"input_tokens": 11, "output_tokens": 7},
    }
    body.update(extra)
    return httpx.Response(200, json=body)


class _Script:
    """Atrapa: kolejne odpowiedzi ze skryptu, zapis żądań i uśpień."""

    def __init__(self, *steps: httpx.Response | Exception | Handler) -> None:
        self.steps = list(steps)
        self.requests: list[httpx.Request] = []
        self.sleeps: list[float] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        step = self.steps.pop(0) if len(self.steps) > 1 else self.steps[0]
        if isinstance(step, Exception):
            raise step
        if isinstance(step, httpx.Response):
            return step
        return step(request)

    def client(self, **overrides: object) -> LlmClient:
        return LlmClient(
            _settings(**overrides),
            transport=httpx.MockTransport(self.handle),
            sleep=self.sleeps.append,
        )

    def bodies(self) -> list[dict[str, object]]:
        return [json.loads(request.content) for request in self.requests]


def _error_with_canary(status: int, **headers: str) -> httpx.Response:
    return httpx.Response(
        status, json={"error": {"message": f"invalid key {CANARY}"}}, headers=headers
    )


# --- adres i konfiguracja ---


def test_base_url_must_be_https() -> None:
    with pytest.raises(ProcessingError, match="https") as caught:
        validate_base_url("http://api.minimax.io/v1", ("api.minimax.io",))
    assert caught.value.code == "invalid_configuration"


def test_base_url_host_must_be_on_allow_list() -> None:
    with pytest.raises(ProcessingError, match="spoza listy") as caught:
        validate_base_url("https://evil.example/v1", ("api.minimax.io",))
    assert caught.value.code == "invalid_configuration"


@pytest.mark.parametrize(
    "url",
    [
        "https://api.minimax.io.evil.example/v1",
        "https://user:pass@api.minimax.io/v1",
        "https:///v1",
        "api.minimax.io/v1",
        "https://[::1/v1",
        "",
    ],
)
def test_base_url_rejects_lookalikes_credentials_and_garbage(url: str) -> None:
    with pytest.raises(ProcessingError) as caught:
        validate_base_url(url, ("api.minimax.io",))
    assert caught.value.code == "invalid_configuration"


def test_base_url_host_comparison_ignores_case() -> None:
    assert validate_base_url("https://API.MiniMax.io/v1", ("api.minimax.IO",))


def test_http_localhost_requires_explicit_flag() -> None:
    with pytest.raises(ProcessingError):
        validate_base_url("http://127.0.0.1:8080/v1", ())
    assert validate_base_url("http://127.0.0.1:8080/v1", (), allow_http_localhost=True)
    assert validate_base_url("http://localhost:1/v1", (), allow_http_localhost=True)
    with pytest.raises(ProcessingError):
        validate_base_url("http://example.com/v1", ("example.com",), allow_http_localhost=True)


def test_client_rejects_bad_url_unknown_protocol_and_missing_values() -> None:
    with pytest.raises(ProcessingError) as bad_url:
        LlmClient(_settings(base_url="https://evil.example/v1"))
    assert bad_url.value.code == "invalid_configuration"
    with pytest.raises(ProcessingError) as bad_protocol:
        LlmClient(_settings(protocol="gemini"))
    assert bad_protocol.value.code == "invalid_configuration"
    with pytest.raises(ProcessingError) as no_key:
        LlmClient(_settings(api_key="  "))
    assert no_key.value.code == "llm_authorization"
    with pytest.raises(ProcessingError) as no_model:
        LlmClient(_settings(model=""))
    assert no_model.value.code == "invalid_configuration"


def test_settings_repr_hides_key() -> None:
    assert CANARY not in repr(_settings())
    assert CANARY not in repr(LlmClient(_settings()).settings)


# --- nagłówki i treść żądania ---


def test_anthropic_request_has_single_key_header_and_expected_body() -> None:
    script = _Script(_anthropic("ok"))
    reply = script.client().complete("system", "użytkownik", [Image("image/jpeg", b"\xff\xd8")])

    request = script.requests[0]
    assert str(request.url) == URL
    assert request.headers["x-api-key"] == CANARY
    assert "authorization" not in request.headers
    assert request.headers["anthropic-version"] == "2023-06-01"
    carriers = [name for name, value in request.headers.items() if CANARY in value]
    assert carriers == ["x-api-key"]
    body = script.bodies()[0]
    assert body["model"] == "model-testowy"
    assert body["max_tokens"] == 12000
    assert body["temperature"] == 0.0
    assert body["system"] == "system"
    assert "output_config" not in body
    assert body["messages"] == [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": "/9g="},
                },
                {"type": "text", "text": "użytkownik"},
            ],
        }
    ]
    assert CANARY not in request.content.decode()
    assert reply.text == "ok"
    assert (reply.input_tokens, reply.output_tokens) == (11, 7)
    assert (reply.model, reply.stop_reason, reply.attempts) == ("model-zwrocony", "end_turn", 1)


def test_openai_request_uses_bearer_header_and_chat_completions_path() -> None:
    response = httpx.Response(
        200,
        json={
            "model": "m",
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2},
        },
    )
    script = _Script(response)
    client = script.client(
        protocol="openai", base_url="https://llm.example/v1/", allowed_hosts=("llm.example",)
    )

    reply = client.complete("system", "użytkownik", [Image("image/png", b"\x89P")])

    request = script.requests[0]
    assert str(request.url) == "https://llm.example/v1/chat/completions"
    assert request.headers["authorization"] == f"Bearer {CANARY}"
    assert "x-api-key" not in request.headers
    assert "anthropic-version" not in request.headers
    body = script.bodies()[0]
    assert body["messages"] == [
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "użytkownik"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVA="}},
            ],
        },
    ]
    assert body["max_tokens"] == 12000
    assert (reply.text, reply.input_tokens, reply.output_tokens) == ("ok", 5, 2)
    assert (reply.model, reply.stop_reason) == ("m", "stop")


def test_openai_full_endpoint_is_not_extended() -> None:
    script = _Script(httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}))
    url = "https://llm.example/v1/chat/completions"
    reply = script.client(protocol="openai", base_url=url, allowed_hosts=("llm.example",)).complete(
        "s", "u"
    )

    assert str(script.requests[0].url) == url
    assert (reply.input_tokens, reply.output_tokens, reply.stop_reason) == (None, None, None)


def test_openai_without_choices_or_content_is_invalid_response() -> None:
    for payload in ({"choices": []}, {"choices": [{"message": {"content": None}}]}, {"id": 1}):
        script = _Script(httpx.Response(200, json=payload))
        client = script.client(
            protocol="openai", base_url="https://llm.example/v1", allowed_hosts=("llm.example",)
        )
        with pytest.raises(ProcessingError) as caught:
            client.complete("s", "u")
        assert caught.value.code == "llm_invalid_response"


def test_redirects_are_not_followed() -> None:
    script = _Script(httpx.Response(307, headers={"location": "https://evil.example/steal"}))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete("s", "u")

    assert caught.value.code == "llm_request_rejected"
    assert len(script.requests) == 1


# --- kody błędów i ponowienia ---


@pytest.mark.parametrize("status", [401, 403])
def test_authorization_error_is_not_retried_and_hides_key(status: int) -> None:
    script = _Script(_error_with_canary(status))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete("s", "u")

    assert caught.value.code == "llm_authorization"
    assert str(status) in caught.value.message
    assert CANARY not in str(caught.value)
    assert CANARY not in repr(caught.value)
    assert len(script.requests) == 1
    assert script.sleeps == []


def test_rate_limit_honours_retry_after_then_succeeds() -> None:
    script = _Script(_error_with_canary(429, **{"retry-after": "7"}), _anthropic("ok"))

    reply = script.client().complete("s", "u")

    assert reply.text == "ok"
    assert reply.attempts == 2
    assert script.sleeps == [7.0]


def test_retry_after_is_capped_at_limit() -> None:
    script = _Script(_error_with_canary(429, **{"retry-after": "3600"}), _anthropic("ok"))

    script.client().complete("s", "u")

    assert script.sleeps == [60.0]


def test_retry_after_http_date_is_understood() -> None:
    moment = format_datetime(datetime.now(UTC) + timedelta(seconds=30), usegmt=True)
    script = _Script(_error_with_canary(429, **{"retry-after": moment}), _anthropic("ok"))

    script.client().complete("s", "u")

    assert 25.0 <= script.sleeps[0] <= 30.0


@pytest.mark.parametrize("header", ["wkrotce", "nan", "inf", "-5", "Mon, 99 Foo 2026 00:00:00"])
def test_unusable_retry_after_falls_back_to_backoff(header: str) -> None:
    script = _Script(_error_with_canary(429, **{"retry-after": header}), _anthropic("ok"))

    script.client().complete("s", "u")

    assert script.sleeps == [1.0]


def test_rate_limit_gives_up_after_three_retries_with_exponential_backoff() -> None:
    script = _Script(_error_with_canary(429))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete("s", "u")

    assert caught.value.code == "llm_rate_limit"
    assert "429" in caught.value.message
    assert CANARY not in str(caught.value)
    assert len(script.requests) == 4
    assert script.sleeps == [1.0, 2.0, 4.0]


def test_backoff_is_capped_by_configured_limit() -> None:
    script = _Script(_error_with_canary(500))

    with pytest.raises(ProcessingError):
        script.client(max_retries=5, max_retry_delay_s=3.0).complete("s", "u")

    assert script.sleeps == [1.0, 2.0, 3.0, 3.0, 3.0]


@pytest.mark.parametrize("status", [500, 502, 503, 529])
def test_server_error_is_retried_then_reported(status: int) -> None:
    script = _Script(_error_with_canary(status))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete("s", "u")

    assert caught.value.code == "llm_unavailable"
    assert str(status) in caught.value.message
    assert CANARY not in str(caught.value)
    assert len(script.requests) == 4


def test_server_error_then_success() -> None:
    script = _Script(_error_with_canary(500), _error_with_canary(503), _anthropic("ok"))

    reply = script.client().complete("s", "u")

    assert reply.attempts == 3
    assert script.sleeps == [1.0, 2.0]


def test_timeout_is_retried_then_reported() -> None:
    script = _Script(httpx.ReadTimeout(f"timeout {CANARY}"))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete("s", "u")

    assert caught.value.code == "llm_unavailable"
    assert "limit czasu" in caught.value.message
    assert CANARY not in str(caught.value)
    assert len(script.requests) == 4


def test_network_error_is_retried_and_message_has_only_class_name() -> None:
    script = _Script(httpx.ConnectError(f"https://x/?key={CANARY}"), _anthropic("ok"))

    assert script.client().complete("s", "u").attempts == 2

    failing = _Script(httpx.ConnectError(f"https://x/?key={CANARY}"))
    with pytest.raises(ProcessingError) as caught:
        failing.client().complete("s", "u")
    assert caught.value.code == "llm_unavailable"
    assert "ConnectError" in caught.value.message
    assert CANARY not in str(caught.value)


@pytest.mark.parametrize("status", [400, 404, 422])
def test_other_client_error_is_rejected_request_without_retry(status: int) -> None:
    script = _Script(_error_with_canary(status))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete("s", "u")

    assert caught.value.code == "llm_request_rejected"
    assert CANARY not in str(caught.value)
    assert len(script.requests) == 1


def test_html_body_is_invalid_response() -> None:
    script = _Script(httpx.Response(200, content=b"<html>Bad gateway</html>"))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete("s", "u")

    assert caught.value.code == "llm_invalid_response"
    assert len(script.requests) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "bez content"},
        {"content": "tekst zamiast listy"},
        {"content": [{"type": "text", "text": "   "}]},
        {"content": [{"type": "thinking", "thinking": "tylko rozumowanie"}]},
        ["lista"],
    ],
)
def test_unexpected_or_empty_envelope_is_invalid_response(payload: object) -> None:
    script = _Script(httpx.Response(200, json=payload))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete("s", "u")

    assert caught.value.code == "llm_invalid_response"


def test_extra_envelope_fields_are_ignored_and_usage_is_optional() -> None:
    script = _Script(
        httpx.Response(
            200,
            json={"content": [{"type": "text", "text": "ok", "citations": []}], "nowe_pole": 1},
        )
    )
    client = script.client()

    reply = client.complete("s", "u")

    assert reply.text == "ok"
    assert reply.input_tokens is None
    assert (client.input_tokens, client.output_tokens) == (0, 0)


# --- limity ---


def test_call_limit_stops_before_network_and_counts_retries() -> None:
    script = _Script(_error_with_canary(500), _anthropic("ok"))
    client = script.client(max_calls=3)

    client.complete("s", "u")
    assert client.calls == 2
    client.complete("s", "u")
    assert client.calls == 3
    with pytest.raises(ProcessingError) as caught:
        client.complete("s", "u")

    assert caught.value.code == "llm_call_limit"
    assert "3" in caught.value.message
    assert len(script.requests) == 3


def test_token_counters_accumulate() -> None:
    script = _Script(_anthropic("ok"))
    client = script.client()

    client.complete("s", "u")
    client.complete("s", "u")

    assert (client.input_tokens, client.output_tokens, client.calls) == (22, 14, 2)


def test_input_limit_is_enforced_before_network() -> None:
    script = _Script(_anthropic("ok"))
    client = script.client(max_input_tokens=100)

    client.complete("s" * 150, "u" * 150)
    with pytest.raises(ProcessingError) as caught:
        client.complete("s" * 150, "u" * 151)

    assert caught.value.code == "llm_input_limit"
    assert len(script.requests) == 1


def test_estimate_tokens_counts_characters_and_images() -> None:
    assert estimate_tokens([], 0) == 0
    assert estimate_tokens(["abc", "d"], 0) == 2
    assert estimate_tokens(["abc"], 2) == 5001


def test_output_limit_cannot_exceed_configured_maximum() -> None:
    script = _Script(_anthropic("ok"))
    client = script.client(max_output_tokens=500)

    client.complete("s", "u", max_output_tokens=9000)
    client.complete("s", "u", max_output_tokens=100, effort="low")

    bodies = script.bodies()
    assert bodies[0]["max_tokens"] == 500
    assert bodies[1]["max_tokens"] == 100
    assert bodies[1]["output_config"] == {"effort": "low"}


# --- JSON i schemat ---


@pytest.mark.parametrize(
    "text",
    [
        '{"a": 1}',
        '  {"a": 1}\n',
        '```json\n{"a": 1}\n```',
        '```\n{"a": 1}\n```  ',
        '```json\n{"a": 1}',
    ],
)
def test_parse_json_object_accepts_plain_and_fenced(text: str) -> None:
    assert parse_json_object(text) == {"a": 1}


@pytest.mark.parametrize(
    "text",
    [
        '{"a": 1',
        'Oto wynik: {"a": 1}',
        '{"a": 1} koniec',
        "[1, 2]",
        '"tekst"',
        "",
        "```",
    ],
)
def test_parse_json_object_does_not_guess(text: str) -> None:
    with pytest.raises(ProcessingError) as caught:
        parse_json_object(text)
    assert caught.value.code == "llm_invalid_response"


def _require_class(data: dict[str, object]) -> str:
    value = data.get("class")
    if not isinstance(value, str):
        raise ProcessingError("llm_invalid_response", "brak klasy")
    return value


def test_complete_json_returns_validated_value_in_one_call() -> None:
    script = _Script(_anthropic('{"class": "appeal", "dodatkowe": true}'))

    assert script.client().complete_json("s", "u", None, _require_class) == "appeal"
    assert len(script.requests) == 1


def test_truncated_json_gets_one_retry_with_shorter_output_limit() -> None:
    script = _Script(
        _anthropic('{"class": "appe', stop_reason="max_tokens"), _anthropic('{"class": "appeal"}')
    )

    result = script.client(retry_effort="low").complete_json("s", "u", None, _require_class)

    assert result == "appeal"
    first, second = script.bodies()
    assert first["max_tokens"] == 12000
    assert "output_config" not in first
    assert second["max_tokens"] == 6000
    assert second["output_config"] == {"effort": "low"}
    first_text = first["messages"][0]["content"][-1]["text"]  # type: ignore[index]
    second_text = second["messages"][0]["content"][-1]["text"]  # type: ignore[index]
    assert first_text == "u"
    assert second_text.startswith("u\n\nPoprzednia odpowiedź")


def test_retry_output_limit_never_exceeds_maximum() -> None:
    script = _Script(_anthropic("nie json"), _anthropic('{"class": "x"}'))

    script.client(max_output_tokens=1000).complete_json("s", "u", None, _require_class)

    assert [body["max_tokens"] for body in script.bodies()] == [1000, 1000]


def test_schema_violation_twice_is_invalid_response_after_two_calls() -> None:
    script = _Script(_anthropic('{"class": 5}'))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete_json("s", "u", None, _require_class)

    assert caught.value.code == "llm_invalid_response"
    assert len(script.requests) == 2


def test_html_then_valid_answer_is_recovered_by_schema_retry() -> None:
    script = _Script(httpx.Response(200, content=b"<html></html>"), _anthropic('{"class": "x"}'))

    assert script.client().complete_json("s", "u", None, _require_class) == "x"


def test_complete_json_does_not_retry_authorization_error() -> None:
    script = _Script(_error_with_canary(401))

    with pytest.raises(ProcessingError) as caught:
        script.client().complete_json("s", "u", None, _require_class)

    assert caught.value.code == "llm_authorization"
    assert len(script.requests) == 1


# --- self-check ---


def test_self_check_sends_one_small_probe() -> None:
    script = _Script(_anthropic("OK"))

    script.client().self_check()

    assert len(script.requests) == 1
    assert script.bodies()[0]["max_tokens"] == 16


def test_self_check_accepts_empty_text_because_only_acceptance_matters() -> None:
    script = _Script(_anthropic("", stop_reason="max_tokens"))

    script.client().self_check()


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "llm_authorization"),
        (403, "llm_authorization"),
        (429, "llm_rate_limit"),
        (500, "llm_unavailable"),
        (404, "llm_request_rejected"),
    ],
)
def test_self_check_fails_fast_without_retries(status: int, code: str) -> None:
    script = _Script(_error_with_canary(status, **{"retry-after": "30"}))

    with pytest.raises(ProcessingError) as caught:
        script.client().self_check()

    assert caught.value.code == code
    assert CANARY not in str(caught.value)
    assert len(script.requests) == 1
    assert script.sleeps == []


def test_processing_error_rejects_unknown_code_and_formats_message() -> None:
    with pytest.raises(ValueError, match="nieznany kod"):
        ProcessingError("wymyslony", "x")
    error = ProcessingError("ocr_error", "opis", page=3)
    assert str(error) == "ocr_error: opis"
    assert error.page == 3
    assert error.retry_after_s is None
