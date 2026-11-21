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
