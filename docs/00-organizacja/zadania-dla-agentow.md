---
wersja: 0.1.0
aktualizacja: 2026-11-22
status: lista zadań do wykonania; stan faktyczny ustal w kodzie i testach
---

# Zadania dla agentów (stan po eksperymentach 2026-11-22)

Tylko to, co zostało do zrobienia. Wyniki i uzasadnienia: [raport eksperymentów](../../experiments/2026-11-21-wybor-modulow/RAPORT.md), [ocena architektury (Fable)](../../experiments/2026-11-21-wybor-modulow/recenzje/fable-ocena-architektury.md), [backlog](backlog.md). Kolejność zadań wynika z oceny: **produkt dziś zapisuje `{}` dla każdego PDF (F1 pól = 0)**, a wszystkie liczby pochodzą z uprzęży w `experiments/`.

**Zadania GUI (`apps/web`) mają osobny plik: [zadania GUI](zadania-gui.md)** (G01–G13: połączenie z silnikiem, edycja i historia wersji, wersja angielska, bramka wizualna, CI, porządki). Zasady wspólne poniżej obowiązują także tam. Z14 (GUI minimum) jest wyprzedzone: GUI istnieje na mocku, więc Z14 dotyczy już tylko API HTTP, a podpięcie GUI to G01 i G02.

## Zasady wspólne (obowiązują w każdym zadaniu)

