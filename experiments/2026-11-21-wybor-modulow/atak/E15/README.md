# E15: wsad i współbieżność, uszkodzone pliki, `kill -9`, wyścigi

> **Zakres.** Wynik opisuje **uprząż** (stan wsadów i dokumentów w pamięci procesu, `LockedReader` serializujący PDFium, pula wątków), **nie produkt** z SQLite (ADR-004). Dane: 60 dokumentów ze zbioru rozwojowego (20 odwołań, 20 pełnomocnictw, 20 przelewów), ekstraktor regułowy, bez OCR i bez LLM.
> **Czas i RSS są niewiążące.** Pomiar czasu szedł pod `flock /tmp/uzp-cpu.lock`, ale cztery grupy liczyły naraz (load avg ok. 22–35 na 8 rdzeniach); liczby dok/s i RSS opisują stan „pod obciążeniem, nie do decyzji”. Czas do decyzji powstanie w osobnym cichym oknie ogłoszonym przez koordynatora.

## Hipoteza i kryterium (plan E15)

Wsad kończy się kompletem wyników niezależnie od współbieżności (1/2/4), uszkodzony plik w środku nie zatrzymuje reszty, po `kill -9` nie ma plików częściowych ani uszkodzonych JSON, a stan jest jawny i wsad da się dokończyć. Kryterium: *brak plików częściowych, wsad kończy resztę*.

## Metoda

Skrypt: `.venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E15/e15.py` (`--only batch,corrupt,kill,races,isolation,queue`). Wynik: `wyniki.json`.

- **W01**: wsad 60 dokumentów, `max_workers` 1/2/4, świeży serwer pod 14 GB; po zakończeniu: kompletność, parsowalność wszystkich `*.json`, brak `*.tmp`/`*.part`, skrót SHA wyniku każdego dokumentu porównany z `w=1`.
- **W02**: 12 poprawnych dokumentów + 4 uszkodzone (śmieci, obcięty, pusty, zaszyfrowany) rozsiane w środku wsadu.
- **W03**: `kill -9` całej grupy procesów serwera w trakcie wsadu 60 dokumentów, 5 prób z opóźnieniem 0,25 / 0,6 / 1,0 / 1,6 / 2,4 s; potem kontrola plików, restart serwera **na tym samym katalogu roboczym**, zapytanie o wsad i ponowne wgranie nieukończonych.
- **X01–X04**: odczyt wyniku/dowodów/raportu/metryk z 8 wątków w trakcie zapisu; 12 równoległych wgrań tych samych bajtów na barierze; trasa retry (nie istnieje); dwa procesy serwera na jednym katalogu roboczym.
- **I01**: ten sam dokument samotnie, w odwróconej kolejności, równolegle (w=4) i obok dokumentów z innym NIP.
- **Q01**: 8 wsadów po 100 dokumentów naraz przy jednym wątku roboczym (kolejka).

## Jak to działa i dlaczego tak wyszło

