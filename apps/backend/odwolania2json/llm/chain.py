"""Łańcuch dostawców LLM: główny, a po jego awarii zapasowy.

Dlaczego: limit konta głównego dostawcy bywa wyczerpany (HTTP 429), a bez odpowiedzi
modelu cały wsad kończy się pustymi wynikami. Zasady przełączania:
- przełączamy dopiero po wyczerpaniu ponowień głównego: 429, 5xx, sieć i limit czasu,
  402 (brak środków), odrzucone żądanie, a także 401/403; odrzucony klucz głównego
  zostawia w raporcie ostrzeżenie `llm_primary_unauthorized`, żeby nie zniknął po cichu;
- odpowiedź poza schematem najpierw dostaje ponowienie u tego samego dostawcy
  (robi je `LlmClient.complete_json`), dopiero potem pytamy zapasowego;
- dostawca zapasowy przechodzi tę samą walidację odpowiedzi i to samo ponowienie;
- po błędzie trwałym (klucz, środki) dostawca jest wyłączony do końca wsadu, po
  przejściowym (429, sieć) na czas przerwy: kolejne dokumenty nie czekają na ponowienia;
- budżet wywołań i tokenów jest wspólny (`LlmBudget` przekazany obu klientom).

Zgodność dostawcy zapasowego z wymogami konkursu (UE/EOG, licencja) nie jest tu
zakładana ani sprawdzana: to decyzja konfiguracji (ADR-007).
"""

from __future__ import annotations

import time
from collections.abc import Callable

from odwolania2json.errors import ProcessingError
from odwolania2json.extract.ports import LlmTrace

from .client import Image, LlmBudget, LlmClient

__all__ = ["DEFAULT_COOLDOWN_S", "PRIMARY_UNAUTHORIZED", "LlmChain"]

DEFAULT_COOLDOWN_S = 300.0
PRIMARY_UNAUTHORIZED = "llm_primary_unauthorized"

# Błędy, po których warto zapytać drugiego dostawcę.
_SWITCH_CODES = frozenset(
    {
        "llm_rate_limit",
        "llm_unavailable",
        "llm_payment_required",
        "llm_authorization",
        "llm_request_rejected",
        "llm_invalid_response",
    }
)
# Błędy konta: ponawianie w tym wsadzie nie ma sensu.
_PERMANENT_CODES = frozenset({"llm_authorization", "llm_payment_required"})
# Błędy przejściowe usługi: dostawca odpoczywa przez `cooldown_s`.
_TRANSIENT_CODES = frozenset({"llm_rate_limit", "llm_unavailable"})


class _Provider:
    """Klient z nazwą roli i stanem wyłączenia w bieżącym wsadzie."""

    def __init__(self, name: str, client: LlmClient) -> None:
        self.name = name
        self.client = client
        self._down_code: str | None = None
        self._down_until: float | None = None

    def down_code(self, now: float) -> str | None:
        """Kod błędu, przez który dostawca jest teraz wyłączony, albo `None`."""
        if self._down_code is None:
            return None
        if self._down_until is not None and now >= self._down_until:
            self._down_code = self._down_until = None
            return None
        return self._down_code

    def mark(self, code: str, now: float, cooldown_s: float) -> None:
        if code in _PERMANENT_CODES:
            self._down_code, self._down_until = code, None
        elif code in _TRANSIENT_CODES:
            self._down_code, self._down_until = code, now + cooldown_s


