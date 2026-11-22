"""Fałszywy serwer LLM dla testów: prawdziwy `LlmClient` na `httpx.MockTransport`.

Testy przechodzą przez prawdziwą ścieżkę klienta (nagłówki, parsowanie, ponowienia),
ale bez sieci. Odpowiedzi podaje się jako kolejkę: słownik (obiekt JSON odpowiedzi
modelu), tekst (surowa treść), liczba (status HTTP błędu) albo `TIMEOUT`.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence

import httpx
from odwolania2json.llm.client import LlmBudget, LlmClient, LlmSettings

__all__ = [
    "API_KEY",
    "FALLBACK_KEY",
    "TIMEOUT",
    "FakeLlmServer",
    "answer",
    "field",
    "fields_from_reference",
]

API_KEY = "KANAREK-sekretny-klucz-0123456789"
FALLBACK_KEY = "KANAREK-zapasowy-klucz-9876543210"


class _Timeout:
    """Znacznik odpowiedzi: serwer nie odpowiada w czasie."""


TIMEOUT = _Timeout()

type Reply = dict[str, object] | str | int | _Timeout
type Responder = Callable[[str], Reply]


def field(pointer: str, value: object, quote: str = "cytat", page: int = 1) -> dict[str, object]:
    return {"field": pointer, "value": value, "quote": quote, "page": page}


def answer(label: str, *fields: dict[str, object]) -> dict[str, object]:
    return {"class": label, "fields": list(fields)}


class FakeLlmServer:
    """Kolejka odpowiedzi albo funkcja `tekst użytkownika → odpowiedź`."""

    def __init__(
        self,
        replies: Sequence[Reply] | Responder,
        *,
        protocol: str = "anthropic",
        api_key: str = API_KEY,
        host: str = "llm.example.test",
        model: str = "atrapa",
    ) -> None:
        self.protocol = protocol
        self.api_key = api_key
        self.host = host
        self.model = model
        self._queue: list[Reply] | None = None if callable(replies) else list(replies)
        self._responder: Responder | None = replies if callable(replies) else None
        self.requests: list[dict[str, object]] = []
        self.headers: list[dict[str, str]] = []

    @property
    def user_texts(self) -> list[str]:
        texts: list[str] = []
        for body in self.requests:
            messages = body["messages"]
            assert isinstance(messages, list)
            content = messages[-1]["content"]
            texts.append("".join(part.get("text", "") for part in content))
        return texts

    def _handle(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.requests.append(body)
        self.headers.append(dict(request.headers))
        if self._responder is not None:
            reply = self._responder(self.user_texts[-1])
        else:
            assert self._queue, "atrapa LLM: brak zaplanowanej odpowiedzi"
            reply = self._queue.pop(0)
        if isinstance(reply, _Timeout):
            raise httpx.ReadTimeout("atrapa: brak odpowiedzi", request=request)
        if isinstance(reply, int):
            # Treść błędu zawiera klucz: klient nie może jej nigdzie przepisać.
            return httpx.Response(reply, json={"error": f"odrzucono klucz {self.api_key}"})
        text = reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False)
        if self.protocol == "openai":
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                    "model": self.model,
                },
            )
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": text}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
                "model": self.model,
                "stop_reason": "end_turn",
            },
        )

    def client(self, *, budget: LlmBudget | None = None, **overrides: object) -> LlmClient:
        path = "/v1/chat/completions" if self.protocol == "openai" else "/v1/messages"
        options: dict[str, object] = {
            "protocol": self.protocol,
            "base_url": f"https://{self.host}{path}",
            "model": self.model,
            "api_key": self.api_key,
            "allowed_hosts": (self.host,),
        }
        options.update(overrides)
        settings = LlmSettings(**options)  # type: ignore[arg-type]  # słownik opcji testowych
        return LlmClient(
            settings,
            transport=httpx.MockTransport(self._handle),
            sleep=lambda _seconds: None,
            budget=budget,
        )


def fields_from_reference(reference: object, prefix: str = "") -> list[dict[str, object]]:
    """Pola odpowiedzi modelu odtwarzające referencję (ścieżka JSON Pointer → wartość)."""
    if isinstance(reference, dict):
        return [
            item
            for key, value in reference.items()
            for item in fields_from_reference(value, f"{prefix}/{key}")
        ]
    if isinstance(reference, list):
        return [
            item
            for index, value in enumerate(reference)
            for item in fields_from_reference(value, f"{prefix}/{index}")
        ]
    return [field(prefix, reference)]
