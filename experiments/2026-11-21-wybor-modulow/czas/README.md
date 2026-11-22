# Grupa T: czas i pamięć do decyzji (T1-T6)

**Stan: CZĘŚCIOWY i OBCIĄŻONY.** Cichego okna nie było: maszyna była współdzielona (load avg 3-80, także od cudzych repozytoriów: next build, playwright, kwin, IDE). Wszystkie czasy ścienne są „obciążone, orientacyjne” (górne granice). Wyniki bez oznaczenia „niewiążące” mają znaczenie rzędu wielkości i **rankingu konfiguracji w obrębie jednego pomiaru** (jednostki były przeplatane w losowanych blokach, więc szum rozkłada się równo), nie wartości absolutnych dla laptopa jury. Wyniki: [PODSUMOWANIE.md](PODSUMOWANIE.md).

## Jak to działa i dlaczego

- `tlib.py`: bramka ciszy, metadane (model CPU Core Ultra 7 258V, 8 rdzeni bez HT, wersje, ziarno 20261122, governor `powersave`), statystyki, cgroup `memory.peak`, monitor obcych procesów `.venv-exp`. Reguły bramki zmieniały się na polecenie koordynatora: najpierw load avg < 1,0; potem **load avg 1 min < 4, po ≤ czasu oczekiwania pomiar mimo to z oznaczeniem „obciążony”** (próg `LOAD_THRESHOLD = 4.0`). Jednostka z obcym aktywnym procesem `.venv-exp` w trakcie jest oznaczona `clean: false`, powtarzana (≤ 3×) i wyłączana z agregatów, jeśli jest czysta alternatywa. `clean` **nie** oznacza ciszy CPU: load avg przed/po i `top_cpu_foreign_at_end` są w każdej jednostce (`wyniki/*.units.*`), a najwyższe obciążenia (> 4) były normą.
- Kolejność jednostek: bloki losowane (każda konfiguracja raz na blok, ziarno stałe).
- `t1_ocr.py` (T1), `t2_pdf.py` (T2), `t3_http.py` + `srvunit.py` (T3), `t4_llm.py` (T4), `t5_model.py` (T5; w tej wersji obliczone ręcznie skryptem z PODSUMOWANIA, zob. `wyniki/T5.json`), `t6_mem.py` (T6). Każdy skrypt: jedno polecenie `../../../.venv-exp/bin/python tN_*.py`. `run_all.sh`, `run2.sh`, `run3.sh` to kolejne wersje sekwencera (zmieniane w trakcie przez skrócony czas).
- Pamięć grupy procesów: `systemd-run --user --scope -p MemoryMax=14G -p MemorySwapMax=0` i odczyt `memory.peak` cgroup scope (T3, T6); T1/T2 używają `VmHWM` procesów.
- Surowe dane: `wyniki/T1.json` (+ `.units.jsonl`), `T2.json` (+ `.units.json`), `T3.json` (+ `.units.jsonl`), `T4.json` (+ `.calls.jsonl`), `T5.json`, `T6.*` jeśli dokończone, `cisza-dziennik.tsv` (load co 30 s), `odrzucone/` (przerwane/zanieczyszczone próby, zachowane dla jawności).

## Odchylenia od zlecenia (jawnie)

- T1: **3 powtórzenia zamiast 5**, siatka zredukowana (dpi 300 × 1/2/4/8 wątków, dpi 150 i 200 przy 4 wątkach, workery 2×{2,4} i 4×{1,2} wątków, jeden wariant `max_side_len=4000`); 150/200 dpi przy 1/2/8 wątkach i 1/2/4 workerów przy dpi 150 pominięte. T1 nie mierzy CPU-sekund (dodane później do skryptu, nie wykonane).
- T2: 198 PDF-ów organizatora (zlecenie mówiło o 206; takiej liczby w repozytorium nie ma), **2 przejścia (zimne, ciepłe) × 2 procesy** na operację (po 2 czyste jednostki zamiast 5), bez renderu 200 dpi.
- T3: tylko zbiór „text” (60 dok., współbieżność 1/2/4, 3 powtórzenia; przy c=2 dwie jednostki nieczyste z powodu obcego procesu); **zbiór „scan” niewykonany** (przerwany: jedna jednostka trwała > 10 min przy load 50-80).
- T4: **niewykonane** (patrz PODSUMOWANIE).
- T5: wersja uproszczona (z czasu ściennego, górna granica), bez CPU-sekund i bez opóźnienia LLM.
- T6: patrz PODSUMOWANIE (jeśli brak wiersza z liczbą, niewykonane).
