"""Fałszywy serwer LLM dla testów: prawdziwy `LlmClient` na `httpx.MockTransport`.

Testy przechodzą przez prawdziwą ścieżkę klienta (nagłówki, parsowanie, ponowienia),
ale bez sieci. Odpowiedzi podaje się jako kolejkę: słownik (obiekt JSON odpowiedzi
modelu), tekst (surowa treść) albo liczba (status HTTP błędu).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence

import httpx
from odwolania2json.llm.client import LlmClient, LlmSettings

__all__ = ["API_KEY", "FakeLlmServer", "answer", "field", "fields_from_reference"]

API_KEY = "KANAREK-sekretny-klucz-0123456789"

type Reply = dict[str, object] | str | int
type Responder = Callable[[str], Reply]


def field(pointer: str, value: object, quote: str = "cytat", page: int = 1) -> dict[str, object]:
    return {"field": pointer, "value": value, "quote": quote, "page": page}


def answer(label: str, *fields: dict[str, object]) -> dict[str, object]:
    return {"class": label, "fields": list(fields)}


class FakeLlmServer:
    """Kolejka odpowiedzi albo funkcja `tekst użytkownika → odpowiedź`."""

    def __init__(self, replies: Sequence[Reply] | Responder) -> None:
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
            content = messages[0]["content"]
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
        if isinstance(reply, int):
            # Treść błędu zawiera klucz: klient nie może jej nigdzie przepisać.
            return httpx.Response(reply, json={"error": f"odrzucono klucz {API_KEY}"})
        text = reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False)
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": text}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
                "model": "atrapa",
                "stop_reason": "end_turn",
            },
        )

    def client(self, **overrides: object) -> LlmClient:
        options: dict[str, object] = {
            "protocol": "anthropic",
            "base_url": "https://llm.example.test/v1/messages",
            "model": "atrapa",
            "api_key": API_KEY,
            "allowed_hosts": ("llm.example.test",),
        }
        options.update(overrides)
        settings = LlmSettings(**options)  # type: ignore[arg-type]  # słownik opcji testowych
        return LlmClient(
            settings, transport=httpx.MockTransport(self._handle), sleep=lambda _seconds: None
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