- **Zapis atomowy działa**: `write_json_atomic` (plik tymczasowy, `fsync`, `os.replace`) i `input.pdf.part` → `os.replace`. Po `kill -9` w 5 próbach: 0 uszkodzonych JSON, 0 plików `.tmp`/`.part`; 8 wątków odpytujących wynik w trakcie zapisu widziało tylko 200 z pełnym JSON-em albo 409 (1027 × 200, 109 × 409, 0 anomalii). **Uwaga uczciwości:** wsad 60 dokumentów kończy się w ~1,5 s, więc tylko 3 z 5 prób trafiły w środek wsadu (7, 22 i 33 z 60 ukończonych w chwili ubicia; próby 4 i 5 ubiły serwer po skończeniu), a ubicie dokładnie w trakcie `os.replace` nie zostało zaobserwowane; brak uszkodzeń jest dowodem na tej próbce, nie gwarancją.
- **Stan wsadu istnieje tylko w pamięci procesu.** Po restarcie na tym samym katalogu `GET /batches/{id}` zwraca 404 we wszystkich próbach; dokumenty bez `state.json` (52, 37 i 25 z 60 w trzech próbach z ubiciem w trakcie) zostają jako osierocone katalogi bez jawnego stanu (brak `technical_error`, brak „do wznowienia”). Ponowne wgranie nieukończonych (10 z 10, 9 z 10, 7 z 10 sprawdzanych) działa, bo to nowy wsad: kontynuacja jest ręczna, a mapowanie wejście→wynik ginie.
- **Współbieżność nie zmienia wyników**: skrót bajtowy wyniku identyczny dla 60/60 dokumentów przy w=2 i w=4 względem w=1; wyniki `complete` 42, `partial` 8, `ambiguous` 10 w każdym poziomie. `max_workers>1` niewiele przyspiesza, bo `LockedReader` serializuje PDFium (PDFium nie jest bezpieczny wątkowo), a dokumenty testowe są małe; czasy 1,3 / 2,2 / 1,6 s są niewiążące (obciążenie).
- **Uszkodzone pliki w środku** nie zatrzymują wsadu: 4/4 jako `technical_error` z kodem (`not_a_pdf`, `pdf_corrupted`, `not_a_pdf`, `pdf_encrypted`), 12/12 poprawnych przetworzonych (`complete`/`partial`/`ambiguous`; to uczciwe wyniki routera, nie awarie).
- **Izolacja dokumentów**: 0 różnic wyniku w 3 układach (odwrócona kolejność, równolegle, obok dokumentów z innym NIP) na 6 dokumentach. Uprząż nie współdzieli stanu między dokumentami.
- **Wyścigi**: 12 równoległych wgrań tych samych bajtów dało 12 unikalnych ID i 1 skrót wyniku (X02). Brak cache po SHA, więc nie ma „jednego właściciela próby” do przetestowania. Trasy retry nie ma (X03: HTTP 404), więc wektor „20× retry” nie został wykonany. Dwa procesy na jednym katalogu nie kolidują (ID losowe, brak wspólnej bazy), ale nie widzą swoich wsadów (X04).
- **Kolejka jest nieograniczona**: 800 dokumentów przyjęto w 0,8 s bez odmowy (wszystkie 100 w ostatnim wsadzie w stanie `queued`), `/health` ≤ 53 ms, wszystkie ukończone; w produkcie zapchana kolejka potrzebuje limitu i kodu 429.

## Ograniczenia

Próbka: 60 małych, tekstowych dokumentów; ekstraktor regułowy (szybki), więc wsad trwa sekundy i `kill -9` rzadko trafia w trakcie zapisu; z OCR i LLM okno ubicia jest szersze, ale tego nie mierzono. Brak testu SQLite (`database is locked`), bo uprząż go nie ma. Czas i RSS niewiążące (obciążenie maszyny).

## Wyniki wektorów

### Zestawienie wektorów

Wektorów: 9; luka: częściowo 2, nie 5, nie dotyczy 1, tak 1.

| ID | Rodzina | Wektor | Luka |
|---|---|---|---|
| I01 | izolacja-dokumentów | ten sam dokument samotnie, w odwróconej kolejności, równolegle i obok dokumentów z innym NIP | **nie** |
| Q01 | kolejka | 800 dokumentów w 8 wsadach naraz przy 1 wątku roboczym (zapchana kolejka) | **częściowo** |
| W01 | wsad-współbieżność | wsad 60 dokumentów, max_workers 1/2/4: kompletność, czas, RSS, atomowość, zgodność wyników między poziomami współbieżności | **nie** |
| W02 | wsad-współbieżność | 4 uszkodzone pliki (śmieci, obcięty, pusty, zaszyfrowany) rozsiane w środku wsadu 16 dokumentów | **nie** |
| W03 | kill-9 | kill -9 serwera w trakcie wsadu 60 dokumentów (5 prób po 0,25–2,4 s), restart na tym samym katalogu roboczym | **tak** |
| X01 | wyścigi | 8 wątków odpytuje wynik/dowody/raport/metryki w trakcie przetwarzania i zapisu artefaktów | **nie** |
| X02 | wyścigi | 12 równoległych wgrań tych samych bajtów (na barierze), nazwy dup0–dup2 | **nie** |
| X03 | wyścigi | 20× retry tego samego zadania równolegle (oczekiwany jeden aktywny run_id, reszta konflikt) | **nie dotyczy** |
| X04 | wyścigi | dwa procesy serwera na tym samym katalogu roboczym (po 18 dokumentów każdy) | **częściowo** |

### Szczegóły: oczekiwane, faktyczne, poprawka, test do produktu

**I01 — ten sam dokument samotnie, w odwróconej kolejności, równolegle i obok dokumentów z innym NIP** (luka: nie)

