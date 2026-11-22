"""Wywołania LLM przez HTTP (MiniMax, protokół Anthropic) z cache na dysku i równoległością ≤3.

Cache: cache/llm/<skrót(model, system, user)>.json = surowa odpowiedź + tokeny + czas (bez klucza i bez nagłówków).
Klucz czyta wyłącznie harness/llm.py z pliku (MINIMAX_KEY_FILE lub ~/kluczMiniMaxKacper).
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import lib
from common import HarnessError
from config import LlmSettings
from llm import LlmClient, extract_json

SETTINGS = LlmSettings(max_tokens=6000, timeout_s=180.0, retries=3)
TRANSIENT = ("llm_rate_limit", "llm_unavailable")
OUTER_TRIES = 6  # ponowienia zewnętrzne z narastającym odstępem (klucz współdzielony z innymi grupami: 429)
_lock = threading.Lock()
STATS = {"calls": 0, "cache_hits": 0, "failures": 0, "input_tokens": 0, "output_tokens": 0, "wall_s": 0.0}


def call(system: str, user: str, tag: str = "", repeat: int = 0) -> dict[str, Any]:
    """Zwraca {ok, data|error, raw, input_tokens, output_tokens, latency_s, model, cached}. `repeat` rozróżnia powtórzenia w cache."""
    h = hashlib.sha256(json.dumps([SETTINGS.model, system, user, repeat], ensure_ascii=False).encode()).hexdigest()[:24]
    p = lib.CACHE / "llm" / f"{h}.json"
    if p.is_file():
        with _lock:
            STATS["cache_hits"] += 1
        return json.loads(p.read_text()) | {"cached": True}
    cl = LlmClient(SETTINGS)
    t0 = time.monotonic()
    rec: dict[str, Any]
    try:
        for attempt in range(OUTER_TRIES):
            try:
                r = cl.complete(user, system=system)
                break
            except HarnessError as e:
                if e.code not in TRANSIENT or attempt == OUTER_TRIES - 1:
                    raise
                time.sleep(min(10 * (attempt + 1), 45))
        try:
            data: Any = extract_json(r.text)
            ok, err = True, None
        except HarnessError as e:
            data, ok, err = None, False, f"{e.code}"
        rec = {"ok": ok, "data": data, "error": err, "raw": r.text, "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
               "latency_s": r.latency_s, "model": r.model, "stop_reason": r.stop_reason, "attempts": r.attempts, "tag": tag}
    except HarnessError as e:
        rec = {"ok": False, "data": None, "error": e.code, "raw": None, "input_tokens": 0, "output_tokens": 0, "latency_s": time.monotonic() - t0,
               "model": None, "tag": tag}
    with _lock:
        STATS["calls"] += 1
        STATS["failures"] += 0 if rec["ok"] else 1
        STATS["input_tokens"] += rec["input_tokens"] or 0
        STATS["output_tokens"] += rec["output_tokens"] or 0
        STATS["wall_s"] += rec["latency_s"]
    if rec["error"] not in ("llm_authorization", *TRANSIENT):  # błędy przejściowe i autoryzacji nie trafiają do cache
        p.write_text(json.dumps(rec, ensure_ascii=False))
    return rec | {"cached": False}


def run_many(jobs: list[tuple[str, str, str]], workers: int = 3, repeat: int = 0) -> list[dict[str, Any]]:
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda j: call(j[0], j[1], j[2], repeat), jobs))
