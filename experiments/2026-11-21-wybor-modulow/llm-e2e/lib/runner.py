"""Runner grupy C: dokumenty × powtórzenia przez HTTP do backendu uprzęży, zapis JSONL (wznowienie po przerwaniu).

Użycie (z korzenia repozytorium):
    .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/llm-e2e/lib/runner.py <spec.json> [--dry]

Spec (JSON):
    {"name": "E10-text-p2", "experiment": "E10",
     "docs": {"set": "dev_sub" | "dev_all" | "keys:<plik>", "negatives": true, "variant_kinds": ["raster150"], "truncate_pages": null},
     "server": {pola HarnessConfig, np. "router": "llm1", "extractor": "llm1", "ocr": "none", "limits": {"max_workers": 4}, "llm": {...}},
     "env":    {"LLME2E_MODE": "text", ...},      # zmienne serwera (wtyczka llm_e2e_plugins)
     "reps": 5, "concurrency": 4, "timing_lock": false}

Zapis: `<katalog eksperymentu>/raw/<name>.jsonl` (jeden wiersz = jedno (powtórzenie, dokument)) i `<name>.meta.json`
(konfiguracja, wersje, szczytowy RSS, czas, metoda limitu pamięci). Klucza API nie zapisujemy: ścieżka pliku klucza
nie trafia do spec, a rekord LLM z uprzęży nie zawiera nagłówków.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LLM_E2E = HERE.parent
EXP = LLM_E2E.parent
HARNESS = EXP / "harness"
for p in (HARNESS, HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import data  # noqa: E402
from client import HarnessClient, ManagedServer  # noqa: E402
from common import WORK_ROOT, sha256_file, write_json_atomic  # noqa: E402
from config import load_config  # noqa: E402
from run_experiment import collect_versions, cpu_lock  # noqa: E402

SUBSET_SEED = 20261122
LOCK = threading.Lock()


# ---------- zbiory dokumentów ----------

def dev_cases() -> list[str]:
    return sorted({i.case_id for i in data.load_items("cases-dev")})


def make_subset(n_cases: int, seed: int = SUBSET_SEED) -> list[str]:
    """Powtarzalny podzbiór spraw rozwojowych: wszystkie sprawy z długim odwołaniem są w puli, ale losowanie jest jedno i zapisane."""
    items = data.load_items("cases-dev")
    cases = dev_cases()
    long_cases = sorted({i.case_id for i in items if i.document_class == "odwolanie" and _pages(i.source) >= 10})
    rng = random.Random(seed)
    n_long = max(1, round(n_cases * len(long_cases) / len(cases)))
    pick = set(rng.sample(long_cases, min(n_long, len(long_cases))))
    rest = [c for c in cases if c not in pick]
    pick |= set(rng.sample(rest, n_cases - len(pick)))
    return sorted(pick)


def _pages(path: Path) -> int:
    import pypdfium2 as pdfium

    d = pdfium.PdfDocument(str(path))
    try:
        return len(d)
    finally:
        d.close()


def select(spec_docs: dict[str, Any]) -> list[data.DocItem]:
    which = spec_docs.get("set", "dev_all")
    cases_file = LLM_E2E / "subset_dev.json"
    if which == "dev_all":
        items = data.load_items("cases-dev")
    elif which in ("dev_screen", "dev_long"):
        keep = set(json.loads((LLM_E2E / f"subset_{which[4:]}.json").read_text(encoding="utf-8"))["cases"])
        items = [i for i in data.load_items("cases-dev") if i.case_id in keep]
    elif which == "dev_sub":
        keep = set(json.loads(cases_file.read_text(encoding="utf-8"))["cases"])
        items = [i for i in data.load_items("cases-dev") if i.case_id in keep]
    elif which.startswith("cases:"):
        keep = set(json.loads(Path(which[6:]).read_text(encoding="utf-8"))["cases"])
        items = [i for i in data.load_items("cases-dev") if i.case_id in keep]
    elif which.startswith("zestaw:"):
        return _zestaw_items(which[7:], spec_docs)
    elif which == "control":
        if not spec_docs.get("confirm_control"):
            raise SystemExit("zbiór kontrolny: wymagane docs.confirm_control=true (jeden przebieg, na końcu)")
        items = data.load_items("control")
    else:
        raise SystemExit(f"nieznany zbiór {which}")
    if spec_docs.get("classes"):
        items = [i for i in items if i.document_class in spec_docs["classes"]]
    if spec_docs.get("negatives", False):
        items = items + data.load_items("negatives")
    return sorted(items, key=lambda i: i.key)


ZESTAW = EXP / "odczyt" / "zestaw"


@dataclass(frozen=True)
class ZItem(data.DocItem):
    """Dokument z zestawu skanów: wariant i ścieżka referencji niesione razem z elementem."""

    variant: str = ""
    ref: str = ""


def _zestaw_items(variants: str, spec_docs: dict[str, Any]) -> list[data.DocItem]:
    """Skany z zestawu grupy A (tylko sprawy rozwojowe; loader ma blokadę przecieku). `docs.cases` zawęża do podzbioru."""
    sys.path.insert(0, str(ZESTAW))
    from api import load_zestaw  # noqa: E402

    names = variants.split(",")
    keep = None
    if spec_docs.get("cases") in ("dev_sub", "dev_screen", "dev_long"):
        fn = "subset_dev.json" if spec_docs["cases"] == "dev_sub" else f"subset_{spec_docs['cases'][4:]}.json"
        keep = set(json.loads((LLM_E2E / fn).read_text(encoding="utf-8"))["cases"])
    out: list[data.DocItem] = []
    for it in load_zestaw(names):
        if keep is not None and it.case_id not in keep:
            continue
        out.append(ZItem(it.case_id, it.entry["input_name"], it.document_class, "dev", it.pdf, None, variant=it.variant, ref=str(it.ref)))
    return sorted(out, key=lambda i: (i.key, i.variant))  # type: ignore[attr-defined]


def prepare_files(items: list[data.DocItem], kinds: list[str], work: Path, seed: int) -> list[dict[str, Any]]:
    """Ścieżki PDF do wgrania: oryginały albo warianty (rasteryzacja itd.) z uprzęży; referencja dziedziczona."""
    if items and isinstance(items[0], ZItem):  # zestaw skanów: gotowe PDF-y, bez kopii roboczych
        return [{"item": i, "path": i.source, "variant": i.variant, "ref": i.ref} for i in items]  # type: ignore[attr-defined]
    originals = data.materialize(items)
    if not kinds:
        return [{"item": i, "path": originals[i.key], "variant": None} for i in items]
    recs = data.build_variants(items, kinds, work / "variants", seed=seed)
    by_key = {i.key: i for i in items}
    return [{"item": by_key[f"{r['case_id']}/{r['input_name']}"], "path": Path(r["output"]), "variant": r["kind"]} for r in recs]


# ---------- przebieg ----------

def _fetch(client: HarnessClient, doc_id: str, name: str) -> Any:
    code, body = client.artifact(doc_id, name)
    return body if code == 200 else None


def _artifact(client: HarnessClient, doc_id: str, name: str) -> Any:
    r = client.http.get(f"/documents/{doc_id}/artifact/{name}")
    return r.json() if r.status_code == 200 else None


def run_job(client: HarnessClient, entry: dict[str, Any], rep: int, wait_s: float) -> dict[str, Any]:
    item = entry["item"]
    t0 = time.monotonic()
    up = client.upload_paths([entry["path"]])
    doc_id = up["document_id"]
    st = client.wait_done(doc_id, timeout=wait_s, poll=0.25)
    wall = time.monotonic() - t0
    code, result = client.artifact(doc_id, "result")
    rec: dict[str, Any] = {
        "rep": rep, "key": item.key, "case_id": item.case_id, "input_name": item.input_name, "expected_class": item.document_class,
        "variant": entry["variant"], "ref": entry.get("ref"), "file": str(entry["path"].name), "outcome": st["outcome"], "class_id": st["class_id"],
        "codes": st["codes"], "errors": st["errors"], "result": result if code == 200 else None, "wall_s": round(wall, 3),
        "metrics": _fetch(client, doc_id, "metrics"), "router": _artifact(client, doc_id, "t1/router.json"),
        "candidates": _artifact(client, doc_id, "t3/candidates.json"), "report": _fetch(client, doc_id, "report"),
        "diagnosis_codes": (_fetch(client, doc_id, "diagnosis") or {}).get("codes"),
        "n_evidence": len(_fetch(client, doc_id, "evidence") or []),
    }
    return rec


def load_done(path: Path) -> set[tuple[int, str]]:
    done: set[tuple[int, str]] = set()
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["rep"], r["key"] + "|" + (r["variant"] or "")))
    return done


def run_spec(spec: dict[str, Any], *, dry: bool = False) -> Path:
    exp, name = spec["experiment"], spec["name"]
    out_dir = LLM_E2E / exp / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / f"{name}.jsonl"
    work = WORK_ROOT / "runs" / "llm-e2e" / name
    work.mkdir(parents=True, exist_ok=True)
    docs = spec.get("docs", {})
    items = select(docs)
    seed = int(spec.get("seed", SUBSET_SEED))
    entries = prepare_files(items, docs.get("variant_kinds") or [], work, seed)
    index = {sha256_file(e["path"]): str(e["path"]) for e in entries}
    index_path = work / "pdf-index.json"
    write_json_atomic(index_path, index)
    server_cfg = dict(spec.get("server", {}))
    conc = int(spec.get("concurrency", 4))
    server_cfg.setdefault("limits", {}).setdefault("max_workers", conc)
    server_cfg.setdefault("work_dir", str(work / "srv"))
    server_cfg.setdefault("seed", seed)
    server_cfg.setdefault("name", f"{exp}-{name}")
    cfg_path = work / "server-config.json"
    write_json_atomic(cfg_path, server_cfg)
    cfg = load_config(cfg_path, env={})
    env = {"HARNESS_PLUGINS": "llm_e2e_plugins", "PYTHONPATH": str(HERE), "LLME2E_PDF_INDEX": str(index_path),
           "LLME2E_FAILLOG": str(out_dir / f"{name}.fail"), **{k: str(v) for k, v in (spec.get("env") or {}).items()}}
    reps = int(spec.get("reps", 1))
    done = load_done(jsonl)
    jobs = [(r, e) for r in range(1, reps + 1) for e in entries if (r, e["item"].key + "|" + (e["variant"] or "")) not in done]
    print(f"[{name}] dokumentów {len(entries)}, powtórzeń {reps}, do wykonania {len(jobs)}, współbieżność {conc}", flush=True)
    if dry:
        return jsonl
    started = time.time()
    meta: dict[str, Any] = {"name": name, "experiment": exp, "spec": spec, "versions": collect_versions(), "seed": seed,
                            "documents": len(entries), "reps": reps, "concurrency": conc,
                            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started))}
    with cpu_lock(bool(spec.get("timing_lock", False))) as waited:
        meta["lock_wait_s"] = round(waited, 3)
        t_run = time.monotonic()
        with ManagedServer(cfg_path, env=env, log_path=work / "server.log") as srv:
            meta.update(server_start_s=round(srv.start_s or 0.0, 3), limit_method=srv.limit_method)
            probe = HarnessClient(srv.url, server=srv)
            meta["system"] = probe.system()
            probe.close()
            local = threading.local()

            def worker(job: tuple[int, dict[str, Any]]) -> dict[str, Any]:
                if not hasattr(local, "c"):
                    local.c = HarnessClient(srv.url, timeout=120.0, server=srv)
                rep, entry = job
                return run_job(local.c, entry, rep, float(spec.get("document_wait_s", 900)))

            n = 0
            with ThreadPoolExecutor(max_workers=conc) as ex, jsonl.open("a", encoding="utf-8") as f:
                futs = {ex.submit(worker, j): j for j in jobs}
                for fut in as_completed(futs):
                    try:
                        rec = fut.result()
                    except Exception as e:  # noqa: BLE001 — błąd klienta HTTP: zapisujemy jawnie, runner idzie dalej
                        rep, entry = futs[fut]
                        rec = {"rep": rep, "key": entry["item"].key, "case_id": entry["item"].case_id, "input_name": entry["item"].input_name,
                               "expected_class": entry["item"].document_class, "variant": entry["variant"], "outcome": "client_error",
                               "class_id": None, "codes": [type(e).__name__], "errors": [], "result": None, "wall_s": None}
                    with LOCK:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        f.flush()
                    n += 1
                    if n % 20 == 0 or n == len(jobs):
                        print(f"  [{name}] {n}/{len(jobs)} ({time.monotonic() - t_run:.0f}s)", flush=True)
            peak = srv.sample_rss()
        meta.update(peak_rss_mb=round((peak or 0) / 1024, 1), total_wall_s=round(time.monotonic() - t_run, 2),
                    finished_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    prev = out_dir / f"{name}.meta.json"
    if prev.is_file():  # wznowienie: zachowaj wcześniejsze segmenty czasu
        old = json.loads(prev.read_text(encoding="utf-8"))
        meta["segments"] = old.get("segments", [{k: old.get(k) for k in ("started_utc", "finished_utc", "total_wall_s", "peak_rss_mb")}]) + \
            [{k: meta.get(k) for k in ("started_utc", "finished_utc", "total_wall_s", "peak_rss_mb")}]
    write_json_atomic(prev, meta)
    return jsonl


def drop_transient_errors(jsonl: Path) -> int:
    """Wiersze z błędem przejściowym LLM (429, 5xx, timeout, błąd klienta) przenosimy do `<name>.errors.jsonl` (audyt) i zlecamy ponownie.
    Błędy trwałe (np. `ocr_unavailable`, `llm_invalid_response` po ponowieniu) zostają w wyniku: to część mierzonego zachowania."""
    if not jsonl.is_file():
        return 0
    keep, drop = [], []
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        transient = r.get("outcome") == "client_error" or (r.get("outcome") == "technical_error" and
                    any(c in ("llm_unavailable", "llm_rate_limit") for c in r.get("codes") or []))
        (drop if transient else keep).append(line)
    if drop:
        with jsonl.with_suffix(".errors.jsonl").open("a", encoding="utf-8") as f:
            f.write("\n".join(drop) + "\n")
        tmp = jsonl.with_suffix(".tmp")
        tmp.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
        tmp.replace(jsonl)
    return len(drop)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="+")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--retry-passes", type=int, default=3, help="ile razy ponowić wiersze z błędem przejściowym (429/5xx/timeout)")
    ns = ap.parse_args(argv)
    for sp in ns.specs:
        spec = json.loads(Path(sp).read_text(encoding="utf-8"))
        jsonl = run_spec(spec, dry=ns.dry)
        for k in range(ns.retry_passes):
            if ns.dry:
                break
            n = drop_transient_errors(jsonl)
            print(f"[{spec['name']}] przebieg ponowień {k + 1}: błędów przejściowych do ponowienia: {n}", flush=True)
            if not n:
                break
            time.sleep(30)
            run_spec(spec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
