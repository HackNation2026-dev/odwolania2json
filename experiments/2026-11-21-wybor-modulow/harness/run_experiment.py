"""Wspólne CLI eksperymentów E##: konfiguracja wariantu (JSON) → pomiar przez HTTP → `wyniki/E##/<wariant>.json` + README.

Użycie:
    python run_experiment.py examples/E00-smoke-pdfium.json [--out-root DIR] [--no-lock]
    python run_experiment.py --list-runners

Plik konfiguracyjny wariantu (wszystkie pola poza `experiment` i `variant` mają wartości domyślne):
    {"experiment": "E01", "variant": "pdfium", "description": "co mierzymy i dlaczego",
     "runner": "e2e",                       # albo "moj_modul:moja_funkcja" (patrz niżej)
     "dataset": "cases-dev",                # dev | cases-dev | control | negatives | template | all
     "confirm_control": false,              # wymagane true dla control/all (kontrolny tylko raz, na końcu)
     "limit": 10, "seed": 20261122,         # losowy, ale powtarzalny podzbiór
     "variant_kinds": [],                   # np. ["raster150","rot90"] → dokumenty wariantowe zamiast oryginałów
     "timing": true,                        # pomiar czasu pod flock /tmp/uzp-cpu.lock
     "server": {"ocr": "none", "extractor": "rules", ...},   # pola HarnessConfig (config.py)
     "env": {"HARNESS_PLUGINS": "moje_wtyczki"}}              # dodatkowe zmienne środowiskowe serwera

Własny runner: funkcja `fn(spec: dict, ctx: RunContext) -> dict` zwraca słownik z kluczami wyniku
(`documents`, `aggregates`, …); harness dopisze wersje, konfigurację, czasy, RSS, ziarno. Rejestracja:
`register_runner("nazwa", fn)` w module z `HARNESS_PLUGINS`, albo wskazanie `modul:funkcja` w `runner`.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib
import json
import platform
import random
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import common
from client import HarnessClient, ManagedServer
from common import RESULTS_ROOT, WORK_ROOT, read_json, write_json_atomic
from config import HarnessConfig, load_config

LOCK_PATH = "/tmp/uzp-cpu.lock"
CONTROL_SETS = {"control", "all"}


@dataclass
class RunContext:
    out_dir: Path
    work_dir: Path
    cfg: HarnessConfig
    cfg_path: Path
    timing: bool
    extra: dict[str, Any] = field(default_factory=dict)


@contextmanager
def cpu_lock(enabled: bool, path: str = LOCK_PATH):
    """flock na /tmp/uzp-cpu.lock (zgodny z poleceniem `flock`): serializuje pomiary czasu między zadaniami."""
    if not enabled:
        yield 0.0
        return
    t0 = time.monotonic()
    with open(path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield time.monotonic() - t0
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


RUNNERS: dict[str, Callable[[dict[str, Any], RunContext], dict[str, Any]]] = {}


def register_runner(name: str, fn: Callable[[dict[str, Any], RunContext], dict[str, Any]]) -> None:
    RUNNERS[name] = fn


def resolve_runner(name: str) -> Callable[[dict[str, Any], RunContext], dict[str, Any]]:
    if name in RUNNERS:
        return RUNNERS[name]
    if ":" in name:
        mod, fn = name.split(":", 1)
        return getattr(importlib.import_module(mod), fn)
    raise SystemExit(f"nieznany runner: {name}; dostępne: {sorted(RUNNERS)}")


# ---------- dobór dokumentów ----------

def select_documents(spec: dict[str, Any], work: Path) -> list[dict[str, Any]]:
    import data

    which = spec.get("dataset", "cases-dev")
    if which in CONTROL_SETS and not spec.get("confirm_control"):
        raise SystemExit("zbiór kontrolny tylko raz, na końcu: ustaw w konfiguracji \"confirm_control\": true świadomie")
    items = data.load_items(which)
    items = sorted(items, key=lambda i: i.key)
    seed = int(spec.get("seed", 20261122))
    limit = spec.get("limit")
    if limit:
        items = sorted(random.Random(seed).sample(items, min(int(limit), len(items))), key=lambda i: i.key)
    originals = data.materialize(items)
    kinds = spec.get("variant_kinds") or []
    docs: list[dict[str, Any]] = []
    if not kinds:
        docs = [{"item": i, "path": originals[i.key], "variant": None} for i in items]
    else:
        recs = data.build_variants(items, kinds, work / "variants", seed=seed)
        by_key = {i.key: i for i in items}
        for r in recs:
            docs.append({"item": by_key[f"{r['case_id']}/{r['input_name']}"], "path": Path(r["output"]), "variant": r["kind"],
                         "variant_record": {k: r[k] for k in ("kind", "description", "dpi", "seed", "output_sha256")}})
    return docs


# ---------- miary liści ----------

def _leaves(x: Any, path: str = "") -> list[tuple[str, str]]:
    """Niepuste liście jako (ścieżka bez indeksów list, wartość JSON); kolejność elementów list nie ma znaczenia."""
    if isinstance(x, dict):
        return [p for k, v in x.items() for p in _leaves(v, f"{path}.{k}")]
    if isinstance(x, list):
        return [p for v in x for p in _leaves(v, path)]
    return [] if x is None else [(path, json.dumps(x, ensure_ascii=False, sort_keys=True))]


def leaf_counts(pred: Any, ref: Any) -> dict[str, int]:
    """TP/FP/FN na niepustych liściach (multizbiór). Ewaluator produkcyjny nie liczy `tp` dla pól (trafione pole to `tn`),
    więc jego F1 pól wynosi 0; ta miara służy do porównywania wariantów i NIE jest oficjalnym wynikiem."""
    p, r = Counter(_leaves(pred)), Counter(_leaves(ref))
    tp = sum((p & r).values())
    return {"tp": tp, "fp": sum(p.values()) - tp, "fn": sum(r.values()) - tp}


def leaf_f1(c: dict[str, int]) -> float:
    d = 2 * c["tp"] + c["fp"] + c["fn"]
    return round(2 * c["tp"] / d, 4) if d else 0.0


# ---------- runner e2e ----------

def _predicted_class(state: dict[str, Any], expected: str) -> tuple[str, bool]:
    """(klasa przewidziana, czy podjęto decyzję). Brak decyzji nigdy nie liczy się jako trafienie."""
    from stages import ORGANIZER_CLASS

    if state["outcome"] in ("complete", "partial"):
        return ORGANIZER_CLASS[state["class_id"]], True
    if state["outcome"] == "foreign":
        return "obcy", True
    return ("odwolanie" if expected == "obcy" else "obcy"), False


def run_e2e(spec: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    import data
    from odwolania2json.evaluator import evaluate_document, summarize
    from odwolania2json.loader import CaseReference

    docs = select_documents(spec, ctx.work_dir)
    records: list[dict[str, Any]] = []
    metrics = []
    with cpu_lock(ctx.timing and not ctx.extra.get("no_lock")) as waited:
        ctx.extra["lock_wait_s"] = round(waited, 3)
        t_run = time.monotonic()
        with ManagedServer(ctx.cfg_path, env=spec.get("env"), log_path=ctx.work_dir / "server.log") as srv:
            ctx.extra.update(server_start_s=round(srv.start_s or 0.0, 3), limit_method=srv.limit_method)
            with HarnessClient(srv.url, server=srv) as client:
                ctx.extra["system"] = client.system()
                for d in docs:
                    item = d["item"]
                    run = client.run_document(d["path"], timeout=float(spec.get("document_wait_s", 900)))
                    st = run["state"]
                    result = run["artifacts"]["result"]["body"] if run["artifacts"]["result"]["http"] == 200 else None
                    rec: dict[str, Any] = {
                        "key": item.key, "expected_class": item.document_class, "variant": d["variant"],
                        "variant_record": d.get("variant_record"), "outcome": st["outcome"], "class_id": st["class_id"],
                        "codes": st["codes"], "errors": st["errors"], "timing": run["timing"],
                        "peak_rss_mb_so_far": run.get("peak_rss_mb"), "result": result,
                        "evidence_count": len(run["artifacts"]["evidence"]["body"] or []),
                        "pipeline_metrics": run["artifacts"]["metrics"]["body"]}
                    pred, decided = _predicted_class(st, item.document_class)
                    rec["predicted_class"], rec["decided"] = pred, decided
                    if item.document_class in ("odwolanie", "pelnomocnictwo", "przelew", "obcy"):
                        ref = data.reference_for(item)
                        case = CaseReference(case_id=item.case_id, input_name=item.input_name,
                                             document_class=item.document_class, reference_name=item.reference_name)  # type: ignore[arg-type]
                        m = evaluate_document(case, result or {}, ref, pred)  # type: ignore[arg-type]
                        if not decided:
                            m = m.model_copy(update={"classification": "fn"})
                        metrics.append(m)
                        rec["leaf_counts"] = leaf_counts(result or {}, ref)
                    records.append(rec)
                    print(f"  {item.key:55s} {st['outcome']:16s} {run['timing']['wall_s']:7.2f}s", flush=True)
            peak = srv.sample_rss()
        ctx.extra.update(peak_rss_mb=round((peak or 0) / 1024, 1), total_wall_s=round(time.monotonic() - t_run, 3))
    aggregates: dict[str, Any] = {
        "documents": len(records), "outcomes": dict(Counter(r["outcome"] for r in records)),
        "error_codes": dict(Counter(c for r in records for c in r["codes"] if r["outcome"] == "technical_error")),
        "classification_confusion": dict(Counter(f"{r['expected_class']}->{r['predicted_class'] if r['decided'] else 'brak_decyzji'}" for r in records)),
        "wall_s_total_per_doc": round(sum(r["timing"]["wall_s"] for r in records), 3),
        "wall_s_mean_per_doc": round(sum(r["timing"]["wall_s"] for r in records) / max(1, len(records)), 4),
        "approx_f1": summarize(metrics) if metrics else None,
        "leaf_f1": _leaf_totals(records),
        "note": "Ewaluator produkcyjny (approx_f1) nie zlicza tp dla pól, więc jego F1 pól to 0; do porównań używaj leaf_f1. Żadna z miar nie jest oficjalnym wynikiem."}
    return {"documents": records, "aggregates": aggregates}


def _leaf_totals(records: list[dict[str, Any]]) -> dict[str, Any]:
    tot = {"tp": 0, "fp": 0, "fn": 0}
    per_class: dict[str, dict[str, int]] = {}
    for r in records:
        c = r.get("leaf_counts")
        if c is None:
            continue
        pc = per_class.setdefault(r["expected_class"], {"tp": 0, "fp": 0, "fn": 0})
        for k in tot:
            tot[k] += c[k]
            pc[k] += c[k]
    return {"total": tot | {"f1": leaf_f1(tot)}, "per_class": {k: v | {"f1": leaf_f1(v)} for k, v in per_class.items()}}


register_runner("e2e", run_e2e)


# ---------- wersje i zapis ----------

def collect_versions() -> dict[str, Any]:
    import importlib.metadata as md

    v: dict[str, Any] = {"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine()}
    for pkg in ("fastapi", "uvicorn", "httpx", "pydantic", "pypdfium2", "rapidocr", "onnxruntime", "pillow", "numpy"):
        try:
            v[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            v[pkg] = None
    try:
        v["git_commit"] = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=common.REPO).stdout.strip()
    except OSError:
        v["git_commit"] = None
    return v


def write_readme(out_dir: Path, experiment: str) -> None:
    """README E## generowane z istniejących plików wariantów; opis bierze z pola `description` konfiguracji."""
    rows, desc = [], ""
    for p in sorted(out_dir.glob("*.json")):
        d = read_json(p)
        a = d.get("aggregates", {})
        desc = desc or d.get("description", "")
        f1 = ((a.get("leaf_f1") or {}).get("total") or {}).get("f1")
        rows.append(f"| `{p.name}` | {d.get('dataset')} | {a.get('documents')} | {a.get('outcomes')} | "
                    f"{a.get('wall_s_mean_per_doc')} | {d.get('peak_rss_mb')} | {'' if f1 is None else round(f1, 4)} | {d.get('limit_method')} |")
    text = f"""# {experiment}: wyniki surowe i sposób pomiaru

{desc or '(opis w polu `description` konfiguracji wariantu)'}

## Jak to działa i dlaczego

Każdy plik `<wariant>.json` to jeden przebieg `python harness/run_experiment.py <konfiguracja>`: harness startuje backend
eksperymentalny jako podproces pod limitem pamięci 14 GB, wgrywa dokumenty przez HTTP (`POST /batches`), czeka na stan
`done` i czyta wynik, dowody, raport i diagnozę. Mierzymy po stronie klienta czas ścienny, a po stronie procesu serwera
szczytowy RSS (VmHWM). Pomiar czasu biegnie pod `flock {LOCK_PATH}`, żeby równoległe zadania nie zniekształcały wyniku.
Dlaczego HTTP: tak będzie używał backendu klient i GUI, więc mierzymy też narzut przyjęcia, kolejki i zapisu.
Plik wariantu zawiera konfigurację, wersje pakietów, ziarno, metodę limitu pamięci i surowe rekordy dokumentów;
liczby w tabeli poniżej są tylko streszczeniem (F1 liści: miara pomocnicza do porównań wariantów, nie wynik oficjalny; surowe liczniki są w `aggregates.leaf_f1`).

| plik | zbiór | dok. | wyniki | śr. s/dok. | szczyt RSS MB | F1 liści (suma) | limit pamięci |
|---|---|---|---|---|---|---|---|
""" + "\n".join(rows) + "\n"
    common.write_bytes_atomic(out_dir / "README.md", text.encode("utf-8"))


