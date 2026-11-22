---
wersja: 0.1.0
aktualizacja: 2026-11-21
status: lista prac do realizacji; stan faktyczny ustal w kodzie i testach
---

# Backlog i znane długi

Kolejność wynika z [warunków wejścia do implementacji](../04-architektura/architektura-wewnetrzna.md) (§1) i [pomiaru jako wymagania](../04-architektura/architektura-wewnetrzna.md) (§11). Pozycja jest ukończona dopiero po dowodzie z kolumny „Dowód”. Zanim zaczniesz, sprawdź w kodzie, czy pozycja nie została już zrobiona.

## Definicja ukończenia (każde zadanie)

1. Test napisany przed kodem; nazwy testów po angielsku.
2. `python3 scripts/ci.py --stage all` zielone: docs, lint, typy, API, testy, mutacje (zasady: [lokalne CI/CD](lokalne-ci-cd.md), [AGENTS.md](../../AGENTS.md)).
3. Zmiana kontraktu idzie najpierw do `openapi.yaml` (skill `generate-api`); zmiana stosu ma ADR.
4. Małe, atomowe commity; osobna gałąź na zadanie; merge dopiero po zielonym CI.

## Kolejka (priorytet malejący)

| Nr | Zadanie | Dowód ukończenia | Zależy od |
|---|---|---|---|
| 1 | Loader 60 spraw: referencje organizatora z poprawkami, mapowanie `potwierdzenie_przelewu.pdf` ↔ `przelew.json`, nazwa wyniku według wejścia | test na wszystkich 60 sprawach, oryginały nienaruszone | — |
| 2 | Ewaluator TP/TN/FP/FN per pole, klasę i dokument; F1 = `2*TP/(2*TP+FP+FN)`, osobno klasyfikacja, struktura, dowody | testy z ręcznie policzonymi przypadkami, raport JSON | 1 |
| 3 | CLI `input` → `output` na atrapie silnika: drzewo katalogów, `{}` dla obcego, błędy, atomowość, niezależność dokumentów | testy CLI, kody wyjścia 0/1/2 | 1 |
| 4 | Zamrożenie zestawu rozwojowego i kontrolnego (podział po całych sprawach i rodzinach duplikatów) | plik podziału w repo, test niezmienności | 1 |
| 5 | OpenAPI v1: `system`, `batches`, `jobs`, `documents`, `diagnosis`, `result`, `evidence`, `report`, `classes`, `codes`; błędy RFC 7807 | `validate_api.py --stage all`, test kontraktowy | 3 |
| 6 | Kontrakt odczytu i OCR (`Reading`, `OcrRequest/Response`) z bbox; wymienny dostawca, dostawca `none` | testy mapowania narożników, brak OCR daje `ocr_unavailable` | 5 |
| 7 | Zastępczy czytnik PDF i OCR za kontraktem; pomiar na rasteryzacji 60 spraw | raport czasu i dokładności; wybór czytnika zatwierdza użytkownik | 6 |
| 8 | Klient LLM: protokoły OpenAI i Anthropic, konfiguracja, self-check, ograniczone ponowienia, bez cache przy awarii | testy z atrapą HTTP, wstrzykiwanie awarii 401/403/429/sieć | 5 |
| 9 | Ścieżka pionowa E, L, T1, T3, T5: przelew, potem pełnomocnictwo i odwołanie; kotwiczenie cytatów w słowach z bbox | F1 na zbiorze rozwojowym, raport per klasa | 2, 7, 8 |
| 10 | Testy mutacyjne regex i walidatora (obowiązek ADR-002 pkt 6) | zero przeżytych mutantów w zakresie | — |
| 11 | GUI P0: wgranie i przegląd, dowód strona + cytat + bbox, pobranie JSON, karty modeli i gotowość OCR | działa na CLI/API, bez serwera Node | 5, 9 |

Rozszerzenia T2, T4, analiza regionów włączamy tylko po poprawie F1 na zbiorze rozwojowym (architektura §3).

## Zadania z eksperymentów (2026-11-22)

