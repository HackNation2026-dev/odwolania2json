"""Klient LLM po HTTP: protokół Anthropic (MiniMax) i OpenAI-zgodny, plus atrapa do testów i E14.

Zasady:
- Klucz czytany z pliku w chwili wywołania (`key_file` → `MINIMAX_KEY_FILE` → `~/kluczMiniMaxKacper`),
  trzymany tylko w zmiennej lokalnej. Nagłówków autoryzacji ani klucza nie logujemy, nie zapisujemy
  i nie wstawiamy do komunikatów błędów (`redact`).
- 401/403 nie jest ponawiane. 429, 5xx, timeouty i błędy sieci mają ograniczony budżet prób.
- Każda awaria to `HarnessError` z kodem z architektury §6; nigdy zmyślona odpowiedź.
- Zliczamy tokeny i czas ścienny (`LlmStats`), żeby eksperymenty raportowały koszt.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from common import HarnessError
from config import LlmSettings

DEFAULT_KEY_FILE = Path.home() / "kluczMiniMaxKacper"


@dataclass
class LlmResponse:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    latency_s: float
    attempts: int
    model: str | None
    stop_reason: str | None


@dataclass
class LlmStats:
    calls: int = 0
    failures: int = 0
    retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    wall_s: float = 0.0
    error_codes: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def resolve_key_path(settings: LlmSettings) -> Path:
    return Path(settings.key_file or os.environ.get("MINIMAX_KEY_FILE") or DEFAULT_KEY_FILE).expanduser()


def _read_key(settings: LlmSettings) -> str:
    path = resolve_key_path(settings)
    try:
        key = path.read_text(encoding="utf-8").strip()
    except OSError:
        raise HarnessError("llm_authorization", "brak odczytywalnego pliku z kluczem API", stage="llm") from None
    if not key:
        raise HarnessError("llm_authorization", "plik z kluczem API jest pusty", stage="llm")
    return key


def extract_json(text: str) -> dict[str, Any]:
    """Pierwszy obiekt JSON z odpowiedzi (także w bloku ```json); błąd => llm_invalid_response."""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", t, re.S)
    if m:
        t = m.group(1)
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        raise HarnessError("llm_invalid_response", "odpowiedź bez obiektu JSON", stage="llm")
    try:
        obj = json.loads(t[start:end + 1])
    except ValueError:
        raise HarnessError("llm_invalid_response", "odpowiedź z urwanym lub niepoprawnym JSON", stage="llm") from None
    if not isinstance(obj, dict):
        raise HarnessError("llm_invalid_response", "JSON odpowiedzi nie jest obiektem", stage="llm")
    return obj


class LlmClient:
    def __init__(self, settings: LlmSettings, *, transport: httpx.BaseTransport | None = None,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.settings = settings
        self.stats = LlmStats()
        self._sleep = sleep
        self._transport = transport
        if settings.protocol == "mock" and transport is None:
            self._transport = MockLlm().transport()
        if settings.protocol not in ("anthropic", "openai", "mock"):
            raise HarnessError("invalid_configuration", f"nieznany protokół LLM: {settings.protocol}", stage="llm")

    # ---- budowa żądania ----
    def _request(self, system: str | None, user: str, images: list[tuple[str, bytes]], key: str | None) -> tuple[str, dict[str, str], dict[str, Any]]:
        s = self.settings
        if s.protocol in ("anthropic", "mock"):
            content: list[dict[str, Any]] = []
            for media, data in images:
                content.append({"type": "image", "source": {"type": "base64", "media_type": media,
                                                            "data": base64.b64encode(data).decode()}})
            content.append({"type": "text", "text": user})
            body: dict[str, Any] = {"model": s.model, "max_tokens": s.max_tokens, "temperature": s.temperature,
                                    "messages": [{"role": "user", "content": content}]}
            if system:
                body["system"] = system
            if s.effort:
                body["output_config"] = {"effort": s.effort}
            headers = {"Content-Type": "application/json", "anthropic-version": "2023-06-01"}
            if key:
                headers |= {"x-api-key": key, "Authorization": f"Bearer {key}"}
            return s.base_url, headers, body
        parts: list[dict[str, Any]] = [{"type": "text", "text": user}]
        for media, data in images:
            parts.append({"type": "image_url", "image_url": {"url": f"data:{media};base64,{base64.b64encode(data).decode()}"}})
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": parts}]
        url = s.base_url if s.base_url.rstrip("/").endswith("/chat/completions") else s.base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return url, headers, {"model": s.model, "max_tokens": s.max_tokens, "temperature": s.temperature, "messages": messages}

    def _parse(self, payload: dict[str, Any]) -> tuple[str, int | None, int | None, str | None, str | None]:
        if self.settings.protocol in ("anthropic", "mock"):
            blocks = payload.get("content")
            if not isinstance(blocks, list):
                raise HarnessError("llm_invalid_response", "brak pola content w odpowiedzi", stage="llm")
            text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
            usage = payload.get("usage") or {}
            return text, usage.get("input_tokens"), usage.get("output_tokens"), payload.get("model"), payload.get("stop_reason")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise HarnessError("llm_invalid_response", "brak pola choices w odpowiedzi", stage="llm")
        text = (choices[0].get("message") or {}).get("content") or ""
        usage = payload.get("usage") or {}
        return text, usage.get("prompt_tokens"), usage.get("completion_tokens"), payload.get("model"), choices[0].get("finish_reason")

    # ---- wywołanie z ponowieniami ----
    def complete(self, user: str, *, system: str | None = None, images: list[tuple[str, bytes]] | None = None) -> LlmResponse:
        s = self.settings
        key = None if s.protocol == "mock" else _read_key(s)  # brak klucza = jawny llm_authorization, bez sieci
        secrets = [key] if key else []
        url, headers, body = self._request(system, user, images or [], key)
        t0 = time.monotonic()
        attempts = 0
        last: HarnessError | None = None
        self.stats.calls += 1
        with httpx.Client(transport=self._transport, timeout=s.timeout_s) as http:
            while attempts <= s.retries:
                attempts += 1
                try:
                    resp = http.post(url, headers=headers, json=body)
                except httpx.TimeoutException:
                    last = HarnessError("llm_unavailable", "przekroczono limit czasu połączenia z LLM", stage="llm", retryable=True)
                except httpx.HTTPError as e:
                    last = HarnessError("llm_unavailable", f"błąd sieci: {type(e).__name__}", stage="llm", retryable=True)
                else:
                    if resp.status_code in (401, 403):
                        last = HarnessError("llm_authorization", f"HTTP {resp.status_code}", stage="llm")
                        break  # bez pętli ponowień (architektura §9.1)
                    if resp.status_code == 429:
                        last = HarnessError("llm_rate_limit", "HTTP 429", stage="llm", retryable=True)
                    elif resp.status_code >= 500:
                        last = HarnessError("llm_unavailable", f"HTTP {resp.status_code}", stage="llm", retryable=True)
                    elif resp.status_code >= 400:
                        last = HarnessError("llm_invalid_response", f"HTTP {resp.status_code}", stage="llm")
                        break
                    else:
                        try:
                            payload = resp.json()
                            if not isinstance(payload, dict):
                                raise ValueError
                        except ValueError:
                            last = HarnessError("llm_invalid_response", "ciało odpowiedzi nie jest obiektem JSON", stage="llm")
                            break
                        try:
                            text, tin, tout, model, stop = self._parse(payload)
                        except HarnessError as e:
                            last = e
                            break
                        if not text.strip():
                            last = HarnessError("llm_invalid_response", "pusta odpowiedź modelu", stage="llm")
                            break
                        latency = time.monotonic() - t0
                        self.stats.input_tokens += tin or 0
                        self.stats.output_tokens += tout or 0
                        self.stats.wall_s += latency
                        self.stats.retries += attempts - 1
                        return LlmResponse(text, tin, tout, latency, attempts, model, stop)
                if attempts <= s.retries:
                    self._sleep(min(2.0 ** (attempts - 1), 8.0))
        assert last is not None
        self.stats.failures += 1
        self.stats.retries += attempts - 1
        self.stats.wall_s += time.monotonic() - t0
        self.stats.error_codes[last.code] = self.stats.error_codes.get(last.code, 0) + 1
        raise HarnessError(last.code, redact_msg(last.description, secrets), stage="llm", retryable=last.retryable)

    def complete_json(self, user: str, *, system: str | None = None, images: list[tuple[str, bytes]] | None = None) -> tuple[dict[str, Any], LlmResponse]:
        resp = self.complete(user, system=system, images=images)
        try:
            return extract_json(resp.text), resp
        except HarnessError:
            self.stats.failures += 1
            self.stats.error_codes["llm_invalid_response"] = self.stats.error_codes.get("llm_invalid_response", 0) + 1
            raise

    def info(self) -> dict[str, Any]:
        """Metadane do GET /system: bez klucza i bez wywołania płatnego API."""
        s = self.settings
        return {"protocol": s.protocol, "endpoint": s.base_url, "model": s.model,
                "key_file_present": s.protocol == "mock" or resolve_key_path(s).is_file(),
                "license": None, "location": None, "parameter_count": None}


def redact_msg(text: str, secrets: list[str]) -> str:
    for s in secrets:
        if s:
            text = text.replace(s, "***")
    return text


class MockLlm:
    """Atrapa HTTP (httpx.MockTransport) w formacie Anthropic. Skrypt zachowań do E14.

    `script`: kolejka kroków zużywana po jednym na żądanie; po wyczerpaniu działa `default`.
    Krok: ("ok", tekst) | ("status", kod) | ("timeout",) | ("connect",) | ("truncated", tekst) |
    ("garbage",) | ("empty",) | ("no_content",).
    Zapisuje żądania w `requests` (bez nagłówków autoryzacji) do asercji w testach.
    """

    def __init__(self, script: list[tuple[Any, ...]] | None = None, default: tuple[Any, ...] | None = None,
                 responder: Callable[[dict[str, Any]], str] | None = None) -> None:
        self.script: deque[tuple[Any, ...]] = deque(script or [])
        self.default = default or (("ok",) if responder else ("ok", "{}"))
        self.responder = responder
        self.requests: list[dict[str, Any]] = []

    def _body(self, text: str, stop: str = "end_turn") -> dict[str, Any]:
        return {"id": "mock", "model": "mock-model", "stop_reason": stop,
                "content": [{"type": "text", "text": text}],
                "usage": {"input_tokens": 10, "output_tokens": max(1, len(text) // 4)}}

    def _handle(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.requests.append(body)
        step = self.script.popleft() if self.script else self.default
        kind = step[0]
        if kind == "ok":
            text = step[1] if len(step) > 1 else (self.responder(body) if self.responder else "{}")
            return httpx.Response(200, json=self._body(text))
        if kind == "status":
            return httpx.Response(int(step[1]), json={"error": {"message": "mock"}})
        if kind == "timeout":
            raise httpx.ReadTimeout("mock timeout", request=request)
        if kind == "connect":
            raise httpx.ConnectError("mock connect", request=request)
        if kind == "truncated":
            return httpx.Response(200, json=self._body(step[1][: max(1, len(step[1]) // 2)], "max_tokens"))
        if kind == "garbage":
            return httpx.Response(200, content=b"<html>not json</html>")
        if kind == "empty":
            return httpx.Response(200, json=self._body(""))
        if kind == "no_content":
            return httpx.Response(200, json={"id": "mock"})
        raise ValueError(f"nieznany krok atrapy: {kind}")

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)
