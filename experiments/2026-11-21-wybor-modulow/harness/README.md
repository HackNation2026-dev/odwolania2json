# Uprząż eksperymentalna: pomiar modułów przez HTTP

Wspólna infrastruktura eksperymentów E01–E16 ([plan](../../../docs/05-weryfikacja/plan-eksperymentow-wyboru-modulow-2026-11-21.md)).
To warstwa pomiarowa w `experiments/`, **nie produkcja i nie kontrakt**: trasy idą w kierunku OpenAPI v1, ale `openapi.yaml`
ich jeszcze nie zawiera. Nie zmienia `apps/`, `packages/` ani `docs/`; z backendu produkcyjnego tylko importuje
`loader`, `dataset`, `evaluator` i `domain.normalize` (tylko odczyt). Środowisko i wyniki instalacji: [ENV.md](ENV.md).

## Uruchomienie (jedno polecenie na wszystko)

Z korzenia repozytorium, w środowisku `.venv-exp`:

```sh
cd experiments/2026-11-21-wybor-modulow
../../.venv-exp/bin/python harness/run_experiment.py harness/examples/E00-smoke-pdfium.json     # tekst, bez OCR, ok. 1 s
../../.venv-exp/bin/python harness/run_experiment.py harness/examples/E00-szablon-skan-ocr.json # skan z OCR, ok. 25 s
```

Każde polecenie: startuje serwer jako podproces pod limitem 14 GB, wgrywa dokumenty przez HTTP, zbiera wyniki, zapisuje
`wyniki/E00/<wariant>.json` i `wyniki/E00/README.md` (jak działa i dlaczego, tabela wariantów).

Testy (99, w tym wolne z prawdziwym OCR i podprocesem serwera):

```sh
cd experiments/2026-11-21-wybor-modulow/harness && ../../../.venv-exp/bin/python -m pytest
```

Samodzielny serwer i klient:

```sh
../../../.venv-exp/bin/python server.py --port 8765 [--config wariant.json]   # tylko 127.0.0.1, bez uwierzytelniania
HARNESS_OCR=rapidocr HARNESS_EXTRACTOR=llm ../../../.venv-exp/bin/python server.py   # warianty ze zmiennych środowiskowych
```

```python
from client import ManagedServer, HarnessClient
with ManagedServer("wariant.json") as srv, HarnessClient(srv.url, server=srv) as c:
    r = c.run_document("plik.pdf")   # health → upload → czekanie → result/evidence/report/diagnosis/metrics
    r["state"], r["timing"], r["peak_rss_mb"], r["limit_method"]
```

## Trasy backendu

| Trasa | Opis |
|---|---|
| `GET /health` | żywotność procesu |
| `GET /system` | gotowość OCR i LLM, metadane modeli, konfiguracja (bez klucza), limity; nie wykonuje płatnego wywołania |
| `POST /batches` | multipart `files` (wiele PDF-ów); zwraca `batch_id`, `document_id` (pierwszy), `document_ids`, `documents` |
| `GET /batches/{id}` | dokumenty wsadu i flaga `done` |
| `GET /documents/{id}` | `progress`: queued/running/done; `outcome`: complete/partial/foreign/ambiguous/technical_error/null; `stage`, `class_id`, `codes`, `errors[]` |
| `GET /documents/{id}/result` | JSON w kluczach organizatora; **409** `result_unavailable` dla `technical_error`/`ambiguous`, **409** `not_ready` przed końcem |
| `/evidence`, `/report`, `/diagnosis` | dowody (strona, cytat, słowa, bbox), raport braków, diagnoza stron |
| `/metrics`, `/artifact/{ścieżka.json}` | rozszerzenia harnessu: czasy etapów; dowolny artefakt przebiegu (np. `raw/reading.json`, `t1/router.json`, `t3/ai-response.json`) |

