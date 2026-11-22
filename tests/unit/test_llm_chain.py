"""Testy łańcucha dostawców LLM: przełączanie, ślad do raportu, wspólny budżet, kanarki."""

from __future__ import annotations

import pytest
from odwolania2json.errors import ProcessingError
from odwolania2json.extract.answer import LlmAnswer, parse_answer
from odwolania2json.extract.ports import LlmTrace, TracedLlm
from odwolania2json.llm.chain import PRIMARY_UNAUTHORIZED, LlmChain
from odwolania2json.llm.client import LlmBudget
from support.llm import API_KEY, FALLBACK_KEY, TIMEOUT, FakeLlmServer, Reply, answer

FOREIGN = answer("foreign")
TRANSFER = answer("bank_transfer")


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _fallback(replies: list[Reply]) -> FakeLlmServer:
    return FakeLlmServer(
        replies,
        protocol="openai",
        api_key=FALLBACK_KEY,
        host="zapas.example.test",
        model="model-zapasowy",
    )


def _chain(
    primary: FakeLlmServer,
    fallback: FakeLlmServer | None,
    *,
    clock: _Clock | None = None,
    budget: LlmBudget | None = None,
) -> LlmChain:
    return LlmChain(
        primary.client(budget=budget),
        fallback.client(budget=budget) if fallback is not None else None,
        cooldown_s=300.0,
        clock=clock or _Clock(),
    )


def _ask(chain: LlmChain) -> LlmAnswer:
    return chain.complete_json("system", "tekst", None, parse_answer)


def test_chain_is_a_traced_llm() -> None:
    chain = _chain(FakeLlmServer([FOREIGN]), None)

    assert isinstance(chain, TracedLlm)
    assert chain.has_fallback is False
    assert chain.take_trace() is None


def test_primary_answer_never_touches_fallback() -> None:
    primary, fallback = FakeLlmServer([TRANSFER]), _fallback([])
    chain = _chain(primary, fallback)

    assert _ask(chain).label == "bank_transfer"
    assert chain.has_fallback is True
    assert chain.take_trace() == LlmTrace("primary", "atrapa", None, ())
    assert chain.take_trace() is None
    assert fallback.requests == []


@pytest.mark.parametrize(
    ("failure", "calls", "reason"),
    [
        (429, 4, "llm_rate_limit"),
        (402, 1, "llm_payment_required"),
        (500, 4, "llm_unavailable"),
        (503, 4, "llm_unavailable"),
        (TIMEOUT, 4, "llm_unavailable"),
        (400, 1, "llm_request_rejected"),
    ],
)
def test_fallback_answers_after_primary_retries_are_exhausted(
    failure: Reply, calls: int, reason: str
) -> None:
    primary, fallback = FakeLlmServer([failure] * calls), _fallback([TRANSFER])
    chain = _chain(primary, fallback)

    assert _ask(chain).label == "bank_transfer"

    assert len(primary.requests) == calls
    assert len(fallback.requests) == 1
    assert chain.take_trace() == LlmTrace("fallback", "model-zapasowy", reason, ())
    assert fallback.headers[0]["authorization"] == f"Bearer {FALLBACK_KEY}"
    assert API_KEY not in str(fallback.headers[0])


@pytest.mark.parametrize("status", [401, 403])
def test_rejected_primary_key_switches_and_leaves_warning(status: int) -> None:
    primary, fallback = FakeLlmServer([status]), _fallback([TRANSFER, FOREIGN])
    chain = _chain(primary, fallback)

    assert _ask(chain).label == "bank_transfer"
    assert chain.take_trace() == LlmTrace(
        "fallback", "model-zapasowy", "llm_authorization", (PRIMARY_UNAUTHORIZED,)
    )
    # Zły klucz nie naprawi się w tym wsadzie: główny nie jest już pytany.
    assert _ask(chain).label == "foreign"
    assert len(primary.requests) == 1
    assert chain.take_trace() == LlmTrace(
        "fallback", "model-zapasowy", "llm_authorization", (PRIMARY_UNAUTHORIZED,)
    )


