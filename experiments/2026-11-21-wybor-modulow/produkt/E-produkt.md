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

## 2. `process` z prawdziwym LLM: NIE WYKONANY

**Liczb F1 produktu z prawdziwym LLM nie ma.** Powody i stan na koniec etapu (22.11.2026):

- Dostawca główny (MiniMax `MiniMax-M3.1-Flash-Preview`): jedna próba na jednym dokumencie (`przyklad_02/potwierdzenie_przelewu.pdf`). Self-check zwrócił `llm_rate_limit` (HTTP 429, wyczerpany limit konta); program zakończył się kodem 2 bez przetwarzania wsadu, zgodnie z ADR-006. Zużyto 1 wywołanie.
- Dostawca zapasowy (GLM `glm-5.3-flash` przez OpenCode, ADR-007): kod i testy na atrapie HTTP są w `main`, ale przebieg na dokumentach nie został uruchomiony przed końcem etapu. Zużyto 0 wywołań z uzgodnionego limitu 200.

### Jak wznowić

Skrypt dzieli pomiar na partie i nie powtarza dokumentów z wynikiem; budżet wywołań obowiązuje łącznie w katalogu roboczym (`.ci/eval-process/state.json`).

```sh
export CI_PYTHON=$PWD/.venv/bin/python PATH=$PWD/.venv/bin:$PATH
FB="--allowed-hosts api.minimax.io,opencode.ai --fallback-base-url https://opencode.ai/inference/go/openai/v1 \
    --fallback-model glm-5.3-flash --fallback-key-file ~/kluczOpenCodeGLM"
# 1) próba 10 dokumentów: sprawdź statusy, kody błędów, tokeny i czas w wypisanym podsumowaniu
python scripts/eval_process.py $FB --fallback-headers '{"x-opencode-session": "{session}"}' --max-docs 10 --call-budget 200
# 2) reszta 147 dokumentów rozwojowych (49 spraw); wynik do pliku
python scripts/eval_process.py $FB --fallback-headers '{"x-opencode-session": "{session}"}' --call-budget 200 --out .ci/eval-process/wynik.json
# 3) sama ocena dotychczasowych wyników, bez wywołań
python scripts/eval_process.py --skip-run
```

Ponowienia sieciowe są w pomiarze wyłączone (`--max-retries 0`), a dostawca po błędzie nie jest pytany ponownie w tym uruchomieniu (`--cooldown 86400`): HTTP 429 albo 403 od dostawcy zatrzymuje wywołania, pozostałe dokumenty dostają `{}` z kodem błędu, a podsumowanie jest oznaczone jako niepełne (kod wyjścia 3). Podsumowanie podaje F1 przybliżony ogółem, per klasa i per pole z przedziałem z bootstrapu po sprawach, liczbę dokumentów bez wyniku, kody błędów technicznych, który dostawca i model odpowiedział dla ilu dokumentów oraz zużycie wywołań i tokenów.

Sprawdzone bez sieci: `python scripts/eval_process.py --skip-run` na pustym katalogu roboczym zwraca 147 dokumentów zaplanowanych, 0 ocenionych i kod 3 (pomiar niepełny).

Ograniczenia do zapisania przy wyniku: jeden przebieg (bez powtórzeń), brak negatywów w domyślnym zestawie (`--negatives` je dołącza), wynik na dostawcy zapasowym nie dowodzi zgodności z wymogiem UE/EOG (ADR-007), a porównanie z E10 (tekst 0,938 [0,910; 0,959], inny model i 25 spraw) nie jest sparowane.
