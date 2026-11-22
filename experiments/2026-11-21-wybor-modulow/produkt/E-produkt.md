# E-produkt: pomiar polecenia `process` (produkt, nie uprząż)

**Wynik nie jest oficjalnym F1.** Miara: F1 przybliżony ewaluatora zespołu (`apps/backend/odwolania2json/evaluator.py`, ADR-005), przedział 95% z bootstrapu po sprawach (`bootstrap.py`, 2000 losowań, ziarno 20261122). Zbiór kontrolny nie był uruchamiany.

## Stan (2026-11-22)

| Pomiar | Stan |
|---|---|
| Pipeline produktu na zapisanych odpowiedziach E10 (bez wywołań API) | wykonany, wynik niżej |
| `process` z prawdziwym LLM | w toku: dostawca główny (MiniMax) zwraca HTTP 429, patrz niżej |

## 1. Pipeline produktu na zapisanych odpowiedziach E10 (bez sieci)

Co sprawdza: czy kod produktu (`extract/answer.py`, `extract/pipeline.py`, `serialize.py`) z tych samych odpowiedzi modelu daje ten sam wynik co uprząż. Nie sprawdza czytnika PDF produktu ani nowych wywołań.

Metoda: 435 wierszy `llm-e2e/E10/raw/e10-text-p2.jsonl` (25 spraw rozwojowych z `subset_dev.json` + 12 negatywów, 5 powtórzeń, MiniMax `MiniMax-M3.1-Flash`); ostatnia poprawna surowa odpowiedź modelu z każdego wiersza przechodzi przez `parse_answer` i `build_extraction`; wiersz bez odpowiedzi liczy się jak `{}`.

| Wariant | F1 przybliżony [95%] |
|---|---|
| uprząż (zapisany `result`) | 0,938 [0,910; 0,959] |
| produkt | 0,938 [0,910; 0,960] |
| produkt bez uzgadniania pary `czynnosc_powod_id` ↔ `czynnosc_opis` | 0,938 [0,910; 0,959] |

Jedyna różnica: uzgadnianie pary powodu ze słownikiem poprawia `czynnosc_opis` (TP 89 → 91, FP 27 → 25 na 125 wystąpieniach); różnica całkowita +0,0003 mieści się w szumie. Prompt produktu jest bajtowo równy promptowi p2 z E10 (test migawki `tests/unit/test_extract_prompt.py`).

## 2. `process` z prawdziwym LLM

Komenda: `python scripts/eval_process.py` (opis opcji: `--help`). Skrypt kopiuje PDF-y spraw rozwojowych do katalogu roboczego, uruchamia `python -m odwolania2json process`, ocenia pliki wyniku i zapisuje podsumowanie JSON.

Próba 22.11.2026: jeden dokument (`przyklad_02/potwierdzenie_przelewu.pdf`), dostawca główny MiniMax `MiniMax-M3.1-Flash-Preview`. Self-check zwrócił `llm_rate_limit` (HTTP 429, wyczerpany limit konta), program zakończył się kodem 2 bez przetwarzania wsadu, zgodnie z ADR-006. **Liczb F1 z tego dostawcy nie ma.**

Wynik pomiaru przez dostawcę zapasowego (ADR-007) zostanie dopisany w tej sekcji po przebiegu.