def test_payment_failure_disables_primary_for_the_batch() -> None:
    primary, fallback = FakeLlmServer([402]), _fallback([TRANSFER, FOREIGN])
    clock = _Clock()
    chain = _chain(primary, fallback, clock=clock)

    _ask(chain)
    clock.now = 10_000.0
    _ask(chain)

    assert len(primary.requests) == 1
    assert len(fallback.requests) == 2


def test_rate_limited_primary_rests_for_cooldown_then_is_asked_again() -> None:
    primary = FakeLlmServer([429, 429, 429, 429, TRANSFER])
    fallback = _fallback([FOREIGN, FOREIGN])
    clock = _Clock()
    chain = _chain(primary, fallback, clock=clock)

    assert _ask(chain).label == "foreign"
    clock.now = 299.0
    assert _ask(chain).label == "foreign"
    assert len(primary.requests) == 4
    assert chain.take_trace() == LlmTrace("fallback", "model-zapasowy", "llm_rate_limit", ())

    clock.now = 300.0
    assert _ask(chain).label == "bank_transfer"
    assert len(primary.requests) == 5
    assert chain.take_trace() == LlmTrace("primary", "atrapa", None, ())


def test_invalid_answer_is_retried_at_primary_before_fallback() -> None:
    primary = FakeLlmServer(["nie JSON", {"class": "wyrok"}, TRANSFER])
    fallback = _fallback([FOREIGN])
    chain = _chain(primary, fallback)

    assert _ask(chain).label == "foreign"

    assert len(primary.requests) == 2
    assert chain.take_trace() == LlmTrace("fallback", "model-zapasowy", "llm_invalid_response", ())
    # Błąd treści dotyczy jednego dokumentu: następny znów trafia do głównego.
    assert _ask(chain).label == "bank_transfer"
    assert len(fallback.requests) == 1


def test_fallback_answer_is_validated_and_semantically_retried_too() -> None:
    primary = FakeLlmServer([402])
    fallback = _fallback(['```json\n{"class": "nieznana"}\n```', TRANSFER])
    chain = _chain(primary, fallback)

    assert _ask(chain).label == "bank_transfer"
    assert len(fallback.requests) == 2
    assert fallback.requests[1]["max_tokens"] == 6000


def test_both_providers_failing_is_an_explicit_error_without_keys() -> None:
    primary, fallback = FakeLlmServer([429] * 4), _fallback([500] * 4)
    chain = _chain(primary, fallback)

    with pytest.raises(ProcessingError) as caught:
        _ask(chain)

    assert caught.value.code == "llm_unavailable"
    assert caught.value.message == (
        "obaj dostawcy LLM zawiedli (główny: llm_rate_limit, zapasowy: llm_unavailable)"
    )
    assert chain.take_trace() == LlmTrace(None, None, "llm_rate_limit", ())
    for secret in (API_KEY, FALLBACK_KEY):
        assert secret not in str(caught.value) + repr(caught.value)


def test_rejected_fallback_key_does_not_hide_transient_primary_code() -> None:
    primary, fallback = FakeLlmServer([429] * 4), _fallback([401])
    chain = _chain(primary, fallback)

    with pytest.raises(ProcessingError) as caught:
        _ask(chain)

    # Kod `llm_authorization` zatrzymałby wsad, a główny może wrócić po przerwie.
    assert caught.value.code == "llm_rate_limit"
    assert "zapasowy: llm_authorization" in caught.value.message


def test_both_keys_rejected_fails_fast_for_following_documents() -> None:
    primary, fallback = FakeLlmServer([401]), _fallback([403])
    chain = _chain(primary, fallback)

    for _ in range(3):
        with pytest.raises(ProcessingError) as caught:
            _ask(chain)
        assert caught.value.code == "llm_authorization"
        assert chain.take_trace() == LlmTrace(
            None, None, "llm_authorization", (PRIMARY_UNAUTHORIZED,)
        )

    assert (len(primary.requests), len(fallback.requests)) == (1, 1)