def run_spec(spec: dict[str, Any], *, out_root: Path = RESULTS_ROOT, no_lock: bool = False) -> Path:
    exp, variant = spec["experiment"], spec["variant"]
    if not (len(exp) >= 3 and exp[0] == "E" and exp[1:].isdigit()):
        raise SystemExit(f"nieprawidłowy identyfikator eksperymentu: {exp}")
    work = WORK_ROOT / "runs" / exp / variant
    work.mkdir(parents=True, exist_ok=True)
    server_cfg = dict(spec.get("server", {}))
    server_cfg.setdefault("work_dir", str(work / "srv"))
    server_cfg.setdefault("seed", spec.get("seed", 20261122))
    server_cfg.setdefault("name", f"{exp}-{variant}")
    cfg_path = work / "server-config.json"
    write_json_atomic(cfg_path, server_cfg)  # bez sekretów: tylko ścieżka pliku klucza, jeśli ją podano
    cfg = load_config(cfg_path, env={})
    out_dir = out_root / exp
    ctx = RunContext(out_dir=out_dir, work_dir=work, cfg=cfg, cfg_path=cfg_path, timing=bool(spec.get("timing", True)),
                     extra={"no_lock": no_lock})
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body = resolve_runner(spec.get("runner", "e2e"))(spec, ctx)
    public_llm = {k: v for k, v in cfg.llm.__dict__.items() if k != "key_file"}
    record = {"experiment": exp, "variant": variant, "description": spec.get("description", ""), "dataset": spec.get("dataset"),
              "seed": spec.get("seed", 20261122), "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "spec": spec, "harness_config": cfg.to_dict() | {"llm": public_llm}, "versions": collect_versions(),
              "timing_locked": ctx.timing and not no_lock, **{k: v for k, v in ctx.extra.items() if k != "no_lock"}, **body}
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(out_dir / f"{variant}.json", record)
    write_readme(out_dir, exp)
    return out_dir / f"{variant}.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", nargs="?", help="plik JSON wariantu eksperymentu")
    ap.add_argument("--out-root", default=str(RESULTS_ROOT))
    ap.add_argument("--no-lock", action="store_true", help="pomiń flock (wyniki czasu nie są wiarygodne)")
    ap.add_argument("--list-runners", action="store_true")
    ns = ap.parse_args(argv)
    from stages import load_plugins
    load_plugins()
    if ns.list_runners:
        print("\n".join(sorted(RUNNERS)))
        return 0
    if not ns.config:
        ap.error("podaj plik konfiguracji wariantu")
    out = run_spec(read_json(Path(ns.config)), out_root=Path(ns.out_root), no_lock=ns.no_lock)
    print(f"zapisano {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