Źródło: [raport wyboru modułów](../../experiments/2026-11-21-wybor-modulow/RAPORT.md). To hipotezy z uprzęży i zbioru rozwojowego, nie fakty o produkcie; każda wymaga testu i ADR.

| Nr | Zadanie | Dowód ukończenia |
|---|---|---|
| E-1 | Nie ufać warstwie tekstu stron zdominowanych przez obraz (S5: poprawny skan z błędną niewidoczną warstwą daje F1 0,000 przy `complete`): obraz strony do LLM albo kontrola zgodności warstwy z OCR próbki | test S5 w produkcie, F1 S5 ≥ wariant z obrazem (E11) |
| E-2 | Polityka braków: eksportować `partial` z flagą, nie zerować pola bez kotwicy, bbox nie decyduje o treści JSON (E17: −0,021 i −0,208 F1) | zmiana architektury §4.5/§10 i ADR |
| E-3 | Parser PDF w procesie potomnym z limitem pamięci i czasu (samoodwołujący się XObject ubija serwer) | test bomby PDF kończy się `technical_error`, serwer żyje |
| E-4 | Backend: walidacja Host/Origin, limit ciała żądania, jeden nagłówek klucza LLM i walidacja `base_url`, limit budżetu wywołań, trwały stan wsadu po `kill -9`, limit kolejki | testy z E12–E15 przeniesione do produktu |
| E-5 | Normalizatory: NIP/REGON/KRS ze spacjami i myślnikami, kwota `1.000,50`, daty skrócone i rzymskie miesiące; sumy kontrolne tylko jako sygnał | testy E19, zero przeżytych mutantów |
| E-6 | OCR konfigurowany w pikselach dłuższego boku; wykrywanie obrotu tak, deskew i binaryzacja nie | test konfiguracji, wynik E03 |
| E-7 | Kotwiczenie cytatów: cytat z kontekstem, słowa OCR drobniejsze niż linia (dziś 86% jednoznacznych na PDF, 73% poprawnych bbox na OCR) | ≥ 95% jednoznacznych na rozwojowym |
| E-8 | Dokończyć brakujące eksperymenty: pomiar czasu w cichej maszynie, wariant D na skanach (57 z 150), zbiór kontrolny (jeden przebieg), fizyczne skany ok. 10 spraw, drugi dostawca LLM | raport uzupełniony; licznik użyć zbioru kontrolnego |

## Znane długi

| Dług | Szczegóły | Jak naprawić |
|---|---|---|
| Przeżyłe mutanty | `normalize.py` 83 z 216, `db/repository.py` 8 z 17, `db/data_repository.py` 21 z 63 (pomiar `ci.py --stage mutation`) | testy zabijające mutanty: wagi PESEL, miesiące, wzorce dat; osobna gałąź na plik |
| Dwa repozytoria danych | stary `CatalogRepository` obok `SqliteDataRepository` | decyzja użytkownika: zachować czy usunąć |
| Semantyka `payload` | tekst JSON czy napis | decyzja użytkownika, zapis w ADR |
| Kontrakt OpenAPI | `openapi.yaml` opisuje schematy dokumentów i `/healthz`, bez zasobów v1 | zadanie 5 |
| Hooki | `pre-commit` wymaga jednorazowo `sh scripts/install_hooks.sh` | uruchomić po sklonowaniu |
| Interpretacja F1 | błędna wartość jako FP bez FN, algorytm podobieństwa 80% (domyślnie `ratio`) i parowanie list są przyjęte roboczo ([ADR-005](../07-decyzje/ADR-005-interpretacja-f1.md)) | potwierdzić z mentorem (U-Q01, U-Q02), zmienić domyślne `EvalConfig` |
| Workflow GitHub | `.github/workflows/docs.yml` pozostał, choć CI działa lokalnie | decyzja użytkownika: usunąć |

## Pytania blokujące decyzje

Zamknięte i otwarte pytania do mentora: [pytania otwarte](../07-decyzje/pytania-otwarte.md). Nie zamykaj ich w kodzie; odpowiedzi nie cofają automatycznie decyzji zespołu.
