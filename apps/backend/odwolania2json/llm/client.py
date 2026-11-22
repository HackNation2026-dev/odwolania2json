"""Odporny klient LLM: protokół Anthropic (np. MiniMax) i OpenAI-zgodny.

Zasady (Z04, atak E14):
- adres musi być `https` i wskazywać host z listy zezwoleń z konfiguracji, żeby
  klucz nie wyciekł do przypadkowego serwera; przekierowań nie śledzimy;
- klucz idzie w dokładnie jednym nagłówku właściwym dla protokołu i nigdy nie
  trafia do komunikatów błędów (komunikaty składamy sami, bez treści odpowiedzi);
- błędy sieci, 429 i 5xx są ponawiane z wykładniczym opóźnieniem i `Retry-After`
  (z górnym limitem); 401/403 nie są ponawiane;
- odpowiedź poza schematem dostaje jedno ponowienie z krótszym limitem wyjścia;
  naprawa JSON ogranicza się do zdjęcia znaczników ```;
- limit wywołań na wsad oraz limity tokenów wejścia i wyjścia są twarde; budżet
  wsadu (`LlmBudget`) może być wspólny dla kilku klientów (dostawca główny i zapasowy).
"""

from __future__ import annotations

import base64
import email.utils
import json
import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from odwolania2json.errors import ProcessingError

__all__ = [
    "CHARS_PER_TOKEN",
    "IMAGE_TOKENS",
    "Image",
    "LlmBudget",
    "LlmClient",
    "LlmReply",
    "LlmSettings",
    "estimate_tokens",
    "parse_json_object",
    "validate_base_url",
]

LlmProtocol = Literal["anthropic", "openai"]

# Szacunek rozmiaru wejścia bez tokenizera dostawcy: celowo ostrożny (polski tekst
# ma zwykle 3–4 znaki na token), bo limit ma chronić budżet, a nie go wyliczać.
CHARS_PER_TOKEN = 3
IMAGE_TOKENS = 2500
_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_RETRY_BASE_DELAY_S = 1.0
_PROBE_OUTPUT_TOKENS = 16
_FENCE = "```"
_RETRY_NOTE = (
    "\n\nPoprzednia odpowiedź nie była poprawnym obiektem JSON ze schematu. "
    "Odpowiedz krótko: wyłącznie jeden obiekt JSON, bez komentarzy i bez znaczników."
)


@dataclass(frozen=True)
class Image:
    """Obraz strony wysyłany do modelu."""

    media_type: str
    data: bytes = field(repr=False)


@dataclass(frozen=True)
class LlmSettings:
    """Ustawienia klienta; klucz nie pojawia się w `repr`."""

    protocol: LlmProtocol
    base_url: str
    model: str
    api_key: str = field(repr=False)
    allowed_hosts: tuple[str, ...]
    max_output_tokens: int = 12000
    retry_output_tokens: int = 6000
    max_input_tokens: int = 60000
    timeout_s: float = 150.0
    max_retries: int = 3
    max_retry_delay_s: float = 60.0
    max_calls: int = 1000
    temperature: float = 0.0
    retry_effort: str | None = None
    allow_http_localhost: bool = False
    # Nagłówki dodatkowe z konfiguracji (mogą być sekretne, stąd brak w `repr`).
    user_agent: str | None = None
    extra_headers: tuple[tuple[str, str], ...] = field(default=(), repr=False)


@dataclass
class LlmBudget:
    """Budżet jednego wsadu: liczniki wywołań i tokenów, wspólne dla klientów.

    Dostawca zapasowy nie może podwoić kosztu wsadu, więc limit wywołań i tokenów
    liczymy łącznie dla wszystkich klientów, które dostały ten sam budżet.
    """

    max_calls: int
    max_total_tokens: int | None = None
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def check(self) -> None:
        """Zgłasza `llm_call_limit`, gdy kolejne wywołanie przekroczyłoby budżet."""
        if self.calls >= self.max_calls:
            raise ProcessingError(
                "llm_call_limit", f"wyczerpano limit wywołań LLM na wsad ({self.max_calls})"
            )
        used = self.input_tokens + self.output_tokens
        if self.max_total_tokens is not None and used >= self.max_total_tokens:
            raise ProcessingError(
                "llm_call_limit", f"wyczerpano limit tokenów LLM na wsad ({self.max_total_tokens})"
            )


@dataclass(frozen=True)
class LlmReply:
    """Odpowiedź modelu z licznikami zużycia."""

    text: str
    input_tokens: int | None
    output_tokens: int | None
    model: str | None
    stop_reason: str | None
    attempts: int


class _Lenient(BaseModel):
    # Dostawcy dokładają własne pola (np. bloki rozumowania); nadmiar ignorujemy.
    model_config = ConfigDict(extra="ignore")