- Oczekiwane: wynik niezależny od sąsiadów i kolejności (brak uzupełniania pól sąsiadem)
- Faktyczne: różnice względem wyniku samotnego (liczba dokumentów z 6): kolejność odwrócona, w=1: 0; równolegle, w=4: 0; w jednym wsadzie z dokumentem o innym NIP, w=2: 0
- Proponowana poprawka: Utrzymać brak współdzielonego stanu między dokumentami; test w CI na tych trzech układach.
- Test do przeniesienia do produktu: `test_document_result_independent_of_neighbours_and_order`

**Q01 — 800 dokumentów w 8 wsadach naraz przy 1 wątku roboczym (zapchana kolejka)** (luka: częściowo)

- Oczekiwane: limit długości kolejki (429/503) lub kontrolowana praca bez wzrostu pamięci; serwer reaguje
- Faktyczne: przyjęto wszystko w 0.8 s bez odmowy (kolejka bez limitu; w ostatnim wsadzie 100/100 w stanie queued po przyjęciu); opóźnienie /health ≤ 0.0526 s; ukończone 800/800; RSS drzewa 75.7 MiB
- Proponowana poprawka: Limit liczby oczekujących dokumentów (np. 429 `queue_full` z Retry-After) i limit łącznego rozmiaru oczekujących plików.
- Test do przeniesienia do produktu: `test_queue_full_returns_429_and_health_stays_responsive`

**W01 — wsad 60 dokumentów, max_workers 1/2/4: kompletność, czas, RSS, atomowość, zgodność wyników między poziomami współbieżności** (luka: nie)

- Oczekiwane: komplet wyników, zero plików tymczasowych i uszkodzonych JSON, wyniki identyczne niezależnie od współbieżności
- Faktyczne: w=1: 1.32 s (45.39 dok/s), RSS drzewa 70.0 MiB, cgroup 58.1 MiB, wyniki {'complete': 42, 'partial': 8, 'ambiguous': 10}; w=2: 2.24 s (26.76 dok/s), RSS drzewa 69.8 MiB, cgroup 58.5 MiB, wyniki {'complete': 42, 'partial': 8, 'ambiguous': 10}; w=4: 1.55 s (38.7 dok/s), RSS drzewa 76.0 MiB, cgroup 65.7 MiB, wyniki {'complete': 42, 'partial': 8, 'ambiguous': 10}; identyczność wyniku (SHA po bajtach) z w=1: w=2 60/60, w=4 60/60
- Proponowana poprawka: Utrzymać zapis atomowy; w produkcie PDFium w procesach potomnych (współbieżność realna), bo tu LockedReader serializuje odczyt i `max_workers>1` przyspiesza tylko etapy poza PDFium.
- Test do przeniesienia do produktu: `test_batch_60_docs_results_independent_of_concurrency`

**W02 — 4 uszkodzone pliki (śmieci, obcięty, pusty, zaszyfrowany) rozsiane w środku wsadu 16 dokumentów** (luka: nie)

