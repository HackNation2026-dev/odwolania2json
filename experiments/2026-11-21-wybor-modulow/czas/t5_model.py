"""T5: szacunek czasu całego ukrytego zbioru z liczb T1-T4 (model, nie pomiar). Metoda wg decyzji koordynatora (07:5x): z CZASU CPU, nie ze ściennego.

Polecenie: ../../../.venv-exp/bin/python t5_model.py   → wyniki/T5.json  (czyta T1cpu/T2/T3/T4/T6 z wyniki/; brakujące wejścia są wypisane jako luki)

Model (dokument o p stronach, skan = wszystkie strony przez OCR):
  CPU_doc = c0 + p × (r300 + o)  [CPU-s]   c0: CPU backendu na dokument bez OCR (T3, zbiór text, c=1, ciepły: server_cpu_s / 60),
                                            r300: CPU renderu strony przy 300 dpi (T2, ciepły przejście / liczba stron),
                                            o: CPU OCR na stronę (T1cpu, dpi 300, 1 worker, 4 wątki; CPU z time.process_time workera = suma wątków)
  L(p)    opóźnienie LLM (T4, mediana, prosta przez punkty 2 i 11 str., minimum 50% wartości dla 2 str.) — czas czekania, nie CPU
Czas zbioru: T = max( ΣCPU_doc / R , Σ L / K ) + ogon, gdzie R = liczba rdzeni dostępnych dla backendu (4 lub 8; i7 jury zwykle 4-8 wątków; zakładamy
pełną równoległość, więc to DOLNA granica CPU), K = współbieżność wywołań LLM (limit konta u jury nieznany: 1, 2, 4, 8). Ogon = L̄ + CPU_doc.
Górna granica: ze zmierzonego czasu ściennego T3 (warianty c=1/2/4, maszyna obciążona obcymi zadaniami) skalowanego do 180 dokumentów.
Scenariusze: 60 spraw × 3 dokumenty (180 dok.; rozkład stron z materiałów organizatora), skany 0 / 10 / 50 / 100% dokumentów (strony 2-11 odwołań).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "harness"))
import tlib  # noqa: E402

R = HERE / "wyniki"


def load(n: str) -> dict | None:
    p = R / n
    return json.loads(p.read_text()) if p.exists() else None


def page_counts() -> list[int]:
    import data
    import pypdfium2 as pdfium
    out = []
    for i in data.load_items("all"):
        if i.document_class == "obcy":
            continue
        d = pdfium.PdfDocument(str(i.source))
        out.append(len(d))
        d.close()
    return out


def main() -> int:
    gaps: list[str] = []
    t1c, t2, t3, t4 = load("T1cpu.json"), load("T2.json"), load("T3.json"), load("T4.json")
    pages = page_counts()
    N, P = len(pages), sum(pages)
    # c0
    c0 = None
    if t3 and t3["summary"].get("text_c1", {}).get("clean_units"):
        c0 = t3["summary"]["text_c1"]["warm"]["server_cpu_s"]["p50"] / 60
    else:
        gaps.append("T3 text c1: brak → c0 nieznane")
    r300 = None
    if t2 and t2["summary"].get("render300", {}).get("clean_units"):
        s = t2["summary"]["render300"]
        r300 = s["cpu_s_per_pass_warm"]["p50"] / s["pages_total"]
    else:
        gaps.append("T2 render300: brak → r300 nieznane")
    o = None
    if t1c:
        u = t1c["summary"].get("dpi300_w1_t4_cap2000", {})
        if u.get("clean_units") and u.get("cpu_s_per_page", {}).get("n"):
            o = u["cpu_s_per_page"]["p50"]
    if o is None:
        gaps.append("T1cpu dpi300 w1 t4: brak → CPU OCR/stronę nieznane")
    L2 = L11 = None
    if t4:
        try:
            L2 = t4["summary"]["odwolanie_2str"]["wall_s_incl_retries"]["p50"]
            L11 = t4["summary"]["odwolanie_11str"]["wall_s_incl_retries"]["p50"]
        except KeyError:
            pass
    if L2 is None:
        gaps.append("T4: brak opóźnień LLM → część LLM nieoszacowana")
    out = {"experiment": "T5", "documents": N, "pages_total": P, "pages_per_doc_mean": round(P / N, 2),
           "inputs": {"c0_cpu_s_per_doc": c0, "r300_cpu_s_per_page": r300, "ocr_cpu_s_per_page_t4": o, "llm_p50_2p_s": L2, "llm_p50_11p_s": L11}, "gaps": gaps}
    if None in (c0, r300, o):
        out["scenarios"] = None
        tlib.dump(R / "T5.json", out)
        return 0

    def L(p: int) -> float | None:
        return None if L2 is None else max(0.5 * L2, L2 + (L11 - L2) * (p - 2) / 9)
    Lbar = None if L2 is None else sum(L(p) for p in pages) / N
    scen = {}
    for name, f in (("tekst_100", 0.0), ("skany_10", 0.1), ("skany_50", 0.5), ("skany_100", 1.0)):
        cpu_total = N * c0 + f * P * (r300 + o)
        row = {"frac_scan": f, "cpu_total_s": round(cpu_total, 1), "cpu_s_per_doc": round(cpu_total / N, 2)}
        for R_ in (4, 8):
            row[f"cpu_bound_min_R{R_}"] = round(cpu_total / R_ / 60, 2)
        if Lbar is not None:
            row["llm_total_s_K1"] = round(N * Lbar, 1)
            for K in (1, 2, 4, 8):
                for R_ in (4, 8):
                    t = max(cpu_total / R_, N * Lbar / K) + Lbar + cpu_total / N
                    row[f"total_min_R{R_}_K{K}"] = round(t / 60, 1)
            best = max(cpu_total / 8, N * Lbar / 8)
            row["bottleneck_R8_K4"] = "CPU (OCR)" if cpu_total / 8 > N * Lbar / 4 else "LLM (opóźnienie/limit współbieżności)"
            row["bottleneck_R4_K2"] = "CPU (OCR)" if cpu_total / 4 > N * Lbar / 2 else "LLM (opóźnienie/limit współbieżności)"
        scen[name] = row
    out["scenarios"] = scen
    # górna granica ze ściennego T3 (obciążona maszyna)
    ub = {}
    if t3:
        for k, v in t3["summary"].items():
            if v.get("clean_units"):
                ub[k] = {"warm_wall_s_per_60": v["warm"]["wall_s"]["p50"], "scaled_to_180_min": round(v["warm"]["wall_s"]["p50"] * N / 60 / 60, 1)}
    out["upper_bound_from_T3_wall_no_llm"] = ub
    out["assumptions"] = ["LLM: opóźnienie niezależne od współbieżności (niezmierzone pod współbieżnością); limit konta jury nieznany", "CPU: idealna równoległość na R rdzeniach (dolna granica); realnie 70-90% wydajności",
                          "laptop jury (i7, bez GPU) może być 0,7-2× szybszy/wolniejszy niż Core Ultra 7 258V (8 rdzeni, bez HT)", "bez 429/ponowień, bez startu (zimny start: kilka s)",
                          "OCR max_side_len 2000; dłuższy bok skalowany do ≈2000 px (dla 200 i 300 dpi koszt OCR podobny)"]
    tlib.dump(R / "T5.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