class _AnthropicBlock(_Lenient):
    type: str
    text: str | None = None


class _AnthropicUsage(_Lenient):
    input_tokens: int | None = None
    output_tokens: int | None = None


class _AnthropicBody(_Lenient):
    content: list[_AnthropicBlock]
    usage: _AnthropicUsage | None = None
    model: str | None = None
    stop_reason: str | None = None


class _OpenAiMessage(_Lenient):
    content: str | None = None


class _OpenAiChoice(_Lenient):
    message: _OpenAiMessage
    finish_reason: str | None = None


class _OpenAiUsage(_Lenient):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class _OpenAiBody(_Lenient):
    choices: list[_OpenAiChoice]
    usage: _OpenAiUsage | None = None
    model: str | None = None


def validate_base_url(
    base_url: str, allowed_hosts: tuple[str, ...], *, allow_http_localhost: bool = False
) -> str:
    """Zwraca adres po sprawdzeniu schematu i hosta; inaczej `invalid_configuration`.

    Dlaczego lista zezwoleń: błędny lub podstawiony `LLM_BASE_URL` wysłałby klucz
    i treść dokumentów do obcego serwera (E14, C02).
    """
    try:
        parts = urlsplit(base_url)
        host = (parts.hostname or "").lower()
    except ValueError:
        raise ProcessingError("invalid_configuration", "niepoprawny adres LLM") from None
    if parts.username is not None or parts.password is not None:
        raise ProcessingError(
            "invalid_configuration", "adres LLM nie może zawierać danych logowania"
        )
    if not host:
        raise ProcessingError("invalid_configuration", "adres LLM nie ma hosta")
    local_http = allow_http_localhost and parts.scheme == "http" and host in _LOCAL_HOSTS
    if parts.scheme != "https" and not local_http:
        raise ProcessingError("invalid_configuration", "adres LLM musi używać https")
    if not local_http and host not in {allowed.lower() for allowed in allowed_hosts}:
        raise ProcessingError(
            "invalid_configuration", f"host LLM spoza listy zezwoleń (LLM_ALLOWED_HOSTS): {host}"
        )
    return base_url


def estimate_tokens(texts: list[str], images: int) -> int:
    """Ostrożny szacunek tokenów wejścia: znaki / 3 plus stały koszt obrazu."""
    characters = sum(len(text) for text in texts)
    return math.ceil(characters / CHARS_PER_TOKEN) + images * IMAGE_TOKENS


def parse_json_object(text: str) -> dict[str, object]:
    """Obiekt JSON z odpowiedzi modelu; jedyna naprawa to zdjęcie znaczników ```.

    Nie wycinamy „pierwszego nawiasu” ani nie domykamy uciętego JSON-a: zgadywanie
    struktury byłoby zmyślaniem danych. Błąd to `llm_invalid_response`.
    """
    candidate = text.strip()
    if candidate.startswith(_FENCE):
        first_break = candidate.find("\n")
        candidate = candidate[first_break + 1 :] if first_break >= 0 else candidate[len(_FENCE) :]
        candidate = candidate.rstrip()
        if candidate.endswith(_FENCE):
            candidate = candidate[: -len(_FENCE)]
    try:
        parsed: object = json.loads(candidate)
    except ValueError:
        raise ProcessingError(
            "llm_invalid_response", "odpowiedź modelu nie jest poprawnym JSON-em"
        ) from None
    if not isinstance(parsed, dict):
        raise ProcessingError("llm_invalid_response", "JSON odpowiedzi modelu nie jest obiektem")
    return parsed


def _retry_after_seconds(raw: str | None, now: datetime) -> float | None:
    """`Retry-After` jako sekundy: liczba albo data HTTP; śmieci to brak podpowiedzi."""
    if raw is None:
        return None
    value = raw.strip()
    try:
        seconds = float(value)
    except ValueError:
        try:
            moment = email.utils.parsedate_to_datetime(value)
        except ValueError:
            return None
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        seconds = (moment - now).total_seconds()
    if not math.isfinite(seconds):
        return None
    return max(0.0, seconds)