- Oczekiwane: uszkodzone → technical_error z kodem; reszta wsadu kończy się wynikiem
- Faktyczne: poprawne dokumenty przetworzone bez błędu technicznego 12/12 (wyniki: ['ambiguous', 'complete', 'partial']); uszkodzone jako technical_error 4/4: {'zly_smieci': ('technical_error', ['not_a_pdf']), 'zly_obciety': ('technical_error', ['pdf_corrupted']), 'zly_pusty': ('technical_error', ['not_a_pdf']), 'zly_zaszyfrowany': ('technical_error', ['pdf_encrypted'])}; kontrola po wsadzie={'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Utrzymać izolację błędów per dokument; w produkcie dodać test z uszkodzonym plikiem na początku, w środku i na końcu.
- Test do przeniesienia do produktu: `test_corrupt_file_in_batch_does_not_stop_the_rest`

**W03 — kill -9 serwera w trakcie wsadu 60 dokumentów (5 prób po 0,25–2,4 s), restart na tym samym katalogu roboczym** (luka: tak)

- Oczekiwane: brak plików częściowych i uszkodzonych JSON; po restarcie jawny stan wsadu (technical_error / do wznowienia), kontynuacja reszty
- Faktyczne: uszkodzone JSON: 0; pliki .tmp/.part po ubiciu: 0; po restarcie wsad znany: nie (404 we wszystkich próbach); osierocone katalogi dokumentów bez state.json: [52, 37, 25, 0, 0] z 60; ukończone przed ubiciem: [7, 22, 33, 60, 60]; ponowne wgranie nieukończonych → [10, 9, 7, 0, 0]/[10, 10, 10, 0, 0] poprawnych
- Proponowana poprawka: Trwały stan wsadu/dokumentu (SQLite jak w ADR-004) zapisywany przed pracą; przy starcie dokumenty `running` → `technical_error` (kod `interrupted`) lub kolejka do wznowienia; sprzątanie `*.tmp`/`*.part`.
- Test do przeniesienia do produktu: `test_kill9_mid_batch_then_restart_reports_explicit_state_and_resumes_rest`

**X01 — 8 wątków odpytuje wynik/dowody/raport/metryki w trakcie przetwarzania i zapisu artefaktów** (luka: nie)

- Oczekiwane: wyłącznie 404/409 do końca przetwarzania, potem pełny JSON; nigdy częściowy plik
- Faktyczne: żądań: {'200': 1214, '409': 102, '404': 0, 'other': 0}; anomalie: brak
- Proponowana poprawka: Zapis atomowy (jest); test z równoległym odczytem w CI.
- Test do przeniesienia do produktu: `test_concurrent_read_during_commit_never_sees_partial_json`

**X02 — 12 równoległych wgrań tych samych bajtów (na barierze), nazwy dup0–dup2** (luka: nie)

- Oczekiwane: 12 niezależnych dokumentów z unikalnymi ID i identycznym wynikiem; brak kolizji katalogów
- Faktyczne: unikalne ID: 12/12; wyniki: ['complete']; różnych skrótów wyniku: 1
- Proponowana poprawka: Przy dodaniu deduplikacji po SHA-256 zapewnić jednego właściciela próby (blokada/UNIQUE) i konflikt rewizji dla równoległych retry.
- Test do przeniesienia do produktu: `test_concurrent_identical_uploads_yield_distinct_documents_and_equal_results`

**X03 — 20× retry tego samego zadania równolegle (oczekiwany jeden aktywny run_id, reszta konflikt)** (luka: nie dotyczy)

- Oczekiwane: jedna aktywna próba, reszta 409
- Faktyczne: POST /documents/{id}/retry → HTTP 404: uprząż nie implementuje retry/rewizji (jeden `run_id` r1) — wektor nie wykonany
- Proponowana poprawka: W produkcie: retry jako zasób z `run_id`, warunek `If-Match`/UNIQUE(document_id, active), 409 dla drugiego żądania.
- Test do przeniesienia do produktu: `test_20_parallel_retries_produce_single_active_run_and_conflicts`

**X04 — dwa procesy serwera na tym samym katalogu roboczym (po 18 dokumentów każdy)** (luka: częściowo)

- Oczekiwane: brak kolizji i błędów 500; spójny stan (w produkcie: blokady SQLite bez `database is locked` jako 500)
- Faktyczne: dokumenty bez błędu technicznego 36/36 (18 + 18); JSON uszkodzone: brak; drugi proces widzi wsad pierwszego: HTTP 404 (stan tylko w pamięci procesu)
- Proponowana poprawka: Stan w SQLite współdzielonym przez procesy lub blokada wyłączności katalogu roboczego (flock) przy starcie.
- Test do przeniesienia do produktu: `test_second_server_process_on_same_workdir_is_refused_or_state_is_shared`

## Wniosek decyzyjny wobec kryterium z planu

Kryterium *„brak plików częściowych, wsad kończy resztę”* jest **spełnione w części plikowej** (atomowość: 0 plików częściowych i 0 uszkodzonych JSON w 5 ubiciach i 8 wątkach odczytu; reszta wsadu kończy się przy uszkodzonym pliku; wyniki niezależne od współbieżności i sąsiadów) i **niespełnione w części stanu**: po `kill -9` wsad jest nieznany (404), osierocone dokumenty nie mają jawnego stanu i nic nie wznawia reszty. To luka uprzęży wynikająca z trzymania stanu w pamięci; w produkcie wymaga trwałego stanu (SQLite, ADR-004) zapisanego przed pracą i reguły przy starcie: dokument `running` bez `state.json` → `technical_error` (kod `interrupted`) albo kolejka do wznowienia, plus sprzątanie `*.tmp`/`*.part`.

Do przeniesienia: test `kill -9` w trakcie wsadu z restartem i oczekiwanym jawnym stanem, limit kolejki (429), jeden aktywny `run_id` przy retry (409), blokada katalogu roboczego przy drugim procesie. **Pewność:** wysoka dla atomowości i niezależności wyników na tej próbce, średnia dla ubicia w trakcie `os.replace` (nie zaobserwowano trafienia). **Otwarte:** zachowanie z OCR/LLM w trakcie wsadu, SQLite, realna współbieżność procesów PDFium.
