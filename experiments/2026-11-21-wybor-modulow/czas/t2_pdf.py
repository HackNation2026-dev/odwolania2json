"""T2: czytnik PDF (pypdfium2 przez PdfiumReader uprzęży): czas i RSS odczytu tekstu z geometrią oraz renderu 150/200/300 dpi.

Polecenie: ../../../.venv-exp/bin/python t2_pdf.py [--reps 5]   → wyniki/T2.json (+ T2.units.jsonl)

Materiał: wszystkie PDF-y organizatora w `docs/02-materialy/organizator-uzp/` (tylko odczyt). W repozytorium jest ich 198 (60 spraw × 3 + 12 negatywów
+ 6 dodatkowych w katalogach z 4 plikami); zlecenie mówi o 206 — takiej liczby nie ma w materiałach, zapisano rzeczywistą.
Jednostka = operacja (text | render150 | render200 | render300) w NOWYM procesie: import, potem 2 przejścia po wszystkich dokumentach
(przejście 1 = zimny start procesu i cache plików, przejście 2 = ciepłe), kolejność dokumentów losowana per przejście. Czas dokumentu = otwarcie
bajtów + operacja na wszystkich stronach (render: `PdfiumReader.render_page` = scale dpi/72 względem MediaBox, konwersja do PIL RGB; tekst: `read_page`
= słowa z bbox po /Rotate). Szczyt RSS = VmHWM procesu. Powtórzenia: 5 procesów na operację (≥5 próbek zimnych i ciepłych na dokument), bloki losowane.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "harness"))
import tlib  # noqa: E402

MATERIALS = tlib.REPO / "docs" / "02-materialy" / "organizator-uzp"
OPS = ("text", "render150", "render300")


def all_pdfs() -> list[Path]:
    return sorted(MATERIALS.rglob("*.pdf"))


def worker(op: str, seed: int) -> dict:
    t_imp = time.perf_counter()
    from reading import PdfiumReader
    rd = PdfiumReader()
    t_import = time.perf_counter() - t_imp
    files = all_pdfs()
    blobs = [(str(p.relative_to(MATERIALS)), p.read_bytes()) for p in files]
    rng = random.Random(seed)
    passes = []
    pages = {}
    cpu_pass = []
    for ps in (1, 2):
        c0 = time.process_time()
        order = list(range(len(blobs)))
        rng.shuffle(order)
        times = {}
        for i in order:
            name, b = blobs[i]
            t = time.perf_counter()
            doc = rd.open(b)
            n = rd.page_count(doc)
            for k in range(n):
                if op == "text":
                    rd.read_page(doc, k)
                else:
                    rd.render_page(doc, k, int(op[6:]))
            rd.close(doc)
            times[name] = time.perf_counter() - t
            pages[name] = n
        passes.append(times)
        cpu_pass.append(time.process_time() - c0)
    return {"op": op, "import_s": t_import, "cold": passes[0], "warm": passes[1], "pages": pages, "rss_hwm_mb": tlib.rss_hwm_mb(),
            "cpu_s_pass_cold": cpu_pass[0], "cpu_s_pass_warm": cpu_pass[1], "total_cold_s": sum(passes[0].values()), "total_warm_s": sum(passes[1].values())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--worker")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-wait", type=float, default=3600)
    ns = ap.parse_args()
    if ns.worker:
        print(json.dumps(worker(ns.worker, ns.seed)))
        return 0
    out = HERE / "wyniki" / "T2.json"
    gate0 = tlib.wait_quiet(ns.max_wait, strict=True, label="T2 start")
    units, gates = [], [gate0]
    for rep, op in tlib.block_shuffled(list(OPS), ns.reps):
        for attempt in range(3):
            g = tlib.wait_quiet(ns.max_wait, strict=False, label=f"{op} rep{rep}")
            gates.append(g)
            with tlib.Monitor() as mon:
                p = subprocess.run([sys.executable, str(Path(__file__)), "--worker", op, "--seed", str(rep * 100 + OPS.index(op))], capture_output=True, text=True)
            if p.returncode:
                units.append({"op": op, "rep": rep, "error": p.stderr[-400:], "clean": False})
                break
            r = json.loads(p.stdout.strip().splitlines()[-1])
            r.update({"rep": rep, "attempt": attempt, "gate": g, **mon.record()})
            r["clean"] = r["clean"] and g["quiet"]
            units.append(r)
            print(op, rep, round(r["total_warm_s"], 1), "clean" if r["clean"] else "NIECZYSTA", flush=True)
            if r["clean"]:
                break
    tlib.dump(HERE / "wyniki" / "T2.units.json", units)
    summary = {}
    for op in OPS:
        us = [u for u in units if u["op"] == op and u.get("clean")]
        if not us:
            summary[op] = {"clean_units": 0, "note": "brak czystych jednostek: niewiążące"}
            continue
        names = list(us[0]["pages"])
        pages = us[0]["pages"]
        def per_doc(kind: str) -> dict[str, float]:
            return {n: tlib.pctl([u[kind][n] for u in us], .5) for n in names}
        s = {"clean_units": len(us), "docs": len(names), "pages_total": sum(pages.values()), "import_s": tlib.stats([u["import_s"] for u in us]),
             "rss_peak_mb": tlib.stats([u["rss_hwm_mb"] for u in us]), "cpu_s_per_pass_warm": tlib.stats([u["cpu_s_pass_warm"] for u in us]), "cpu_s_per_pass_cold": tlib.stats([u["cpu_s_pass_cold"] for u in us])}
        for kind in ("cold", "warm"):
            pd = per_doc(kind)
            vals = list(pd.values())
            allv = [u[kind][n] for u in us for n in names]
            s[kind] = {"per_doc_median_s": tlib.stats(vals), "all_samples_s": tlib.stats(allv),
                       "total_s_per_pass": tlib.stats([u[f"total_{kind}_s"] for u in us]),
                       "s_per_page_warm_mean": round(sum(pd.values()) / sum(pages.values()), 5) if kind == "warm" else None}
        pdw = per_doc("warm")
        top = sorted(pdw, key=lambda n: -pdw[n])[:5]
        s["most_expensive_warm"] = [{"doc": n, "pages": pages[n], "median_s": round(pdw[n], 4)} for n in top]
        summary[op] = s
    tlib.dump(out, {"experiment": "T2", "documents": len(all_pdfs()), "environment": tlib.environment(), "gates": gates,
                    "total_wait_s": round(sum(g["waited_s"] for g in gates), 1), "summary": summary,
                    "units_file": "T2.units.json"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