class LlmClient:
    """Klient jednego wsadu: liczy wywołania i tokeny, pilnuje limitów."""

    def __init__(
        self,
        settings: LlmSettings,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        budget: LlmBudget | None = None,
    ) -> None:
        if settings.protocol not in ("anthropic", "openai"):
            raise ProcessingError("invalid_configuration", "nieznany protokół LLM")
        if not settings.api_key.strip():
            raise ProcessingError("llm_authorization", "brak klucza API LLM")
        if not settings.model.strip():
            raise ProcessingError("invalid_configuration", "brak nazwy modelu LLM")
        self._url = self._endpoint(settings)
        self._extra_headers = self._checked_headers(settings)
        self._budget = budget if budget is not None else LlmBudget(settings.max_calls)
        self._settings = settings
        self._transport = transport
        self._sleep = sleep
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    @property
    def settings(self) -> LlmSettings:
        return self._settings

    @staticmethod
    def _endpoint(settings: LlmSettings) -> str:
        url = validate_base_url(
            settings.base_url,
            settings.allowed_hosts,
            allow_http_localhost=settings.allow_http_localhost,
        )
        if settings.protocol == "openai" and not url.rstrip("/").endswith("/chat/completions"):
            return url.rstrip("/") + "/chat/completions"
        return url

    @property
    def budget(self) -> LlmBudget:
        return self._budget

    @staticmethod
    def _checked_headers(settings: LlmSettings) -> dict[str, str]:
        """Nagłówki dodatkowe z konfiguracji; znak końca linii to próba wstrzyknięcia."""
        pairs = list(settings.extra_headers)
        if settings.user_agent is not None:
            pairs.append(("user-agent", settings.user_agent))
        headers: dict[str, str] = {}
        for name, value in pairs:
            token = name.lower()
            if not token or not token.isascii() or any(char in token for char in " \t:\r\n"):
                raise ProcessingError("invalid_configuration", "niepoprawna nazwa nagłówka LLM")
            if "\r" in value or "\n" in value:
                raise ProcessingError(
                    "invalid_configuration", f"niepoprawna wartość nagłówka LLM: {token}"
                )
            headers[token] = value
        return headers

    # --- budowa żądania ---

    def _headers(self) -> dict[str, str]:
        key = self._settings.api_key.strip()
        # Nagłówki protokołu nadpisują dodatkowe: konfiguracja nie podmieni klucza.
        if self._settings.protocol == "anthropic":
            return {
                **self._extra_headers,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": key,
            }
        return {
            **self._extra_headers,
            "content-type": "application/json",
            "authorization": f"Bearer {key}",
        }

    def _body(
        self,
        system: str,
        user: str,
        images: list[Image],
        max_output_tokens: int,
        effort: str | None,
    ) -> dict[str, object]:
        settings = self._settings
        encoded = [(image.media_type, base64.b64encode(image.data).decode()) for image in images]
        if settings.protocol == "anthropic":
            content: list[dict[str, object]] = [
                {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}}
                for media, data in encoded
            ]
            content.append({"type": "text", "text": user})
            body: dict[str, object] = {
                "model": settings.model,
                "max_tokens": max_output_tokens,
                "temperature": settings.temperature,
                "system": system,
                "messages": [{"role": "user", "content": content}],
            }
            if effort:
                body["output_config"] = {"effort": effort}
            return body
        parts: list[dict[str, object]] = [{"type": "text", "text": user}]
        parts.extend(
            {"type": "image_url", "image_url": {"url": f"data:{media};base64,{data}"}}
            for media, data in encoded
        )
        return {
            "model": settings.model,
            "max_tokens": max_output_tokens,
            "temperature": settings.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": parts},
            ],
        }

    # --- odpowiedź ---

    def _parse(self, response: httpx.Response, attempts: int) -> LlmReply:
        try:
            payload: object = response.json()
        except ValueError:
            raise ProcessingError(
                "llm_invalid_response", "ciało odpowiedzi LLM nie jest JSON-em"
            ) from None
        try:
            if self._settings.protocol == "anthropic":
                anthropic = _AnthropicBody.model_validate(payload)
                text = "".join(b.text or "" for b in anthropic.content if b.type == "text")
                usage = anthropic.usage or _AnthropicUsage()
                reply = LlmReply(
                    text=text,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    model=anthropic.model,
                    stop_reason=anthropic.stop_reason,
                    attempts=attempts,
                )
            else:
                openai = _OpenAiBody.model_validate(payload)
                if not openai.choices:
                    raise ProcessingError("llm_invalid_response", "odpowiedź LLM bez wyboru")
                choice = openai.choices[0]
                tokens = openai.usage or _OpenAiUsage()
                reply = LlmReply(
                    text=choice.message.content or "",
                    input_tokens=tokens.prompt_tokens,
                    output_tokens=tokens.completion_tokens,
                    model=openai.model,
                    stop_reason=choice.finish_reason,
                    attempts=attempts,
                )
        except ValidationError:
            raise ProcessingError(
                "llm_invalid_response", "odpowiedź LLM ma nieoczekiwaną strukturę"
            ) from None
        if not reply.text.strip():
            raise ProcessingError("llm_invalid_response", "pusta odpowiedź modelu")
        return reply

    def _classify(self, response: httpx.Response) -> ProcessingError | None:
        """Błąd dla statusu HTTP albo `None` dla 2xx. Treści odpowiedzi nie cytujemy."""
        status = response.status_code
        if status in (401, 403):
            return ProcessingError(
                "llm_authorization", f"LLM odrzucił klucz API (HTTP {status}); sprawdź klucz"
            )
        if status == 402:
            return ProcessingError(
                "llm_payment_required", "LLM odmówił z powodu braku środków na koncie (HTTP 402)"
            )
        if status == 429:
            hint = _retry_after_seconds(response.headers.get("retry-after"), datetime.now(UTC))
            return ProcessingError(
                "llm_rate_limit",
                "LLM zgłosił limit zapytań lub wyczerpany limit konta (HTTP 429)",
                retry_after_s=hint,
            )
        if status >= 500:
            return ProcessingError("llm_unavailable", f"błąd serwera LLM (HTTP {status})")
        if not 200 <= status < 300:
            return ProcessingError("llm_request_rejected", f"LLM odrzucił żądanie (HTTP {status})")
        return None

    def _delay(self, attempt: int, error: ProcessingError) -> float:
        limit = self._settings.max_retry_delay_s
        backoff = _RETRY_BASE_DELAY_S * 2.0 ** (attempt - 1)
        return min(limit, max(backoff, error.retry_after_s or 0.0))

    # --- wywołania ---

    def _send(self, body: dict[str, object], *, retries: int) -> LlmReply:
        settings = self._settings
        attempt = 0
        with httpx.Client(
            transport=self._transport, timeout=settings.timeout_s, follow_redirects=False
        ) as http:
            while True:
                self._budget.check()
                attempt += 1
                self.calls += 1
                self._budget.calls += 1
                error: ProcessingError | None
                try:
                    response = http.post(self._url, headers=self._headers(), json=body)
                except httpx.TimeoutException:
                    error = ProcessingError("llm_unavailable", "przekroczono limit czasu LLM")
                except httpx.HTTPError as failure:
                    # Tylko nazwa klasy: tekst wyjątku mógłby zawierać adres z danymi.
                    error = ProcessingError(
                        "llm_unavailable", f"błąd sieci LLM ({type(failure).__name__})"
                    )
                else:
                    error = self._classify(response)
                    if error is None:
                        reply = self._parse(response, attempt)
                        self.input_tokens += reply.input_tokens or 0
                        self.output_tokens += reply.output_tokens or 0
                        self._budget.input_tokens += reply.input_tokens or 0
                        self._budget.output_tokens += reply.output_tokens or 0
                        return reply
                retryable = error.code in ("llm_unavailable", "llm_rate_limit")
                if not retryable or attempt > retries:
                    raise error
                self._sleep(self._delay(attempt, error))

    def complete(
        self,
        system: str,
        user: str,
        images: list[Image] | None = None,
        *,
        max_output_tokens: int | None = None,
        effort: str | None = None,
    ) -> LlmReply:
        """Jedno zapytanie z ponowieniami transportu; błąd to `ProcessingError`."""
        settings = self._settings
        pictures = images or []
        estimate = estimate_tokens([system, user], len(pictures))
        if estimate > settings.max_input_tokens:
            raise ProcessingError(
                "llm_input_limit",
                f"wejście LLM ok. {estimate} tokenów przekracza limit {settings.max_input_tokens}",
            )
        limit = min(max_output_tokens or settings.max_output_tokens, settings.max_output_tokens)
        body = self._body(system, user, pictures, limit, effort)
        return self._send(body, retries=settings.max_retries)

    def complete_json[T](
        self,
        system: str,
        user: str,
        images: list[Image] | None,
        validate: Callable[[dict[str, object]], T],
    ) -> T:
        """Odpowiedź sprawdzona przez `validate`; jedno ponowienie poza schematem.

        `validate` zgłasza `ProcessingError("llm_invalid_response")`, gdy obiekt nie
        spełnia schematu. Drugie niepowodzenie kończy dokument jawnym błędem.
        """
        settings = self._settings
        try:
            return validate(parse_json_object(self.complete(system, user, images).text))
        except ProcessingError as error:
            if error.code != "llm_invalid_response":
                raise
        retry_limit = min(settings.retry_output_tokens, settings.max_output_tokens)
        reply = self.complete(
            system,
            user + _RETRY_NOTE,
            images,
            max_output_tokens=retry_limit,
            effort=settings.retry_effort,
        )
        return validate(parse_json_object(reply.text))

    def self_check(self) -> None:
        """Jedno krótkie wywołanie próbne przed wsadem, bez ponowień.

        Zły klucz albo wyczerpany limit oznaczałyby pusty wynik całego wsadu, więc
        sprawdzamy to raz, zanim zaczniemy czytać dokumenty. Treść odpowiedzi jest
        nieistotna: liczy się to, że serwer przyjął klucz i żądanie.
        """
        body = self._body("Test połączenia.", "Odpowiedz: OK", [], _PROBE_OUTPUT_TOKENS, None)
        try:
            self._send(body, retries=0)
        except ProcessingError as error:
            if error.code != "llm_invalid_response":
                raise