class LlmChain:
    """Dostawca główny i opcjonalny zapasowy za jednym interfejsem `complete_json`."""

    def __init__(
        self,
        primary: LlmClient,
        fallback: LlmClient | None = None,
        *,
        cooldown_s: float = DEFAULT_COOLDOWN_S,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._primary = _Provider("primary", primary)
        self._fallback = _Provider("fallback", fallback) if fallback is not None else None
        self._cooldown_s = cooldown_s
        self._clock = clock
        self._trace: LlmTrace | None = None

    @property
    def has_fallback(self) -> bool:
        return self._fallback is not None

    @property
    def cooldown_s(self) -> float:
        return self._cooldown_s

    @property
    def budget(self) -> LlmBudget:
        """Budżet wsadu dostawcy głównego (wspólny, jeśli zapasowy dostał ten sam)."""
        return self._primary.client.budget

    def take_trace(self) -> LlmTrace | None:
        """Ślad ostatniego wywołania (kto odpowiedział i dlaczego); odczyt go zeruje."""
        trace, self._trace = self._trace, None
        return trace

    def _attempt[T](
        self, provider: _Provider, call: Callable[[LlmClient], T]
    ) -> T | ProcessingError:
        """Wynik wywołania albo błąd, po którym wolno przełączyć dostawcę."""
        code = provider.down_code(self._clock())
        if code is not None:
            return ProcessingError(code, f"dostawca pominięty po wcześniejszym błędzie ({code})")
        try:
            return call(provider.client)
        except ProcessingError as error:
            if error.code not in _SWITCH_CODES:
                raise
            provider.mark(error.code, self._clock(), self._cooldown_s)
            return error

    def _run[T](self, call: Callable[[LlmClient], T]) -> T:
        self._trace = None
        first = self._attempt(self._primary, call)
        if not isinstance(first, ProcessingError):
            self._trace = LlmTrace("primary", self._primary.client.settings.model, None, ())
            return first
        warnings = (PRIMARY_UNAUTHORIZED,) if first.code == "llm_authorization" else ()
        if self._fallback is None:
            self._trace = LlmTrace(None, None, None, ())
            raise first
        second = self._attempt(self._fallback, call)
        if isinstance(second, ProcessingError):
            self._trace = LlmTrace(None, None, first.code, warnings)
            # Kod błędu konta zapasowego nie może zatrzymać wsadu, gdy główny wróci.
            code = first.code if second.code == "llm_authorization" else second.code
            raise ProcessingError(
                code,
                f"obaj dostawcy LLM zawiedli (główny: {first.code}, zapasowy: {second.code})",
            )
        self._trace = LlmTrace(
            "fallback", self._fallback.client.settings.model, first.code, warnings
        )
        return second

    def complete_json[T](
        self,
        system: str,
        user: str,
        images: list[Image] | None,
        validate: Callable[[dict[str, object]], T],
    ) -> T:
        """Odpowiedź sprawdzona przez `validate` od pierwszego działającego dostawcy."""
        return self._run(lambda client: client.complete_json(system, user, images, validate))

    def self_check(self) -> list[str]:
        """Próba połączenia z obydwoma dostawcami; zwraca ostrzeżenia dla użytkownika.

        Wsad może ruszyć, gdy działa co najmniej jeden dostawca. Niedziałający
        główny przy działającym zapasowym to ostrzeżenie, nie błąd: po to jest zapas.
        """
        warnings: list[str] = []
        results: list[ProcessingError | None] = []
        for provider in (self._primary, self._fallback):
            if provider is None:
                continue
            try:
                provider.client.self_check()
                results.append(None)
            except ProcessingError as error:
                provider.mark(error.code, self._clock(), self._cooldown_s)
                results.append(error)
        primary_error = results[0]
        if self._fallback is None:
            if primary_error is not None:
                raise primary_error
            return warnings
        fallback_error = results[1]
        if primary_error is not None and fallback_error is not None:
            raise ProcessingError(
                primary_error.code,
                f"{primary_error.message}; dostawca zapasowy też zawiódł ({fallback_error.code})",
            )
        if primary_error is not None:
            warnings.append(
                f"dostawca główny LLM nie działa ({primary_error.code}); odpowiada zapasowy"
            )
            if primary_error.code == "llm_authorization":
                warnings.append(f"{PRIMARY_UNAUTHORIZED}: sprawdź klucz dostawcy głównego")
        if fallback_error is not None:
            warnings.append(f"dostawca zapasowy LLM nie działa ({fallback_error.code})")
        return warnings
