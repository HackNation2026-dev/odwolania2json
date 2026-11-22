"""E16: determinizm i regresja: ten sam wsad dwa razy (rozdzielenie kodu od wariancji modelu).

Części:
 D01  kod regułowy: ten sam wsad 60 dok. na świeżych serwerach (w=1, w=4, ponowny start) — porównanie bajtów artefaktów;
 D02  kod na „nagranych” odpowiedziach LLM: atrapa zwraca deterministyczną odpowiedź zależną od treści; dwa przebiegi — porównanie;
 D03  kolejność kluczy i `null` względem referencji; stabilność versions.json;
 D04  ewaluator produkcyjny (PR #8/#9) vs miara liści uprzęży na tym samym wsadzie (opis różnic).
Uruchomienie: .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E16/e16.py
Wynik: atak/E16/wyniki.json. Wynik opisuje UPRZĄŻ i nie jest oficjalnym F1.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import *  # noqa: F401,F403
import lib  # noqa: F401

EXPN = "E16"
WORK = SANDBOX / EXPN
LOCK = "/tmp/uzp-cpu.lock"
ARTIFACTS = ("result.json", "evidence.json", "report.json", "diagnosis.json", "state.json")


def dev_set(n_each: int = 20):
    from data import load_items
    items = load_items("dev")
    out = []
    for cls in ("odwolanie", "pelnomocnictwo", "przelew"):
        out += [i for i in items if i.document_class == cls][:n_each]
    return out


def run_batch(name: str, items: list[Any], workers: int, extra: dict[str, Any] | None = None, llm_mock: MockServer | None = None) -> tuple[dict[str, dict[str, bytes]], dict[str, Any]]:
    """Zwraca {klucz dokumentu: {artefakt: bajty}} odczytane z dysku serwera + metadane. Czas mierzony pod flock."""
    cfg: dict[str, Any] = {"limits": {"max_workers": workers}} | (extra or {})
    with open(LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            with running(name, WORK / name, **cfg) as (srv, c):
                t0 = time.monotonic()
                r = c.http.post("/batches", files=[("files", (i.key.replace("/", "__") + ".pdf", i.source.read_bytes(), "application/pdf")) for i in items], timeout=300)
                j = r.json()
                fin = wait_batch(c, j["batch_id"], 900)
                wall = time.monotonic() - t0
                out: dict[str, dict[str, bytes]] = {}
                for d, it in zip(j["documents"], items, strict=True):
                    run = srv.work / j["batch_id"] / "documents" / d["document_id"] / "runs" / "r1"  # type: ignore[attr-defined]
                    arts = {a: (run / a).read_bytes() for a in (*ARTIFACTS, "versions.json", "t3/ai-response.json", "t3/candidates.json") if (run / a).exists()}
                    out[it.key] = arts
                return out, {"wall_s": round(wall, 2), "done": fin.get("done"), **srv.usage()}
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def compare(a: dict[str, dict[str, bytes]], b: dict[str, dict[str, bytes]], names: tuple[str, ...]) -> dict[str, Any]:
    diff: dict[str, list[str]] = {}
    for k in a:
        for n in names:
            if a[k].get(n) != b[k].get(n):
                diff.setdefault(n, []).append(k)
    return {"docs": len(a), "differences_by_artifact": {n: len(v) for n, v in diff.items()}, "examples": {n: v[:2] for n, v in diff.items()}}


def strip_volatile(raw: bytes | None) -> Any:
    """versions.json: usuwamy z porównania pola z konstrukcji środowiska (port atrapy, ścieżka robocza)."""
    if raw is None:
        return None
    t = json.loads(raw)
    t.get("config", {}).pop("work_dir", None)
    return t


def key_order(x: Any) -> list[str]:
    out: list[str] = []
    if isinstance(x, dict):
        for k, v in x.items():
            out.append(k)
            out += key_order(v)
    elif isinstance(x, list):
        for v in x[:1]:
            out += key_order(v)
    return out


def main() -> int:
    items = dev_set()
    out: dict[str, Any] = {"experiment": EXPN, "versions": versions(), "vectors": [],
                           "note": "Wynik opisuje uprząż; miary F1 poniżej nie są oficjalnym wynikiem (ewaluator produkcyjny po PR #8/#9 vs miara liści uprzęży)."}
    # ---------- D01: kod regułowy
    r1, m1 = run_batch("d01-a-w1", items, 1)
    r2, m2 = run_batch("d01-b-w1", items, 1)
    r4, m4 = run_batch("d01-c-w4", items, 4)
    cmp_ab = compare(r1, r2, ARTIFACTS)
    cmp_ac = compare(r1, r4, ARTIFACTS)
    vers_equal = sum(1 for k in r1 if strip_volatile(r1[k].get("versions.json")) == strip_volatile(r2[k].get("versions.json")))
    ident = not cmp_ab["differences_by_artifact"] and not cmp_ac["differences_by_artifact"]
    out["vectors"].append(vec("DT01", "determinizm", "ten sam wsad 60 dokumentów dwa razy (świeże serwery, w=1) i raz z w=4: bajty result/evidence/report/diagnosis/state", "zero różnic (kod regułowy jest deterministyczny)",
                              f"w=1 vs w=1: {cmp_ab['differences_by_artifact'] or 'zero różnic'}; w=1 vs w=4: {cmp_ac['differences_by_artifact'] or 'zero różnic'}; versions.json (bez work_dir) identyczne w {vers_equal}/{len(r1)}; czasy {m1['wall_s']}/{m2['wall_s']}/{m4['wall_s']} s",
                              "nie" if ident else "tak", fix="Utrzymać test powtarzalności bajtowej w CI (dwa przebiegi na stałych danych).", port_test="test_two_runs_same_batch_are_byte_identical_for_rules_pipeline",
                              data={"a_vs_b": cmp_ab, "a_vs_c": cmp_ac, "runs": [m1, m2, m4]}))
    # ---------- D03: kolejność kluczy i null względem referencji
    from data import reference_for
    order_ok, order_bad, null_diff, n_res = 0, [], 0, 0
    for it in items:
        res = r1[it.key].get("result.json")
        if res is None:
            continue
        n_res += 1
        got = key_order(json.loads(res))
        ref = reference_for(it)
        refk = key_order(ref)
        # kolejność względna wspólnych kluczy ma być zgodna z referencją
        it_ = iter(refk)
        is_sub = all(k in it_ for k in got)  # kolejność kluczy wyniku jest podciągiem kolejności referencji
        order_ok += 1 if is_sub else 0
        if not is_sub:
            order_bad.append(it.key)
        # liczba kluczy z null w wyniku vs referencji
        null_diff += abs(json.dumps(json.loads(res)).count("null") - json.dumps(ref).count("null"))
    out["vectors"].append(vec("DT02", "determinizm", "kolejność kluczy wyniku względem referencji organizatora i obecność `null`", "kolejność kluczy zgodna z szablonem, `null` jawne dla pustych pól",
                              f"kolejność kluczy wyniku jest podciągiem kolejności referencji (puste elementy list usunięte): {order_ok}/{n_res} dokumentów z wynikiem (reszta: ambiguous bez result.json); różnica liczby literałów null między wynikiem a referencją (suma bezwzględna): {null_diff} (wynik po `prune` usuwa puste elementy list, więc null-e w listach się różnią)",
                              "nie" if order_ok == n_res else "tak", fix="Serializować wynik z kolejnością klas szablonu (Pydantic z zachowaniem kolejności pól); test porównania kolejności z `example` OpenAPI.",
                              port_test="test_result_key_order_matches_template_and_nulls_explicit", data={"order_mismatch": order_bad[:5]}))
    # ---------- D02: nagrane odpowiedzi LLM
    def responder(req: MockReq) -> None:
        body = req.json()
        prompt = json.dumps(body)
        m = re.search(r"(\d[\d ]*,\d\d)", prompt.replace("\\n", " "))
        fields = [{"field": "/przelew_bankowy/kwota", "value": 1.0, "quote": m.group(1).strip() if m else "x", "page": 1}] if m else []
        req.anthropic_ok(json.dumps({"fields": fields}, ensure_ascii=False))

    przel = [i for i in items if i.document_class == "przelew"][:10]
    kf = make_key_file(WORK / "key", "CANARY-KEY-" + secrets.token_hex(8))
    runs = []
    for tag in ("a", "b"):
        with MockServer(responder) as mock:
            extra = {"extractor": "llm", "llm": {"protocol": "anthropic", "base_url": mock.url + "/v1/messages", "key_file": str(kf), "retries": 0}}
            rr, mm = run_batch(f"d02-{tag}", przel, 2, extra)
            runs.append((rr, mm, len(mock.log)))
    c2 = compare(runs[0][0], runs[1][0], (*ARTIFACTS, "t3/ai-response.json", "t3/candidates.json"))
    out["vectors"].append(vec("DT03", "determinizm", "kod na stałych odpowiedziach LLM (atrapa deterministyczna z treści): 10 przelewów dwa razy", "identyczne bajty artefaktów; różnice tylko z wariancji modelu (tu jej brak)",
                              f"różnice: {c2['differences_by_artifact'] or 'zero różnic'}; wywołań atrapy {runs[0][2]}/{runs[1][2]}", "nie" if not c2["differences_by_artifact"] else "tak",
                              fix="Zapisywać odpowiedź modelu (jest: ai-response.json) i testować kod na nagranych odpowiedziach osobno od wariancji modelu.", port_test="test_replay_recorded_llm_responses_is_byte_identical",
                              data={"compare": c2}))
    # ---------- D04: ewaluator produkcyjny vs miara liści
    per_class: dict[str, dict[str, int]] = {}
    per_leaf: dict[str, dict[str, int]] = {}
    for it in items:
        res = r1[it.key].get("result.json")
        if res is None:
            continue
        ec = eval_counts(json.loads(res), reference_for(it))
        for k in ("tp", "tn", "fp", "fn"):
            per_class.setdefault(it.document_class, {"tp": 0, "tn": 0, "fp": 0, "fn": 0})[k] += ec[k]
        for k in ("tp", "fp", "fn"):
            per_leaf.setdefault(it.document_class, {"tp": 0, "fp": 0, "fn": 0})[k] += ec["leaf"][k]

    def f1(c: dict[str, int]) -> float:
        d = 2 * c["tp"] + c["fp"] + c["fn"]
        return round(2 * c["tp"] / d, 4) if d else 0.0

    table = {k: {"evaluator": per_class[k] | {"f1": f1(per_class[k])}, "leaf": per_leaf[k] | {"f1": f1(per_leaf[k])}} for k in per_class}
    out["evaluator_vs_leaf"] = table
    out["vectors"].append(vec("DT04", "regresja-miary", "ewaluator produkcyjny (compare_document, domyślnie: błędna wartość = FP, próg 80%) vs miara liści uprzęży na 60 dokumentach regułowych", "wartości zbliżone; różnice wyjaśnione definicją",
                              "; ".join(f"{k}: ewaluator F1={v['evaluator']['f1']} (tp {v['evaluator']['tp']}, tn {v['evaluator']['tn']}, fp {v['evaluator']['fp']}, fn {v['evaluator']['fn']}), liście F1={v['leaf']['f1']}" for k, v in table.items()),
                              "nie dotyczy", fix="Do porównań wariantów używać ewaluatora produkcyjnego; miara liści zostaje tylko jako kontrola.", port_test="(brak: dotyczy pomiaru, nie produktu)", data=table))
    p = ATAK / EXPN / "wyniki.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