Błędy techniczne są jawne: dokument kończy `done/technical_error` z kodem z architektury §6 (`pdf_corrupted`, `pdf_encrypted`,
`ocr_unavailable`, `ocr_error`, `llm_*`, `time_limit`, `write_failed`, `invalid_configuration`, …) oraz kilkoma rozszerzeniami
harnessu (`upload_too_large`, `page_limit`, `not_a_pdf`, `empty_document`, `internal_error`). Serwer nie pada przy złym wejściu.
Skan bez OCR to `technical_error/ocr_unavailable`, nigdy `foreign`. Wynik jest zapisywany atomowo (plik tymczasowy, fsync,
`os.replace`) w `work_dir/<batch>/documents/<doc>/runs/r1/…` (układ z architektury §7, uproszczony do jednego przebiegu).

## Konfiguracja wariantu (`config.py`)

Plik JSON i/lub zmienne `HARNESS_<POLE>` (zmienne wygrywają; zagnieżdżone: `HARNESS_LLM_MODEL`, `HARNESS_LIMITS_MAX_PAGES`).

| Pole | Wartości | Znaczenie |
|---|---|---|
| `pdf_reader` | `pdfium` | czytnik warstwy tekstowej |
| `ocr`, `ocr_dpi`, `ocr_policy` | `none` / `rapidocr`; dpi; `if_needed` / `always` / `never` | OCR i kiedy go wołać |
| `router` | `rules` / `llm` | klasyfikacja dokumentu |
| `extractor` | `rules` / `llm` / `none` | pola (`rules`: wąska linia bazowa dla pól o stałym formacie) |
| `anchor` | `words` | cytat → słowa → bbox |
| `llm.*` | `protocol` (`anthropic`/`openai`/`mock`), `base_url`, `model`, `key_file`, `temperature`, `max_tokens`, `timeout_s`, `retries`, `effort` | klient LLM |
| `limits.*` | `max_upload_bytes`, `max_pages`, `document_timeout_s`, `max_workers`, `max_batch_documents` | limity |

## Interfejsy modułów (jak dopisać wariant bez zmian w harnessie)

Protokoły w `stages.py` (dane to słowniki JSON zgodne z architekturą §4):

```python
class Router:        name; route(reading, diagnosis, document_id) -> ClassDecision   # decision: classified|foreign|ambiguous|technical_error
class Extractor:     name; extract(reading, class_id) -> Extraction(findings=[Finding(field, value, quote, page, method)], ai_response, notes)
class AnchorResolver: name; resolve(reading, quote, page|None) -> {"status": anchored|unanchored|ambiguous, "evidence": [...], "candidates": n}
```

`Reading` ma strony ze słowami (`id`, `text`, `bbox` w punktach, układ po `/Rotate`, `source` pdf/ocr, `line_id`, `confidence`),
liniami, obrazami i `to_pdf`. Czytnik PDF (`reading.PdfReader`) i OCR (`reading.OcrProvider`, `none` albo `rapidocr`) mają własne protokoły.
Ekstraktor zwraca wartość i **cytat**; współrzędne wyznacza kod: pipeline kotwiczy cytat i tworzy `Evidence`. Cytat bez jednoznacznej
kotwicy daje `review_required`, kod `evidence_unanchored` i wynik `partial` (nigdy `complete`).

Rejestracja: moduł wskazany w `HARNESS_PLUGINS` (lista po przecinku, importowany przy starcie serwera i CLI) woła
`stages.register("router"|"extractor"|"anchor", "nazwa", lambda cfg, llm: obiekt)`; wariant wybiera pole konfiguracji.
Własny sposób pomiaru: `run_experiment.register_runner("nazwa", fn(spec, ctx) -> dict)` albo `"runner": "modul:funkcja"`.
Gotowy runner `e2e` robi wgranie przez HTTP, porównanie z referencją i agregaty (macierz pomyłek klas, wyniki, kody błędów, czas, F1 liści).

