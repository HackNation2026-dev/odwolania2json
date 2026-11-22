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
