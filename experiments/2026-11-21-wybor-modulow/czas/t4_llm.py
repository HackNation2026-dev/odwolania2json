"""T4: opóźnienie LLM (MiniMax przez HTTP), wywołanie jak w wariancie bazowym grupy C (E10 tekst, prompt p2, jedno wywołanie na dokument).

Polecenie: ../../../.venv-exp/bin/python t4_llm.py [--calls 15]   → wyniki/T4.json (+ T4.calls.jsonl)

Wywołanie = `SingleCall.run` z `llm-e2e/lib/llm_e2e_plugins.py` (ten sam prompt p2, ta sama walidacja i to samo jedno ponowienie przy odpowiedzi poza
schematem), klient `LlmClient` uprzęży z ustawieniami specyfikacji `e10-text-p2` (model MiniMax-M3.1-Flash-Preview, temperatura 0, retries 4, timeout 150 s).
Warianty: odwołanie 2-stronicowe i 11-stronicowe (tekst PDF z warstwy tekstu, bez OCR). 15 wywołań na wariant = 3 różne dokumenty rozwojowe × 5 powtórzeń
(różne dokumenty, bo identyczne wejście mogłoby trafiać w pamięć podręczną dostawcy i zaniżać opóźnienie). Wywołania SEKWENCYJNE, kolejność losowana w blokach
(blok = każdy dokument obu wariantów raz), żeby dryf pory dnia i obciążenia dostawcy nie przypadał na jeden wariant. Klucza nie czytamy ani nie zapisujemy:
czyta go klient uprzęży z pliku. Zapis: opóźnienie wywołania (całość z ponowieniami HTTP) i ostatniej próby, tokeny wejścia/wyjścia, liczba prób HTTP/schematu,
status; pora dnia; warunki sieci: czas DNS, TCP i TLS do hosta przed i po serii (bez zapisu adresów IP).
Osobno od CPU: wywołanie czeka na sieć; zapisujemy load avg przed/po i czy w trakcie były obce procesy.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
for sub in ("harness", "llm-e2e/lib"):
    sys.path.insert(0, str(HERE.parent / sub))
import tlib  # noqa: E402

SPEC = HERE.parent / "llm-e2e" / "specs" / "e10-text-p2.json"


def pick_docs() -> dict[str, list]:
    import data
    import pypdfium2 as pdfium
    items = [i for i in data.load_items("cases-dev") if i.document_class == "odwolanie"]
    by: dict[int, list] = {2: [], 11: []}
    for i in sorted(items, key=lambda i: i.key):
        d = pdfium.PdfDocument(str(i.source))
        n = len(d)
        d.close()
        if n in by and len(by[n]) < 3:
            by[n].append(i)
    return {f"odwolanie_{n}str": v for n, v in by.items()}


def net_probe(host: str) -> dict:
    out = {}
    try:
        t = time.perf_counter()
        ai = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        out["dns_ms"] = round((time.perf_counter() - t) * 1000, 1)
        t = time.perf_counter()
        s = socket.create_connection(ai[0][4][:2], timeout=10)
        out["tcp_ms"] = round((time.perf_counter() - t) * 1000, 1)
        t = time.perf_counter()
        ctx = ssl.create_default_context()
        ss = ctx.wrap_socket(s, server_hostname=host)
        out["tls_ms"] = round((time.perf_counter() - t) * 1000, 1)
        ss.close()
    except OSError as e:
        out["error"] = type(e).__name__
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", type=int, default=15)
    ap.add_argument("--max-wait", type=float, default=3600)
    ap.add_argument("--no-gate", action="store_true", help="nie czekaj na ciszę CPU (opóźnienie LLM jest sieciowe; odnotowane w wyniku)")
    ns = ap.parse_args()
    os.environ.setdefault("LLME2E_MODE", "text")
    os.environ.setdefault("LLME2E_PROMPT", "p2")
    import llm_e2e_plugins as pl
    from config import LlmSettings
    from llm import LlmClient
    from reading import NoOcr, PdfiumReader as Rd, read_document
    spec = json.loads(SPEC.read_text())
    st = LlmSettings(**{k: v for k, v in spec["server"]["llm"].items()})
    llm = LlmClient(st)
    call = pl.SingleCall(llm)
    docs = pick_docs()
    readings = {}
    for var, items in docs.items():
        for i in items:
            reading, _, _ = read_document(i.source.read_bytes(), reader=Rd(), ocr=NoOcr(), ocr_policy="never", ocr_dpi=200, max_pages=60)
            readings[(var, i.key)] = reading
    reps = ns.calls // 3
    units = [(var, i.key) for var, items in docs.items() for i in items]
    plan = tlib.block_shuffled(units, reps)
    gate = tlib.wait_quiet(ns.max_wait if not ns.no_gate else 0, strict=True, label="T4 start")
    host = urllib.parse.urlparse(st.base_url).hostname or "api.minimax.io"
    net0 = net_probe(host)
    t_start = time.strftime("%Y-%m-%d %H:%M:%S %z")
    rows = []
    with (HERE / "wyniki" / "T4.calls.jsonl").open("w") as fh, tlib.Monitor() as mon:
        for n, (rep, (var, key)) in enumerate(plan):
            reading = readings[(var, key)]
            t0 = time.monotonic()
            err = None
            rec = {}
            try:
                data, rec = call.run(reading)
            except Exception as e:  # noqa: BLE001
                err = getattr(e, "code", type(e).__name__)
            wall = time.monotonic() - t0
            atts = rec.get("attempts", []) if rec else []
            good = [a for a in atts if "latency_s" in a]
            row = {"n": n, "rep": rep, "variant": var, "doc": key, "hour": time.strftime("%H:%M:%S"), "wall_s": round(wall, 3), "error": err,
                   "attempts_schema": len(atts), "schema_first_ok": rec.get("schema_first_ok") if rec else None,
                   "last_attempt_latency_s": good[-1]["latency_s"] if good else None, "all_attempt_latencies_s": [a["latency_s"] for a in good],
                   "input_tokens": sum(a.get("input_tokens") or 0 for a in good), "output_tokens": sum(a.get("output_tokens") or 0 for a in good),
                   "last_input_tokens": good[-1].get("input_tokens") if good else None, "last_output_tokens": good[-1].get("output_tokens") if good else None,
                   "http_attempts": [a.get("http_attempts") for a in good], "model": good[-1].get("model") if good else None,
                   "stop_reason": good[-1].get("stop_reason") if good else None, "doc_pages": rec.get("doc_pages") if rec else None}
            rows.append(row)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            print(n, var, row["wall_s"], row["error"] or "ok", flush=True)
    net1 = net_probe(host)
    summ = {}
    for var in docs:
        rs = [r for r in rows if r["variant"] == var]
        ok = [r for r in rs if not r["error"]]
        summ[var] = {"calls": len(rs), "errors": len(rs) - len(ok), "error_codes": sorted({r["error"] for r in rs if r["error"]}),
                     "wall_s_incl_retries": tlib.stats([r["wall_s"] for r in ok]), "last_attempt_latency_s": tlib.stats([r["last_attempt_latency_s"] for r in ok if r["last_attempt_latency_s"]]),
                     "input_tokens_last_attempt": tlib.stats([r["last_input_tokens"] for r in ok if r["last_input_tokens"]]),
                     "output_tokens_last_attempt": tlib.stats([r["last_output_tokens"] for r in ok if r["last_output_tokens"]]),
                     "tokens_out_per_s_last": tlib.stats([r["last_output_tokens"] / r["last_attempt_latency_s"] for r in ok if r["last_output_tokens"] and r["last_attempt_latency_s"]]),
                     "calls_with_schema_retry": sum(1 for r in rs if r["attempts_schema"] > 1), "calls_with_http_retry": sum(1 for r in rs if any((h or 1) > 1 for h in r["http_attempts"])),
                     "docs": sorted({r["doc"] for r in rs})}
    tlib.dump(HERE / "wyniki" / "T4.json", {"experiment": "T4", "environment": tlib.environment(), "gate": gate, "monitor": mon.record(), "started": t_start,
              "timezone": time.strftime("%Z %z"), "host": host, "net_before": net0, "net_after": net1, "model": st.model, "settings": {"temperature": st.temperature, "max_tokens": st.max_tokens,
              "retries": st.retries, "timeout_s": st.timeout_s}, "prompt": call.pvariant, "mode": call.mode, "summary": summ,
              "note": "inne grupy mogły równolegle korzystać z tego samego konta/limitu API; zob. monitor.foreign_during"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