def test_without_fallback_behaviour_is_unchanged() -> None:
    primary = FakeLlmServer([429] * 4)
    chain = _chain(primary, None)

    with pytest.raises(ProcessingError) as caught:
        _ask(chain)

    assert caught.value.code == "llm_rate_limit"
    assert "HTTP 429" in caught.value.message
    assert chain.take_trace() == LlmTrace(None, None, None, ())


def test_errors_that_another_provider_cannot_fix_are_not_switched() -> None:
    primary, fallback = FakeLlmServer([TRANSFER]), _fallback([TRANSFER])
    chain = LlmChain(primary.client(max_input_tokens=1), fallback.client())

    with pytest.raises(ProcessingError) as caught:
        _ask(chain)

    assert caught.value.code == "llm_input_limit"
    assert chain.take_trace() is None
    assert fallback.requests == []


def test_call_budget_is_shared_by_both_providers() -> None:
    budget = LlmBudget(max_calls=5)
    primary, fallback = FakeLlmServer([429] * 4), _fallback([TRANSFER, TRANSFER])
    chain = _chain(primary, fallback, budget=budget)

    assert _ask(chain).label == "bank_transfer"
    assert budget.calls == 5
    with pytest.raises(ProcessingError) as caught:
        _ask(chain)

    assert caught.value.code == "llm_call_limit"
    assert len(fallback.requests) == 1
    assert (budget.input_tokens, budget.output_tokens) == (10, 5)


def test_self_check_passes_with_both_providers_healthy() -> None:
    primary, fallback = FakeLlmServer(["OK"]), _fallback(["OK"])

    assert _chain(primary, fallback).self_check() == []
    assert (len(primary.requests), len(fallback.requests)) == (1, 1)


def test_self_check_without_fallback_raises_primary_error() -> None:
    chain = _chain(FakeLlmServer([429]), None)

    with pytest.raises(ProcessingError) as caught:
        chain.self_check()

    assert caught.value.code == "llm_rate_limit"


def test_self_check_without_fallback_passes_silently() -> None:
    assert _chain(FakeLlmServer(["OK"]), None).self_check() == []


def test_self_check_with_dead_primary_warns_and_uses_fallback_directly() -> None:
    primary, fallback = FakeLlmServer([429]), _fallback(["OK", TRANSFER])
    chain = _chain(primary, fallback)

    assert chain.self_check() == [
        "dostawca główny LLM nie działa (llm_rate_limit); odpowiada zapasowy"
    ]
    assert _ask(chain).label == "bank_transfer"
    # Główny odpoczywa po nieudanej próbie: dokument nie czeka na jego ponowienia.
    assert len(primary.requests) == 1
    assert chain.take_trace() == LlmTrace("fallback", "model-zapasowy", "llm_rate_limit", ())


def test_self_check_with_rejected_primary_key_adds_named_warning() -> None:
    chain = _chain(FakeLlmServer([401]), _fallback(["OK"]))

    warnings = chain.self_check()

    assert warnings == [
        "dostawca główny LLM nie działa (llm_authorization); odpowiada zapasowy",
        "llm_primary_unauthorized: sprawdź klucz dostawcy głównego",
    ]


def test_self_check_with_dead_fallback_only_warns() -> None:
    chain = _chain(FakeLlmServer(["OK"]), _fallback([402]))

    assert chain.self_check() == ["dostawca zapasowy LLM nie działa (llm_payment_required)"]


def test_self_check_with_both_dead_raises_primary_code_without_keys() -> None:
    chain = _chain(FakeLlmServer([401]), _fallback([402]))

    with pytest.raises(ProcessingError) as caught:
        chain.self_check()

    assert caught.value.code == "llm_authorization"
    assert "dostawca zapasowy też zawiódł (llm_payment_required)" in caught.value.message
    for secret in (API_KEY, FALLBACK_KEY):
        assert secret not in str(caught.value)