## Dane (`data.py`)

`load_items("dev"|"cases-dev"|"control"|"negatives"|"template"|"all")`: pary PDF ↔ referencja z poprawkami organizatora (nakładane w pamięci),
podział z `data/podzial.json`. `dev` zawiera negatywy (do strojenia routera), `control` ich nie zawiera. Zbiór kontrolny wymaga w konfiguracji
`"confirm_control": true` (strojenie tylko na rozwojowym; kontrolny raz, na końcu). Kopie robocze w `harness/work/data/` z weryfikacją SHA-256;
oryginały nietknięte. Warianty brzegowe (`variant_names()`): `rot90/180/270`, `skew3`, `lowres72`, `noise`, `jpeg30`, `mixed`,
`raster100/150/200/300`; deterministyczne dla ziarna (stała data w PDF), rejestr pochodzenia w `variants.json`.
W konfiguracji eksperymentu: `"variant_kinds": ["raster150", "rot90"]`.

## LLM (`llm.py`)

Protokół Anthropic (domyślnie MiniMax `https://api.minimax.io/anthropic/v1/messages`, `MiniMax-M3.1-Flash-Preview`) i OpenAI-zgodny.
Klucz z pliku (`llm.key_file` → `MINIMAX_KEY_FILE` → `~/kluczMiniMaxKacper`), czytany przy wywołaniu; nie jest logowany ani zapisywany,
a komunikaty błędów są z niego oczyszczone. 401/403 bez ponowień; 429/5xx/timeouty z ograniczonym budżetem prób i narastającym odstępem. Kody:
`llm_unavailable`, `llm_authorization`, `llm_rate_limit`, `llm_invalid_response`. `LlmStats` zlicza wywołania, ponowienia, tokeny i czas.
`MockLlm` (protokół `mock`) to atrapa HTTP ze skryptem zachowań (`ok`, `status`, `timeout`, `connect`, `truncated`, `garbage`, `empty`, `no_content`)
do testów i E14.

## Pomiar zasobów

`ManagedServer` uruchamia serwer pod `systemd-run --user --scope -p MemoryMax=14G` (zapas: `prlimit --as`, potem brak limitu; metoda jest w każdym wyniku).
Szczytowy RSS to `VmHWM` procesu serwera, czas ścienny mierzy klient. `run_experiment` bierze `flock /tmp/uzp-cpu.lock` (`fcntl.flock`, zgodne z
poleceniem `flock`) na czas pomiaru, gdy `"timing": true`; `--no-lock` wyłącza to i unieważnia wyniki czasu (`timing_locked: false` w pliku).

## Znane ograniczenia i uwagi dla kolejnych eksperymentów

- Ewaluator produkcyjny nie zlicza `tp` dla pól (trafione pole to `tn`), więc jego F1 pól zawsze wynosi 0; harness podaje obok `aggregates.leaf_f1`
  (multizbiór niepustych liści). Żadna miara nie jest oficjalnym wynikiem.
- Router regułowy i ekstraktor regułowy to linie bazowe (E06–E08 poprawią je strojeniem). Na 192 dokumentach zbioru (60 spraw × 3 klasy + 12 negatywów) router regułowy
  (bez OCR) nie pomylił klasy, ale zwraca `ambiguous` dla części dokumentów (0 pomyłek klas, 22 dokumenty `ambiguous`, 3 skany negatywów `technical_error`).
- Kotwiczenie dopasowuje cytat do słów strony na znakach; obrys obejmuje całe dotknięte słowa. OCR nie wykrywa obrotu skanu (E03).
- Jeden `run_id` (`r1`) na dokument; brak ponowienia, cache i restartowej odbudowy stanu (E15 wymaga własnego runnera).
- PDFium nie jest bezpieczny wątkowo: czytnik jest serializowany blokadą, a OCR i LLM biegną współbieżnie (`limits.max_workers`).
