"""Testy klienta LLM na atrapie HTTP: kody błędów, ponowienia, tokeny, brak wycieku klucza."""

import json

import httpx
import pytest

from common import HarnessError
from config import LlmSettings
from llm import LlmClient, MockLlm, extract_json

SECRET = "sekret-testowy-123456"


def client(mock: MockLlm, protocol: str = "mock", key_file=None, **kw) -> LlmClient:
    s = LlmSettings(protocol=protocol, retries=kw.pop("retries", 2), key_file=key_file, **kw)
    sleeps: list[float] = []
    c = LlmClient(s, transport=mock.transport(), sleep=sleeps.append)
    c.sleeps = sleeps  # type: ignore[attr-defined]
    return c


def test_ok_counts_tokens_and_time():
    m = MockLlm([("ok", '{"a": 1}')])
    c = client(m)
    data, resp = c.complete_json("pytanie")
    assert data == {"a": 1}
    assert resp.input_tokens == 10 and resp.output_tokens >= 1 and resp.attempts == 1
    assert c.stats.calls == 1 and c.stats.input_tokens == 10 and c.stats.wall_s >= 0


@pytest.mark.parametrize("status,code,calls", [(401, "llm_authorization", 1), (403, "llm_authorization", 1),
                                                (429, "llm_rate_limit", 3), (503, "llm_unavailable", 3)])
def test_http_statuses_map_to_codes(status, code, calls):
    m = MockLlm(default=("status", status))
    c = client(m)
    with pytest.raises(HarnessError) as e:
        c.complete("x")
    assert e.value.code == code
    assert len(m.requests) == calls  # 401/403 bez ponowień; reszta ograniczony budżet


def test_timeout_and_connect_become_llm_unavailable_after_retries():
    for step in (("timeout",), ("connect",)):
        m = MockLlm(default=step)
        c = client(m)
        with pytest.raises(HarnessError) as e:
            c.complete("x")
        assert e.value.code == "llm_unavailable" and e.value.retryable
        assert len(m.requests) == 3 and c.sleeps == [1.0, 2.0]  # type: ignore[attr-defined]


def test_retry_recovers_after_429():
    m = MockLlm([("status", 429), ("ok", "{}")])
    c = client(m)
    resp = c.complete("x")
    assert resp.attempts == 2 and c.stats.retries == 1


@pytest.mark.parametrize("step", [("truncated", '{"klucz": "wartość długa"}'), ("garbage",), ("empty",), ("no_content",), ("ok", "to nie jest json")])
def test_malformed_responses_are_invalid_response(step):
    c = client(MockLlm(default=step))
    with pytest.raises(HarnessError) as e:
        c.complete_json("x")
    assert e.value.code == "llm_invalid_response"
    assert c.stats.failures >= 1


def test_missing_key_file_is_authorization_error_without_network(tmp_path):
    m = MockLlm()
    c = client(m, protocol="anthropic", key_file=str(tmp_path / "brak"))
    with pytest.raises(HarnessError) as e:
        c.complete("x")
    assert e.value.code == "llm_authorization" and m.requests == []


def test_key_is_sent_but_never_in_errors_or_stats(tmp_path):
    kf = tmp_path / "klucz"
    kf.write_text(SECRET)
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["x-api-key"] = req.headers.get("x-api-key")
        return httpx.Response(401, json={"error": f"zły klucz {SECRET}"})

    s = LlmSettings(protocol="anthropic", key_file=str(kf), retries=0)
    c = LlmClient(s, transport=httpx.MockTransport(handler))
    with pytest.raises(HarnessError) as e:
        c.complete("x")
    assert seen["x-api-key"] == SECRET
    assert SECRET not in str(e.value) and SECRET not in json.dumps(c.stats.to_dict()) and SECRET not in json.dumps(c.info())


def test_openai_protocol_request_and_parse(tmp_path):
    kf = tmp_path / "k"
    kf.write_text("k")
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        captured["auth"] = req.headers["authorization"]
        captured["body"] = json.loads(req.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok": true}'}, "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 7, "completion_tokens": 3}, "model": "m"})

    s = LlmSettings(protocol="openai", base_url="http://127.0.0.1:1/v1", model="m", key_file=str(kf))
    c = LlmClient(s, transport=httpx.MockTransport(handler))
    data, resp = c.complete_json("hej", system="sys", images=[("image/png", b"\x89PNG")])
    assert data == {"ok": True} and (resp.input_tokens, resp.output_tokens) == (7, 3)
    assert captured["url"].endswith("/v1/chat/completions") and captured["auth"] == "Bearer k"
    assert captured["body"]["messages"][0] == {"role": "system", "content": "sys"}


def test_anthropic_request_shape_with_image(tmp_path):
    kf = tmp_path / "k"
    kf.write_text("k")
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(req.content)
        return httpx.Response(200, json={"content": [{"type": "text", "text": "{}"}], "usage": {}})

    c = LlmClient(LlmSettings(protocol="anthropic", key_file=str(kf), effort="low"), transport=httpx.MockTransport(handler))
    c.complete("t", system="s", images=[("image/jpeg", b"abc")])
    b = captured["body"]
    assert b["system"] == "s" and b["output_config"] == {"effort": "low"} and b["temperature"] == 0.0
    assert b["messages"][0]["content"][0]["type"] == "image"


def test_unknown_protocol_is_configuration_error():
    with pytest.raises(HarnessError) as e:
        LlmClient(LlmSettings(protocol="grpc"))
    assert e.value.code == "invalid_configuration"


def test_extract_json_handles_fences():
    assert extract_json('tekst ```json\n{"a": [1]}\n``` koniec') == {"a": [1]}
    with pytest.raises(HarnessError):
        extract_json("[1,2]")
