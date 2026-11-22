"""E15: wsad i współbieżność: 60 dokumentów × współbieżność 1/2/4, uszkodzone pliki w środku wsadu, `kill -9`, wyścigi, izolacja dokumentów, kolejka.

Uruchomienie: .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E15/e15.py [--only batch,corrupt,kill,races,isolation,queue]
Pomiary czasu pod `flock /tmp/uzp-cpu.lock`. Wynik: atak/E15/wyniki.json. Wynik opisuje UPRZĄŻ, nie produkt.
Dane: tylko zbiór rozwojowy (20 odwołań + 20 pełnomocnictw + 20 przelewów); ekstraktor regułowy, bez OCR i bez LLM.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import *  # noqa: F401,F403
import lib  # noqa: F401

EXPN = "E15"
WORK = SANDBOX / EXPN
LOCK = "/tmp/uzp-cpu.lock"


@contextlib.contextmanager
def cpu_lock():
    with open(LOCK, "w") as f:
        t0 = time.monotonic()
        fcntl.flock(f, fcntl.LOCK_EX)
        yield time.monotonic() - t0
        fcntl.flock(f, fcntl.LOCK_UN)


def dev_set(n_each: int = 20) -> list[tuple[str, str, bytes]]:
    from data import load_items
    items = load_items("dev")
    out: list[tuple[str, str, bytes]] = []
    for cls in ("odwolanie", "pelnomocnictwo", "przelew"):
        sel = [i for i in items if i.document_class == cls][:n_each]
        out += [(i.key.replace("/", "__"), cls, i.source.read_bytes()) for i in sel]
    return out


def json_health(root: Path) -> dict[str, Any]:
    """Wszystkie *.json pod root muszą się parsować; liczymy pliki tymczasowe i `.part`."""
    bad, n, tmp = [], 0, []
    for p in root.rglob("*"):
        if p.is_file():
            if p.suffix == ".tmp" or p.name.endswith(".part"):
                tmp.append(str(p.relative_to(root)))
            elif p.suffix == ".json":
                n += 1
                try:
                    json.loads(p.read_text(encoding="utf-8"))
                except ValueError:
                    bad.append(str(p.relative_to(root)))
    return {"json_files": n, "unparsable": bad, "tmp_or_part_files": tmp}


def result_digest(c: HarnessClient, doc: dict[str, Any]) -> str | None:
    if doc.get("outcome") not in ("complete", "partial", "foreign"):
        return None
    r = c.http.get(f"/documents/{doc['document_id']}/result")
    return hashlib.sha256(r.content).hexdigest()[:16]


def submit_batch(c: HarnessClient, docs: list[tuple[str, str, bytes]]) -> dict[str, Any]:
    r = c.http.post("/batches", files=[("files", (n + ".pdf", d, "application/pdf")) for n, _, d in docs], timeout=300)
    r.raise_for_status()
    return r.json()


# ===================================================================== wsad 60 × współbieżność
def g_batch() -> list[dict[str, Any]]:
    docs = dev_set()
    rows: list[dict[str, Any]] = []
    digests: dict[int, dict[str, str | None]] = {}
    for workers in (1, 2, 4):
        with cpu_lock() as waited:
            with running(f"batch-w{workers}", WORK / f"batch-w{workers}", limits={"max_workers": workers}) as (srv, c):
                t0 = time.monotonic()
                j = submit_batch(c, docs)
                t_up = time.monotonic() - t0
                fin = wait_batch(c, j["batch_id"], 900)
                wall = time.monotonic() - t0
                names = {d["document_id"]: n for d, (n, _, _) in zip(j["documents"], docs, strict=True)}
                outcomes: dict[str, int] = {}
                for d in fin["documents"]:
                    outcomes[d["outcome"] or "none"] = outcomes.get(d["outcome"] or "none", 0) + 1
                digests[workers] = {names[d["document_id"]]: result_digest(c, d) for d in fin["documents"]}
                hh = json_health(srv.work)  # type: ignore[attr-defined]
                rows.append({"workers": workers, "docs": len(docs), "wall_s": round(wall, 2), "upload_s": round(t_up, 2), "docs_per_s": round(len(docs) / wall, 2),
                             "outcomes": outcomes, "complete_all": fin.get("done") and len(fin["documents"]) == len(docs), "json_health": hh,
                             "lock_wait_s": round(waited, 1), **srv.usage()})
    same = {w: sum(1 for k in digests[1] if digests[w].get(k) == digests[1][k]) for w in (2, 4)}
    gap_missing = any(not r["complete_all"] or r["json_health"]["unparsable"] or r["json_health"]["tmp_or_part_files"] for r in rows)
    return [vec("W01", "wsad-współbieżność", "wsad 60 dokumentów, max_workers 1/2/4: kompletność, czas, RSS, atomowość, zgodność wyników między poziomami współbieżności",
                "komplet wyników, zero plików tymczasowych i uszkodzonych JSON, wyniki identyczne niezależnie od współbieżności",
                "; ".join(f"w={r['workers']}: {r['wall_s']} s ({r['docs_per_s']} dok/s), RSS drzewa {r['peak_rss_tree_mb']} MiB, cgroup {r['cgroup_memory_peak_mb']} MiB, wyniki {r['outcomes']}" for r in rows)
                + f"; identyczność wyniku (SHA po bajtach) z w=1: w=2 {same[2]}/{len(docs)}, w=4 {same[4]}/{len(docs)}",
                "tak" if gap_missing or same[2] != len(docs) or same[4] != len(docs) else "nie",
                fix="Utrzymać zapis atomowy; w produkcie PDFium w procesach potomnych (współbieżność realna), bo tu LockedReader serializuje odczyt i `max_workers>1` przyspiesza tylko etapy poza PDFium.",
                port_test="test_batch_60_docs_results_independent_of_concurrency", data={"rows": rows, "identical_to_w1": same}),
            ]


# ===================================================================== uszkodzone pliki w środku wsadu
def g_corrupt() -> list[dict[str, Any]]:
    docs = dev_set(4)
    bad: list[tuple[str, str, bytes]] = [("zly_smieci", "x", b"nie pdf"), ("zly_obciety", "x", docs[0][2][:5000]), ("zly_pusty", "x", b""),
                                         ("zly_zaszyfrowany", "x", encrypted_stub())]
    mixed = docs[:4] + bad[:2] + docs[4:8] + bad[2:] + docs[8:]
    with running("corrupt", WORK / "corrupt", limits={"max_workers": 2}) as (srv, c):
        j = submit_batch(c, mixed)
        fin = wait_batch(c, j["batch_id"], 300)
        names = [n for n, _, _ in mixed]
        res = {n: (d["outcome"], d["codes"]) for n, d in zip(names, fin["documents"], strict=True)}
        good = [n for n in names if not n.startswith("zly")]
        good_ok = sum(1 for n in good if res[n][0] not in ("technical_error", None))  # ambiguous/foreign to uczciwe wyniki routera, nie awarie
        bad_ok = sum(1 for n in names if n.startswith("zly") and res[n][0] == "technical_error")
        pr = probe_ok(c)
        return [vec("W02", "wsad-współbieżność", f"{len(bad)} uszkodzone pliki (śmieci, obcięty, pusty, zaszyfrowany) rozsiane w środku wsadu {len(mixed)} dokumentów",
                    "uszkodzone → technical_error z kodem; reszta wsadu kończy się wynikiem",
                    f"poprawne dokumenty przetworzone bez błędu technicznego {good_ok}/{len(good)} (wyniki: {sorted({res[n][0] for n in good})}); uszkodzone jako technical_error {bad_ok}/{len(bad)}: {({k: v for k, v in res.items() if k.startswith('zly')})}; kontrola po wsadzie={pr}",
                    "nie" if good_ok == len(good) and bad_ok == len(bad) else "tak",
                    fix="Utrzymać izolację błędów per dokument; w produkcie dodać test z uszkodzonym plikiem na początku, w środku i na końcu.", port_test="test_corrupt_file_in_batch_does_not_stop_the_rest",
                    data={"results": res, "probe": pr})]





# ===================================================================== kill -9
def start_on(work: Path, name: str, cfg_over: dict[str, Any]) -> AttackServer:
    cp = write_config(WORK / f"{name}.config.json", work, **cfg_over)
    srv = AttackServer(cp, memory_max="14G", log_path=WORK / f"{name}.server.log")
    srv.start()
    return srv


def g_kill() -> list[dict[str, Any]]:
    docs = dev_set()
    trials: list[dict[str, Any]] = []
    for trial, delay in enumerate((0.25, 0.6, 1.0, 1.6, 2.4), 1):
        name = f"kill-{trial}"
        base = WORK / name
        if base.exists():
            shutil.rmtree(base)
        work = base / "data"
        work.mkdir(parents=True)
        srv = start_on(work, name, {"limits": {"max_workers": 2}})
        c = HarnessClient(srv.url, server=srv, timeout=120)
        try:
            j = submit_batch(c, docs)
            time.sleep(delay)
            states_before = {d["document_id"]: d["progress"] for d in c.http.get(f"/batches/{j['batch_id']}").json()["documents"]}
            srv.kill9()
        finally:
            c.close()
        done_n = sum(1 for v in states_before.values() if v == "done")
        hh = json_health(work)
        # na dysku: dokumenty z state.json (ukończone) vs bez (osierocone)
        docs_dir = work / j["batch_id"] / "documents"
        with_state = sum(1 for d in docs_dir.iterdir() if (d / "runs" / "r1" / "state.json").exists()) if docs_dir.exists() else 0
        n_dirs = len(list(docs_dir.iterdir())) if docs_dir.exists() else 0
        # restart na tym samym katalogu roboczym
        srv2 = start_on(work, name + "-restart", {"limits": {"max_workers": 2}})
        c2 = HarnessClient(srv2.url, server=srv2, timeout=60)
        try:
            r = c2.http.get(f"/batches/{j['batch_id']}")
            known = r.status_code
            r_doc = c2.http.get(f"/documents/{j['document_id']}").status_code
            # poprawne ponowienie: wgranie dokumentów, które nie miały state.json
            missing = [(n, cl, d) for (n, cl, d), dd in zip(docs, sorted(docs_dir.iterdir()), strict=False) if not (dd / "runs" / "r1" / "state.json").exists()] if docs_dir.exists() else docs
            jj = submit_batch(c2, missing[:10]) if missing else None
            fin = wait_batch(c2, jj["batch_id"], 300) if jj else {"documents": []}
            retry_ok = sum(1 for d in fin["documents"] if d["outcome"] in ("complete", "partial"))
            pr = probe_ok(c2)
        finally:
            c2.close()
            srv2.stop()
        trials.append({"trial": trial, "kill_after_s": delay, "done_at_kill": done_n, "docs_total": len(docs), "dirs": n_dirs, "dirs_with_state_json": with_state,
                       "orphans_without_state": n_dirs - with_state, "json_health": hh, "batch_known_after_restart_http": known, "document_known_after_restart_http": r_doc,
                       "retry_submitted": min(10, len(missing)), "retry_ok": retry_ok, "probe": pr})
    uncorrupt = all(not t["json_health"]["unparsable"] for t in trials)
    leftovers = sum(len(t["json_health"]["tmp_or_part_files"]) for t in trials)
    lost = all(t["batch_known_after_restart_http"] == 404 for t in trials)
    return [vec("W03", "kill-9", "kill -9 serwera w trakcie wsadu 60 dokumentów (5 prób po 0,25–2,4 s), restart na tym samym katalogu roboczym",
                "brak plików częściowych i uszkodzonych JSON; po restarcie jawny stan wsadu (technical_error / do wznowienia), kontynuacja reszty",
                f"uszkodzone JSON: {sum(len(t['json_health']['unparsable']) for t in trials)}; pliki .tmp/.part po ubiciu: {leftovers}; po restarcie wsad znany: {'nie (404 we wszystkich próbach)' if lost else [t['batch_known_after_restart_http'] for t in trials]}; "
                f"osierocone katalogi dokumentów bez state.json: {[t['orphans_without_state'] for t in trials]} z {len(docs)}; ukończone przed ubiciem: {[t['done_at_kill'] for t in trials]}; ponowne wgranie nieukończonych → {[t['retry_ok'] for t in trials]}/{[t['retry_submitted'] for t in trials]} poprawnych",
                "tak" if (not uncorrupt or leftovers or lost) else "nie",
                fix="Trwały stan wsadu/dokumentu (SQLite jak w ADR-004) zapisywany przed pracą; przy starcie dokumenty `running` → `technical_error` (kod `interrupted`) lub kolejka do wznowienia; sprzątanie `*.tmp`/`*.part`.",
                port_test="test_kill9_mid_batch_then_restart_reports_explicit_state_and_resumes_rest", data={"trials": trials})]


# ===================================================================== wyścigi
def g_races() -> list[dict[str, Any]]:
    docs = dev_set(6)
    recs: list[dict[str, Any]] = []
    with running("races", WORK / "races", limits={"max_workers": 2}) as (srv, c):
        # R01: polling + odczyt wyniku w trakcie zapisu: nigdy częściowy JSON
        j = submit_batch(c, docs * 3)
        stop = threading.Event()
        anomalies: list[str] = []
        counts = {"200": 0, "409": 0, "404": 0, "other": 0}

        def hammer(did: str) -> None:
            while not stop.is_set():
                for p in ("result", "evidence", "report", "metrics"):
                    r = c.http.get(f"/documents/{did}/{p}")
                    k = str(r.status_code) if r.status_code in (200, 409, 404) else "other"
                    counts[k] += 1
                    if r.status_code == 200:
                        try:
                            r.json()
                        except ValueError:
                            anomalies.append(f"{did}/{p}: częściowy/niepoprawny JSON")
                    elif r.status_code not in (404, 409):
                        anomalies.append(f"{did}/{p}: HTTP {r.status_code}")

        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(hammer, d["document_id"]) for d in j["documents"][:8]]
            fin = wait_batch(c, j["batch_id"], 300)
            time.sleep(0.5)
            stop.set()
            for f in futs:
                f.result()
        recs.append(vec("X01", "wyścigi", "8 wątków odpytuje wynik/dowody/raport/metryki w trakcie przetwarzania i zapisu artefaktów", "wyłącznie 404/409 do końca przetwarzania, potem pełny JSON; nigdy częściowy plik",
                        f"żądań: {counts}; anomalie: {anomalies[:3] or 'brak'}", "tak" if anomalies else "nie",
                        fix="Zapis atomowy (jest); test z równoległym odczytem w CI.", port_test="test_concurrent_read_during_commit_never_sees_partial_json", data={"counts": counts, "anomalies": anomalies}))
        # X02: ten sam plik 12× równolegle (jedna bariera) + ta sama zawartość pod inną nazwą
        pdf = docs[0][2]
        barrier = threading.Barrier(12)
        ids: list[str] = []

        def up(i: int) -> None:
            barrier.wait()
            r = c.http.post("/batches", files=[("files", (f"dup{i % 3}.pdf", pdf, "application/pdf"))])
            ids.append(r.json()["document_id"])

        with ThreadPoolExecutor(max_workers=12) as ex:
            list(ex.map(up, range(12)))
        sts = [doc_state(c, i, 120) for i in ids]
        dig = {result_digest(c, {**s, "document_id": i}) for s, i in zip(sts, ids, strict=True)}
        recs.append(vec("X02", "wyścigi", "12 równoległych wgrań tych samych bajtów (na barierze), nazwy dup0–dup2", "12 niezależnych dokumentów z unikalnymi ID i identycznym wynikiem; brak kolizji katalogów",
                        f"unikalne ID: {len(set(ids))}/12; wyniki: {sorted({s['outcome'] for s in sts})}; różnych skrótów wyniku: {len(dig)}", "nie" if len(set(ids)) == 12 and len(dig) == 1 else "tak",
                        fix="Przy dodaniu deduplikacji po SHA-256 zapewnić jednego właściciela próby (blokada/UNIQUE) i konflikt rewizji dla równoległych retry.",
                        port_test="test_concurrent_identical_uploads_yield_distinct_documents_and_equal_results", data={"digests": sorted(d for d in dig if d)}))
        # X03: retry tego samego zadania — uprząż nie ma trasy retry
        r = c.http.post(f"/documents/{ids[0]}/retry")
        recs.append(vec("X03", "wyścigi", "20× retry tego samego zadania równolegle (oczekiwany jeden aktywny run_id, reszta konflikt)", "jedna aktywna próba, reszta 409",
                        f"POST /documents/{{id}}/retry → HTTP {r.status_code}: uprząż nie implementuje retry/rewizji (jeden `run_id` r1) — wektor nie wykonany", "nie dotyczy",
                        fix="W produkcie: retry jako zasób z `run_id`, warunek `If-Match`/UNIQUE(document_id, active), 409 dla drugiego żądania.",
                        port_test="test_20_parallel_retries_produce_single_active_run_and_conflicts"))
        recs.append({"_probe": probe_ok(c)})
    # X04: dwa procesy serwera na tym samym katalogu roboczym
    base = WORK / "twoprocs"
    if base.exists():
        shutil.rmtree(base)
    work = base / "data"
    work.mkdir(parents=True)
    s1 = start_on(work, "twoprocs-a", {"limits": {"max_workers": 2}})
    s2 = start_on(work, "twoprocs-b", {"limits": {"max_workers": 2}})
    c1, c2 = HarnessClient(s1.url, timeout=120), HarnessClient(s2.url, timeout=120)
    try:
        ja, jb = submit_batch(c1, docs), submit_batch(c2, docs)
        fa, fb = wait_batch(c1, ja["batch_id"], 300), wait_batch(c2, jb["batch_id"], 300)
        cross = c2.http.get(f"/batches/{ja['batch_id']}").status_code
        hh = json_health(work)
        okc = sum(1 for d in fa["documents"] + fb["documents"] if d["outcome"] != "technical_error")
        tot = len(fa["documents"]) + len(fb["documents"])
        recs.append(vec("X04", "wyścigi", "dwa procesy serwera na tym samym katalogu roboczym (po 18 dokumentów każdy)", "brak kolizji i błędów 500; spójny stan (w produkcie: blokady SQLite bez `database is locked` jako 500)",
                        f"dokumenty bez błędu technicznego {okc}/{tot} ({len(docs)} + {len(docs)}); JSON uszkodzone: {hh['unparsable'] or 'brak'}; drugi proces widzi wsad pierwszego: HTTP {cross} (stan tylko w pamięci procesu)", "częściowo" if cross == 404 else "nie",
                        fix="Stan w SQLite współdzielonym przez procesy lub blokada wyłączności katalogu roboczego (flock) przy starcie.",
                        port_test="test_second_server_process_on_same_workdir_is_refused_or_state_is_shared", data={"json_health": hh, "cross_http": cross}))
    finally:
        c1.close()
        c2.close()
        s1.stop()
        s2.stop()
    return recs


# ===================================================================== izolacja dokumentów
def g_isolation() -> list[dict[str, Any]]:
    docs = dev_set(6)
    pick = [docs[0], docs[7], docs[14], docs[13], docs[1], docs[16]]  # różne klasy i sprawy
    solo: dict[str, str | None] = {}
    with running("iso-solo", WORK / "iso-solo", limits={"max_workers": 1}) as (srv, c):
        for n, _, d in pick:
            st = upload_and_wait(c, d, n + ".pdf", 60)
            solo[n] = result_digest(c, {**st, "document_id": st["_document_id"]})
    arms: dict[str, dict[str, str | None]] = {}
    for arm, order, workers in (("kolejność odwrócona, w=1", pick[::-1], 1), ("równolegle, w=4", pick, 4), ("w jednym wsadzie z dokumentem o innym NIP, w=2", [docs[10], *pick, docs[12]], 2)):
        with running("iso-" + arm[:3], WORK / ("iso-" + str(workers) + arm[:3]), limits={"max_workers": workers}) as (srv, c):
            j = submit_batch(c, order)
            fin = wait_batch(c, j["batch_id"], 300)
            res = {}
            for d, (n, _, _) in zip(fin["documents"], order, strict=True):
                if n in solo:
                    res[n] = result_digest(c, d)
            arms[arm] = res
    diffs = {a: [n for n in solo if r.get(n) != solo[n]] for a, r in arms.items()}
    # dostęp do cudzych identyfikatorów z innego wsadu
    return [vec("I01", "izolacja-dokumentów", "ten sam dokument samotnie, w odwróconej kolejności, równolegle i obok dokumentów z innym NIP", "wynik niezależny od sąsiadów i kolejności (brak uzupełniania pól sąsiadem)",
                f"różnice względem wyniku samotnego (liczba dokumentów z {len(solo)}): " + "; ".join(f"{a}: {len(v)}" for a, v in diffs.items()), "tak" if any(diffs.values()) else "nie",
                fix="Utrzymać brak współdzielonego stanu między dokumentami; test w CI na tych trzech układach.", port_test="test_document_result_independent_of_neighbours_and_order", data={"diffs": diffs, "solo": solo})]


# ===================================================================== kolejka bez limitu
def g_queue() -> list[dict[str, Any]]:
    docs = dev_set(6)
    small = docs[14][2]
    with running("queue", WORK / "queue", limits={"max_workers": 1, "max_batch_documents": 500}) as (srv, c):
        t0 = time.monotonic()
        bids = []
        lat = []
        for i in range(8):
            r = c.http.post("/batches", files=[("files", (f"{i}-{k}.pdf", small, "application/pdf")) for k in range(100)], timeout=120)
            bids.append(r.json()["batch_id"])
            t1 = time.monotonic()
            c.http.get("/health", timeout=10)
            lat.append(round(time.monotonic() - t1, 4))
        accept_s = time.monotonic() - t0
        refused = False
        pr0 = c.http.get(f"/batches/{bids[-1]}").json()
        queued = sum(1 for d in pr0["documents"] if d["progress"] == "queued")
        fin = [wait_batch(c, b, 900) for b in bids]
        total_ok = sum(1 for f in fin for d in f["documents"] if d["outcome"] in ("complete", "partial"))
        return [vec("Q01", "kolejka", "800 dokumentów w 8 wsadach naraz przy 1 wątku roboczym (zapchana kolejka)", "limit długości kolejki (429/503) lub kontrolowana praca bez wzrostu pamięci; serwer reaguje",
                    f"przyjęto wszystko w {accept_s:.1f} s bez odmowy (kolejka bez limitu; w ostatnim wsadzie {queued}/100 w stanie queued po przyjęciu); opóźnienie /health ≤ {max(lat)} s; ukończone {total_ok}/800; RSS drzewa {srv.usage()['peak_rss_tree_mb']} MiB",
                    "częściowo", fix="Limit liczby oczekujących dokumentów (np. 429 `queue_full` z Retry-After) i limit łącznego rozmiaru oczekujących plików.", port_test="test_queue_full_returns_429_and_health_stays_responsive",
                    data={"accept_s": round(accept_s, 2), "health_latencies": lat, "ok": total_ok, **srv.usage()})]


GROUPS = {"batch": g_batch, "corrupt": g_corrupt, "kill": g_kill, "races": g_races, "isolation": g_isolation, "queue": g_queue}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ns = ap.parse_args()
    only = {x for x in ns.only.split(",") if x}
    out_path = ATAK / EXPN / "wyniki.json"
    out = json.loads(out_path.read_text()) if out_path.exists() and only else {"experiment": EXPN, "versions": versions(), "vectors": [], "probes": {},
                                                                              "note": "Wynik opisuje uprząż (stan procesu w pamięci, LockedReader), nie produkt. Dane: 60 dokumentów rozwojowych, ekstraktor regułowy."}
    for g, fn in GROUPS.items():
        if only and g not in only:
            continue
        t0 = time.monotonic()
        print("==", g, flush=True)
        recs = fn()
        for r in recs:
            if "_probe" in r:
                out["probes"][g] = r["_probe"]
            else:
                out["vectors"] = [v for v in out["vectors"] if v["id"] != r["id"]] + [r]
        out["vectors"].sort(key=lambda v: v["id"])
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"   {g}: {len(recs)} w {time.monotonic() - t0:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