1. Przeczytaj `AGENTS.md` i `CLAUDE.md`. Pisz po polsku (dokumentacja), nazwy w kodzie i testach po angielsku.
2. **Test najpierw** (czerwony, potem zielony). `mypy --strict`, `ruff`, pokrycie ≥ 90%, mutacje w zakresie (`AGENTS.md`). Zakaz `--no-verify`, `SKIP`, `PRE_COMMIT_ALLOW_NO_CONFIG`. Jeśli hook blokuje, napraw przyczynę.
3. Środowiska: `.venv` (narzędzia deweloperskie i produkt) i `.venv-exp` (OCR, uprząż). Hooki wymagają `export CI_PYTHON=$PWD/.venv/bin/python PATH=$PWD/.venv/bin:$PATH`. Jeśli brak `.venv`: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt -r apps/backend/requirements.txt`; hooki: `sh scripts/install_hooks.sh`.
4. Git: osobna gałąź od `origin/main` na zadanie (`git fetch origin && git checkout -b kacperpaczos/<nazwa> origin/main`), atomowe commity, `git push -u origin <gałąź>`, `gh pr create --base main`, po zielonych hookach `gh pr merge --merge`. **W tym samym katalogu może pracować kilku agentów**: nie przełączaj gałęzi pod cudzymi plikami; jeśli możesz, utwórz osobny worktree (`git worktree add ../<nazwa> -b <gałąź> origin/main`). Nie cofaj cudzych zmian.
5. Dane: oryginały organizatora w `docs/02-materialy/` są niezmienne. Strojenie tylko na zbiorze rozwojowym (`data/podzial.json`). **Zbiór kontrolny wolno uruchomić jeden raz, po zapisaniu wyboru w `WYBOR.md` przed przebiegiem, z licznikiem użyć** (`experiments/2026-11-21-wybor-modulow/llm-e2e/KONTROLNY.md`). Nie używaj wariantów syntetycznych ze spraw kontrolnych do strojenia.
6. Klucze: MiniMax tylko z pliku wskazanego w `MINIMAX_KEY_FILE` (domyślnie `~/kluczMiniMaxKacper`), nigdy w repozytorium, logach, wynikach ani odpowiedziach HTTP. **Nie używaj żadnego innego klucza**, jeśli użytkownik nie dał na niego zgody. Przed commitem sprawdź grepem, że klucza nie ma w nowych plikach. Limit API MiniMax wyczerpał się w nocy 22.11 (wrócił ok. 07:40); wywołania planuj oszczędnie i z ponowieniami.
7. Dużych danych generowanych nie commituj (skany, cache, `vendor`, `work`): są w `.gitignore`. Pliki > 5 MB pytaj o zgodę.
8. Wyniki liczb opisuj jako „F1 przybliżony” (nie oficjalny), z przedziałem z bootstrapu po sprawach (`apps/backend/odwolania2json/bootstrap.py`) i licznością. Nie zawyżaj: jeden generator dokumentów oznacza, że wyniki regułowe są górną granicą.
9. Po zakończeniu zadania zaktualizuj `CHANGELOG.md`, status w [backlogu](backlog.md) i w tym pliku (wykreśl zrobione z listy), a w raporcie podaj komendy weryfikacji i ich wyniki.

## Zadania P0 (bez nich produkt nie ma wyniku)

### Z01. Silnik produktu: przenieść ścieżkę z uprzęży do `process`

**Stan (2026-11-22):** w `main` są klocki: klient LLM (`llm/client.py`, patrz Z04), serializer (`serialize.py`, patrz Z02) i błędy (`errors.py`). **Nie ma** czytnika PDF, adaptera OCR, promptu, pipeline’u ani podpięcia do `process`: `StubEngine` nadal zapisuje `{}`. Niedokończony szkic czytnika i adaptera OCR (bez testów, bez typów dla `pypdfium2`) jest w `experiments/2026-11-21-wybor-modulow/produkt-szkic/` (instrukcja przeniesienia w jego README). Zacznij od testów dla czytnika i OCR, potem prompt p2, pipeline i podpięcie.

**Cel.** Polecenie `python -m odwolania2json process input output` wykonuje prawdziwą ekstrakcję zamiast `StubEngine` (zapis `{}`). Zakres minimalny: pdfium, diagnoza strony, OCR gdy potrzebny, jedno wywołanie LLM na dokument, normalizatory, serializer z szablonu klasy. **Bez** `DataRepository`, HTTP, etapów L, T2, T4 i cache (ocena Fable: nie wpływają na wynik).

**Przeczytaj.** `apps/backend/odwolania2json/engine.py` (`StubEngine`, `run_process`, `write_json_atomic`), `cli.py` (`process`), `loader.py`, `domain/normalize.py`, `packages/contracts/odwolania2json_contracts/models.py`; uprząż do przeniesienia (w `experiments/2026-11-21-wybor-modulow/`): `harness/reading.py` (czytnik pdfium, diagnoza, OCR), `harness/pipeline.py` (`process_document`), `harness/stages.py` (`RulesRouter`, `LlmRouter`, `WordAnchorResolver`, `LlmExtractor`), `harness/llm.py` (klient HTTP Anthropic i OpenAI, kody błędów), `harness/result_model.py`, `llm-e2e/lib/llm_e2e_plugins.py` (`prompt("p2")`, `Llm1Router`, walidacja odpowiedzi), `pola/rules.py` (reguły E09 i pola stałe). Dowody wyboru: `RAPORT.md` §1 i `llm-e2e/E10/README.md`, `E11/README.md`.

**Kroki.**
1. Nowe moduły w `apps/backend/odwolania2json/`: `pdf/reader.py` (słowa z bbox, linie, obrót, diagnoza strony: liczba słów warstwy, pokrycie obrazem), `ocr/rapid.py` (adapter `rapidocr` za protokołem `OcrProvider`, import leniwy, brak = jawny błąd `ocr_unavailable`), `llm/client.py` (protokół Anthropic z konfigurowalnym `base_url`, model, limit tokenów wyjścia, ponowienia, patrz Z04), `extract/prompt.py` (prompt p2 jako stała z testem snapshot), `extract/pipeline.py`, `serialize.py` (Z02).
2. Algorytm dokumentu: czytnik → diagnoza stron → OCR tylko dla stron, które go wymagają (render z limitem dłuższego boku ok. 2000 px, wykrywanie obrotu 90/180, **bez deskew i bez binaryzacji**, E03) → tekst z identyfikatorami linii → **jedno** wywołanie LLM (klasa dokumentu i pola w jednej odpowiedzi, schemat wymuszony, walidacja pydantic) → normalizatory → serializer. Wariant bazowy: tekst PDF + prompt p2 (E10). Dla stron skanowych i zdominowanych obrazem: obraz strony + tekst OCR, **warstwy tekstu PDF takiej strony nie przekazuj** (Z06).
3. Podmień `StubEngine` na `Engine` o tym samym interfejsie (`process(pdf) -> (payload, DocumentClass | None)`), zostaw atrapę jako `StubEngine` dla testów CLI. `run_process` zachowaj (atomowy zapis, niezależność dokumentów, drzewo katalogów).
4. Konfiguracja: `config.py` czyta `LLM_API_KEY`, `LLM_MODEL`; dodaj `LLM_BASE_URL` i protokół (`anthropic`/`openai`), walidację `base_url` (tylko `https`, host z listy zezwoleń z konfiguracji). Klucz tylko w jednym nagłówku właściwym dla protokołu.
5. Testy: jednostkowe dla każdego modułu (atrapa HTTP dla LLM, `tests/fixtures` z krótkimi PDF-ami generowanymi w teście), test integracyjny `process` na 3 małych PDF-ach (tekst, skan, obcy) z atrapą LLM, test że obcy dokument daje `{}`, test że PDF bez warstwy tekstu bez OCR daje `{}` + raport błędu technicznego (nie zmyślone dane).

**Kryteria akceptacji.** `process` na `docs/02-materialy/organizator-uzp/dane/przyklad_01` daje JSON zgodny ze strukturą `oczekiwane-json` (klucze, kolejność, typy); `python scripts/ci.py --stage all` zielone; F1 przybliżony ewaluatora na 25 sprawach rozwojowych z `llm-e2e/subset_dev.json` (z prawdziwym LLM, jedno powtórzenie) nie niższy niż ok. 0,90 na tekście (referencja: E10 0,938 [0,910; 0,959]); wynik zapisany w `experiments/2026-11-21-wybor-modulow/produkt/E-produkt.md` z komendą.

**Weryfikacja.** `.venv/bin/python -m pytest -q`; `.venv/bin/python scripts/ci.py --stage all`; `.venv/bin/python -m odwolania2json process <katalog z 3 PDF> /tmp/out && ls /tmp/out`.

**Pułapki.** Nie kopiuj uprzęży 1:1 (jest poza bramkami jakości, `prune` usuwa elementy: patrz Z02). Nie wołaj LLM w testach jednostkowych. `OMP_NUM_THREADS`/`intra_op_num_threads` ustaw jawnie. `.PDF` (wielkie litery) musi być znajdowane (`loader`): dodaj test.

### Z02. Zawsze plik wyniku, polityka awarii i serializer bez `prune`

**Stan (2026-11-22):** serializer z szablonu klasy (jawne `null`, bez `prune`) jest w `main` z testami (`serialize.py`, `tests/unit/test_serialize.py`). **Zostaje:** ADR-006 z polityką eksportu, adnotacje w architekturze §4.5/§10, polityka awarii w `engine.run_process` (zawsze plik, raport, kod wyjścia), test round-trip na wszystkich 180 plikach referencyjnych (sprawdź, czy już jest w `test_serialize.py`).

**Cel.** Dla każdego pliku wejściowego powstaje JSON (README organizatora §2 pkt 4). Jedna polityka w trzech miejscach, które dziś się różnią: architektura §10 (`empty_json`), `engine.py` (brak pliku i usunięcie poprzedniego), uprząż (brak pliku przy awarii LLM i 409 przy `ambiguous`).

**Przeczytaj.** `architektura-wewnetrzna.md` §4.5, §6, §10; `llm-e2e/E17/README.md` (dane: zerowanie pola bez kotwicy −0,021; brak eksportu `partial` −0,208 tekst, −0,453 skany); `ADR-002` (pkt 11, 12); `experiments/.../atak/E16/README.md` (serializacja, kolejność kluczy, różnica 166 `null`).

**Kroki.**
1. Polityka (zapisz jako `docs/07-decyzje/ADR-006-polityka-eksportu.md` z konsekwencjami): (a) obcy dokument → `{}`; (b) błąd techniczny (OCR, PDF uszkodzony, LLM po wyczerpaniu ponowień) → `{}` **i** wpis w raporcie (`report.json` obok wyniku lub jeden plik `report.jsonl` w katalogu wyjścia), kod wyjścia ≠ 0 dla wsadu; (c) `ambiguous` → najlepsza klasa; (d) niezakotwiczone pole → wartość z flagą w raporcie, **nie** `null`; (e) walidacja nigdy nie blokuje eksportu, tylko flaguje; (f) nie usuwaj poprzedniego pliku wyniku przy błędzie nowego przebiegu (wynik poprzedni nie wraca jako zastępstwo: katalog wyjścia jest nowy na wsad).
2. Serializer z szablonu klasy (`oczekiwane-json/*.json` jako wzorzec struktury): jawne `null` dla brakujących kluczy, **brak `prune`**, kolejność kluczy jak w wzorcu, `pesel` jako tekst lub `null`, `kwota` liczba, numery identyfikacyjne tekst lub `null`.
3. Testy: tabela przypadków (obcy, błąd OCR, błąd LLM po 3 próbach, `ambiguous`, pole bez kotwicy, brak pola) → oczekiwany plik i kod wyjścia; test kolejności kluczy względem wszystkich 180 plików referencyjnych (round-trip: referencja → model → serializacja = bajtowo ten sam JSON po ujednoliconym formatowaniu).

**Kryteria akceptacji.** Dla 100% PDF-ów z wejścia powstaje plik; test round-trip 180/180; ADR-006 zmergowany, `architektura-wewnetrzna.md` §4.5/§10 mają adnotację o pierwszeństwie ADR-006.

**Pułapki.** Zmienia założenia architektury (bbox jako warunek wartości, blokada eksportu): wymaga adnotacji w ADR, nie cichej zmiany. Pytanie do mentora o ewaluację braku pliku (E, pkt 2) pozostaje otwarte: zostaw przełącznik `error_export` (domyślnie `empty_json`).

### Z03. Dostarczenie: instalacja pip, start, README

**Cel.** U jury działa: instalacja z `requirements.txt`, katalogi `input` i `output`, jedno polecenie startowe. Dziś OCR jest w osobnym `apps/backend/requirements-ocr.txt` (skany = 0 po instalacji według instrukcji organizatora).

**Przeczytaj.** `requirements.txt` w korzeniu, `apps/backend/requirements*.txt`, `apps/backend/pyproject.toml`, `README.md` (mówi „aplikacja nie została zaimplementowana”, wersja 0.4.0), README organizatora §2, §5, FAQ 12a.

**Stan 2026-11-22 (Z03 wykonane poza punktami poniżej).** Zrobione: kroki 1–5 (zależności, `requires-python`, `run.sh`, `start.bat`, README, `input/`/`output/` z `.gitkeep`, `scripts/verify_install.py`). Pomiar: czysta instalacja 3.13 ok. 61 s, ok. 500 MB; wagi OCR w kole `rapidocr`. Zostaje: (a) uruchomienie `start.bat` i `verify_install.py` na Windows przez człowieka, (b) wynik dla skanu w `sh run.sh` po Z01 (dziś `process` to atrapa), (c) `process` bez argumentów używa `input`/`output` (zmiana w `cli.py`, część Z01), (d) po Z01 zaktualizować sekcję „Stan implementacji” w README.

**Kroki (wykonane, zachowane jako opis).**
1. `requirements.txt` w korzeniu: tylko zależności uruchomieniowe, przypięte (`==`), wraz z `rapidocr` i `onnxruntime` (CPU); bez `pytest`, `datamodel-code-generator`, `openapi-spec-validator` (do `requirements-dev.txt`); instalacja pakietów lokalnych bez `-e` jeśli to możliwe (`pip install .`/koła). Sprawdź licencje i dostępność kół dla Pythona 3.13 (Linux i Windows).
2. `apps/backend/pyproject.toml`: `requires-python = ">=3.13"`; `package-data` dla wag OCR jeśli koło ich wymaga (wagi muszą być dostarczone przez pip, bez pobierania z sieci przy starcie: sprawdź ENV.md w uprzęży).
3. Skrypty: `run.sh` i `start.bat` (tworzą `.venv`, `pip install -r requirements.txt`, tworzą `input/` i `output/`, uruchamiają `process input output`), `README.md` (po polsku: wymagania, instalacja, uruchomienie, klucz API przez zmienną środowiskową lub plik poza Git, rozwiązywanie problemów).
4. Domyślne `input/` i `output/` w korzeniu (z `.gitkeep`, zawartość w `.gitignore`) używane przez `process` bez argumentów.
5. Test czystej instalacji: skrypt `scripts/verify_install.py` tworzący tymczasowe venv, `pip install -r requirements.txt` bez sieci poza PyPI, uruchamiający `process` na 3 małych PDF-ach z atrapą LLM (zmienna `LLM_BASE_URL` na lokalny mock). Uruchom na Linuksie; **na Windows poproś użytkownika o uruchomienie** i opisz komendę w README (agent zdalny nie ma Windows).

**Kryteria akceptacji.** `sh run.sh` na świeżym klonie daje wynik dla skanu (OCR działa); `scripts/verify_install.py` zielony; `pip install -r requirements.txt` w czystym venv 3.13 bez błędu; README zgodny ze stanem.

**Pułapki.** Wagi OCR pobierane przy pierwszym uruchomieniu = awaria u jury bez sieci. `systemd-run` i `flock` z uprzęży nie działają na Windows: w produkcie ich nie używaj. `rglob("*.pdf")` pomija `.PDF` na Linuksie.

### Z04. LLM: odporność, limity i decyzja o dostawcy

**Stan (2026-11-22):** część kodowa klienta jest w `main` (`llm/client.py`, 646 linii testów: ponowienia z `Retry-After`, kody błędów, walidacja `base_url`, klucz w jednym nagłówku, kanarek). **Zostaje:** self-check przed wsadem podpięty do `process`, limity wywołań na wsad w silniku, test kanarka po artefaktach pełnego przebiegu oraz cała część „decyzja” (zgoda mentora na MiniMax albo drugi dostawca, klucz dla jury).

**Cel.** Wywołanie LLM nie może zerować wyniku wsadu: ponowienia, limity, jawne kody; plus rozstrzygnięcie dostawcy zgodnie z wymogiem „firma i serwery w UE/EOG, open source”.

**Przeczytaj.** `harness/llm.py` (kody `llm_unavailable`, `llm_authorization`, `llm_rate_limit`, `llm_invalid_response`), `atak/E14/README.md` (luki: klucz w 2 nagłówkach do dowolnego hosta, brak limitu budżetu), `pola/BLOKERY.md` (17 z ok. 110 wywołań z 429), `llm-e2e/E10/README.md` (9 odpowiedzi `llm_invalid_response` na długich odwołaniach; M3 zwraca 706 vs 2566 tokenów wyjścia), `ADR-002` pkt 8 (licencja Community, operator w Singapurze).

**Kroki (kod; zadanie dla agenta).**
1. W kliencie: do 3 ponowień z wykładniczym opóźnieniem i szanowaniem `Retry-After` (górny limit 60 s), osobno błędy sieci, 429, 5xx i odpowiedź poza schematem (jedno ponowienie z krótszym limitem wyjścia, potem naprawa JSON ograniczona do usunięcia znaczników ```), twardy limit tokenów wejścia i wyjścia na dokument, limit liczby wywołań na wsad z jawnym błędem.
2. Mały self-check przed wsadem: jedno krótkie wywołanie próbne; przy 401/403/429 natychmiast czytelny komunikat i kod wyjścia 2, bez przetwarzania całego wsadu (zły klucz lub limit = F1 0 dla wszystkiego).
3. Walidacja `base_url` i jeden nagłówek klucza zależny od protokołu; klucz nigdy w logach i wyjątkach (test z kanarkiem: mock LLM zwraca kanarka w treści błędu, `grep` po wszystkich artefaktach).
4. Testy z atrapą HTTP: 401, 403, 429 z `Retry-After`, 500, ucięty JSON, odpowiedź HTML, nadmiarowe pola, timeout; dla każdego oczekiwany kod i brak zmyślonych danych.

**Kroki (decyzja; zadanie dla człowieka).** Uzyskać pisemne potwierdzenie mentora, że MiniMax przez `api.minimax.io` spełnia wymóg UE/EOG i open source, **albo** wybrać drugi model: pomiar na tych samych 25 sprawach (`llm-e2e/subset_dev.json`) u dostawcy z UE z kluczem użytkownika, reguła rozstrzygająca z `llm-e2e/PREREJESTRACJA.md` pkt 6. Dostarczyć osobny klucz dla jury z limitem ≥ 3× zużycia pełnego wsadu.

**Kryteria akceptacji.** Testy z atrapą zielone; `grep` kanarka po artefaktach: 0; self-check zwraca czytelny kod przy zablokowanym API; ADR-002 pkt 8 otwarty ponownie z dowodami.

## Zadania P1 (zwiększają F1 po Z01–Z04)

### ~~Z05. Słabe pola: czynność, numer BZP, imię pełnomocnika~~ (zrobione, bez `extract_poa`)

Reguły czynności i pola słabe w `domain/czynnosc.py` (`extract_act`, `find_bzp`, `validate_bzp`, `validate_representative_name`, `refine_appeal`), testy na 147 dokumentach rozwojowych i 8 + 8 lukach syntetycznych, mutacje 67/67. Replay 25 spraw: ΔF1 całości +0,018 [+0,013; +0,024], `numer_bzp` +0,364; opis i ograniczenia w `experiments/2026-11-21-wybor-modulow/produkt/E-czynnosc.md`. **Do zrobienia:** podłączenie `refine_appeal` do pipeline'u (Z01) i przeniesienie `extract_poa` (pola pełnomocnictwa) tylko jeśli pomiar pokaże zysk.

### Z06. Skany i strona zdominowana obrazem (S5)

**Cel.** S5 (poprawny obraz + błędna niewidoczna warstwa tekstu) daje F1 0,000 przy `complete`; skan kosztuje −0,083 F1. Warstwa tekstu takiej strony nie może wejść do wyniku.

**Przeczytaj.** `odczyt/BLOKERY.md` pkt 6, `odczyt/E04/README.md`, `E03/README.md`, `llm-e2e/E11/README.md` (S5: A 0,625, B 0,724, C 0,927, D 0,876 n=11: D nie wygrywa z C), `atak/E13/README.md` (detektor ukrytego tekstu 5/5 i 49/49 S5, 5/159 fałszywych alarmów), `harness/reading.py` (`read_document` dokleja słowa OCR do błędnej warstwy).

**Kroki.**
1. Diagnoza strony: gdy obraz pokrywa stronę (pokrycie > ok. 0,5) lub wykryto niewidoczny tekst (biały, 1 pt, poza MediaBox, tryb renderowania 3), strona jest „skanowa”: **pomiń warstwę PDF**, OCR strony, tekst z OCR.
2. Dla stron skanowych wyślij do LLM obraz strony (≤ 2000 px dłuższego boku) razem z tekstem OCR; porównaj z wariantem „tylko obraz” (C) na S5 i skanach (`odczyt/zestaw`, `llm-e2e/specs`); wybierz wariant regułą z prerejestracji (dolna granica ΔF1 > 0).
3. ~~Wykrywanie obrotu 90/180 jako warunek OCR (E03: +0,46 i +0,30)~~ (zrobione w adapterze `ocr/rapid.py`, z testami; podłączenie do silnika to Z01). Skos > 3° i zdjęcia telefonem są niezmierzone: dodaj do listy otwartej, nie implementuj deskew (szkodzi, −0,011).
4. Testy: dokument S5 z zestawu (`odczyt/ZESTAW.md`, `load_zestaw`) → wynik nie zawiera wartości z błędnej warstwy; strona tekstowa bez zmian (0 z 514 niepotrzebnie do OCR).

**Kryteria akceptacji.** S5 F1 ≥ ok. 0,90 (referencja C 0,927); brak regresji na stronach tekstowych; opis w `odczyt/E04` zaktualizowany.

### ~~Z07. Normalizatory (luki E19) i testy mutacyjne~~ (zrobione)

Luki E19 naprawione w `domain/normalize.py` (NIP/REGON/KRS z grupami, kwoty z separatorem tysięcy, daty: rok dwucyfrowy, miesiąc rzymski, `RRRR/MM/DD`, dzień słowny; TED ze spacjami), `rank_by_checksum` jako sygnał rankingowy (nie filtr), test obiegowy 55 wariantów E19 zielony, mutacje `normalize.py`: 291/291 zabitych (przed: 83 z 216 przeżyło; część przeżytych była mutantami równoważnymi i usunięto kod nadmiarowy). Szczegóły w `CHANGELOG.md`.

### Z08. Przebieg kontrolny, fizyczne skany, czas

**Cel.** Pierwszy wiarygodny wynik końcowy produktu i budżet czasu.

**Kroki.**
1. **Człowiek:** wydrukować i zeskanować (skaner biurowy, w tym kilka zdjęć telefonem) ok. 10 spraw **rozwojowych** (po jednym odwołaniu, pełnomocnictwie i przelewie), zapisać PDF-y w `experiments/2026-11-21-wybor-modulow/odczyt/fizyczne/` (nie commituj bez zgody, jeśli zawierają dużo danych) i przygotować referencję pól z oryginału sprawy.
2. **Agent:** zmierzyć F1 produktu na fizycznych skanach i na syntetykach tych samych spraw; różnica > 0,05 oznacza, że generator skanów jest nierealistyczny (zapisz wniosek w `odczyt/ZESTAW.md`).
3. **Agent:** pomiar czasu produktu w cichej maszynie (sprawdź `cut -d' ' -f1 /proc/loadavg` < 1,0 oraz `pgrep -fa venv-exp`): `process` na 60 sprawach (180 dokumentów), mediana i p95 na dokument, szczytowy RSS, osobno tekst i skan; metoda i skrypty: `experiments/2026-11-21-wybor-modulow/czas/` (jeśli pomiar nie był wykonany w ciszy, użyj czasu CPU i RSS). Wyniki: `czas/PODSUMOWANIE.md`.
4. **Agent, jednorazowo:** zbiór kontrolny: zapisz `WYBOR.md` (konfiguracja, model, prompt, skróty), uruchom `process` na sprawach kontrolnych (`data/podzial.json`, 11 spraw), oceń ewaluatorem, zwiększ licznik w `KONTROLNY.md`. Nie powtarzaj po zobaczeniu wyniku.

**Kryteria akceptacji.** Raport F1 z przedziałem per klasa i typ wejścia; potwierdzenie albo obalenie progów z oceny Fable (tekst ≥ 0,90, skan ≥ 0,85).

## Zadania P2

### Z09. Kotwiczenie cytatów i dowody (transparentność, GUI)

Odłączyć od treści JSON (E17: bbox jako warunek wartości obniża F1). Pliki: `harness/stages.py` (`WordAnchorResolver`), `odczyt/E05/README.md` (86% jednoznacznych w PDF, 73% poprawnych bbox w OCR). Kroki: cytat z kontekstem i zawężenie obrysu, rozstrzyganie duplikatów wartości na stronie przez kontekst (etykieta przed wartością), słowa OCR drobniejsze niż linia; wynik w `evidence.json` poza ocenianym JSON; flaga w raporcie dla niezakotwiczonych. Kryterium: ≥ 95% jednoznacznych na PDF bez wpływu na wartości w wyniku (test: wynik identyczny z kotwiczeniem i bez).

### Z10. ADR po eksperymentach

Napisać (każdy ze skutkami i odwołaniem do E##): ADR-006 (Z02), zmiana ADR-002 pkt 3 (przyjąć `pypdfium2`), pkt 4 (dostarczany OCR `rapidocr`; własny model dopiero po pobiciu go na tym samym zestawie), pkt 8 (otwarty ponownie: dowód UE/EOG i licencji albo drugi dostawca), pkt 12 i architektura §8 (cache poza zakresem do finału); adnotacje w `architektura-wewnetrzna.md` §3, §4.5, §5, §6, §10 (bbox nie decyduje o treści; `ambiguous` eksportuje najlepszą klasę; strona zdominowana obrazem: warstwa tekstu odrzucona); ADR-003: zakres testów mutacyjnych do terminu. Zasada z `AGENTS.md`: zmiana stosu = ADR z konsekwencjami; nie przepisuj historii, dodawaj adnotacje.

### Z11. Nowa klasa dokumentu z samego pliku konfiguracyjnego (punkty etapu 2)

Dziś YAML opisuje tylko model wyniku (`experiments/2026-11-21-yaml-klasy/`); router i prompt są pisane ręcznie pod trzy klasy. Cel: prompt, sygnały routera i serializer generowane z pliku klasy. Kroki: zdefiniuj schemat pliku klasy (nazwa, pola z typami i normalizatorami, sygnały routera, opis dla promptu), generuj prompt z pliku, dodaj czwartą klasę demonstracyjną **tylko przez nowy plik** i test, że `process` ją obsługuje bez zmiany kodu Pythona. Kryterium: test end-to-end z nową klasą na atrapie LLM.

### Z12. Utwardzenie produktu (z wyników ataku E12–E16)

Dotyczy tylko tego, co produkt faktycznie zawiera (CLI). Kolejność: (1) parser i render PDF w procesie potomnym z limitem pamięci i czasu (`atak/E12` B02, B03, B08: samoodwołujący się XObject ubija proces przy 6 GB w ok. 24 s) i limit pikseli na stronę; (2) detektor ukrytego tekstu i reguły kodu odporne na posłusznego LLM (`atak/E13`: atrapa wykonuje 5 z 6 ataków; zmiana klasy na `foreign` zeruje wszystkie pola); (3) walidacja `base_url`, jeden nagłówek klucza, limity budżetu (`atak/E14` C02, L02, L03); (4) przy późniejszym API HTTP: Host/Origin, limit ciała, trwały stan wsadu, limit kolejki (`atak/E12` P05, F01; `E15` W03, Q01). Każdy punkt jako test w `tests/` (skrypty ataku w `atak/E12..E16` są gotowymi przypadkami).

### Z13. Dług testów mutacyjnych w `db/` i zakres mutacji

`db/repository.py` 8 z 17 przeżyło, `db/data_repository.py` 21 z 63. `DataRepository` nie jest na ścieżce CLI (Fable), więc najpierw decyzja użytkownika o zakresie (zmiana ADR-003), potem testy zabijające mutanty. Nie omijaj hooków.

### Z14. API HTTP i GUI minimum (po działającym CLI)

Tylko po Z01–Z03. Cztery trasy: wgranie, stan, wynik, dowody (`openapi.yaml` najpierw, skill `generate-api`; uprząż `harness/server.py` jako wzorzec, nie kopiuj jej luk, Z12). GUI: jedna strona (wgranie, JSON, obraz strony). Bez `DataRepository` dla CLI.

### Z15. Apache Tika (niski priorytet)

Wstępna ocena (niezweryfikowana, sieć nie działała): wymaga Javy i pobiera serwer JAR przy starcie, nie daje bbox słów, OCR przez Tesseract (binarka systemowa), a `pypdfium2` znalazł 1454/1454 wartości (E01). Jedyna zasadna rola: fallback dla uszkodzonych PDF. Jeśli chcesz to sprawdzić: pobierz dokumentację (`npx ctx7@latest library "Apache Tika" "..."`), uruchom Tikę na 206 PDF-ach i na wejściach z `atak/E12` i porównaj z pdfium (tekst, bbox, czas, RSS); zapisz w `odczyt/E01/tika.md`. Decyzja o wprowadzeniu wymaga ADR.

## Do rozstrzygnięcia przez człowieka (agent nie rozstrzyga)

1. **LLM i klucz (P0):** zgoda mentora na MiniMax albo drugi dostawca z UE; osobny klucz jury z zapasem limitu (patrz Z04).
2. **Pytania do mentora lub organizatora:** (1) czy MiniMax (`api.minimax.io`, podmiot, serwery, licencja wag) spełnia „open source” i „UE/EOG”; (2) jak liczy ewaluator: agregacja, błędna wartość jako FP czy FP+FN (ADR-005), brakujący klucz a `null`, pusta lista, brak pliku; (3) jak powstały skany i dokumenty mieszane w teście i jaki mają udział; (4) jak rozmiar modelu przekłada się na punkty (całkowite czy aktywne parametry, czy OCR się liczy); (5) jak jury uruchomi rozwiązanie (system operacyjny, polecenie, liczba dokumentów, kanał klucza, jeden przebieg).
3. **Czytnik PDF:** zatwierdzenie `pypdfium2` wbrew ADR-002 pkt 3 (wymagane przed Z01 w wersji końcowej).
4. **Zakres mutacji do terminu** (ADR-003, Z13) i **usunięcie `.github/workflows/docs.yml`** (CI jest lokalne).
5. **Windows:** uruchomienie `run.sh`/`start.bat`/`verify_install.py` na Windows (agent zdalny tego nie sprawdzi).
6. **Fizyczne skany** ok. 10 spraw (Z08, krok 1).
7. **Dostęp jury do repozytorium** (konta, U-Q09).

## Porządki techniczne (małe, można zrobić od ręki)

- ~~`README.md` w korzeniu: wersja 0.4.0 i zdanie „aplikacja nie została zaimplementowana”~~ — poprawione w Z03; po Z01 zaktualizować sekcję stanu.
- Podciągnąć lokalny `main` (`git -C <katalog głównego checkoutu> merge --ff-only origin/main`) po zakończeniu pracy równoległych agentów.
- Sprawdzić, czy gałęzie `kacperpaczos/*` zmergowane do `main` można usunąć zdalnie (po potwierdzeniu użytkownika).
- Katalog `czas/` w eksperymentach: dopisać wyniki T5 i T6 po zakończeniu pomiaru (patrz `czas/PODSUMOWANIE.md`).
