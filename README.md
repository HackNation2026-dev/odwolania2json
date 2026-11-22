# Odwołania2JSON — UZP

Konwerter PDF-ów spraw odwoławczych (odwołanie, pełnomocnictwo, przelew) do ścisłego JSON. Rozwiązanie na HackNation 2026 (zadanie Urzędu Zamówień Publicznych). Repozytorium prywatne; organizacja docelowa: `HackNation2026-dev`.

## Stan implementacji (sprawdzony w kodzie)

> **Polecenie `process` obsługuje PDF-y tekstowe, skany i dokumenty mieszane.** Czytnik diagnozuje strony, a LLM dostaje odczytany tekst do rozpoznania klasy i pól. Wynik przechodzi normalizację i zapis JSON według wzorców organizatora. Wyniki i błędy wsadu opisuje `report.jsonl` ([ADR-006](docs/07-decyzje/ADR-006-polityka-eksportu.md)).
>
> **OCR działa domyślnie.** Dla strony bez wiarygodnej warstwy tekstu `process` używa wyniku RapidOCR. Ustaw `OCR_ENABLED=0`, aby wyłączyć OCR. Strony wymagające wyłączonego lub niedostępnego OCR dostają w raporcie kod `ocr_unavailable`.
>
> Liczby jakości (F1 przybliżony) dla produktu: [E-produkt](experiments/2026-11-21-wybor-modulow/produkt/E-produkt.md); pozostałe pochodzą z uprzęży pomiarowej w `experiments/`: [raport eksperymentów](experiments/2026-11-21-wybor-modulow/RAPORT.md).

`requirements.txt` zawiera wyłącznie zależności uruchomieniowe, przypięte (`==`), z OCR (`rapidocr`, `onnxruntime` w wersji CPU) i pakietami lokalnymi instalowanymi bez `-e`. Narzędzia deweloperskie (pytest, ruff, mypy, generatory kontraktu) są w `requirements-dev.txt`.

## Klucz API

Aplikacja czyta konfigurację LLM ze zmiennych środowiskowych. **Klucza nie zapisuj w repozytorium ani w plikach śledzonych przez Git** (`.env` jest w `.gitignore`). Klucz nie trafia do logów, komunikatów błędów ani raportu.

| Zmienna | Znaczenie |
|---|---|
| `LLM_API_KEY` | klucz API dostawcy; zamiast niego można podać `LLM_API_KEY_FILE` (ścieżka do pliku z kluczem poza Git) |
| `LLM_BASE_URL` | adres API, np. `https://adres-api/v1` (protokół OpenAI) albo pełny adres `/v1/messages` (protokół Anthropic); tylko `https` |
| `LLM_MODEL` | nazwa modelu |
| `LLM_PROTOCOL` | `openai` albo `anthropic`; gdy brak, wynika z adresu (ścieżka z `anthropic` → `anthropic`, inaczej `openai`) |
| `LLM_ALLOWED_HOSTS` | lista hostów (po przecinku), do których wolno wysłać klucz i treść dokumentów; domyślnie `api.minimax.io`. Inny host trzeba tu dopisać, inaczej start kończy się błędem `invalid_configuration` |
| `LLM_MAX_CALLS`, `LLM_MAX_TOTAL_TOKENS` | limit wywołań (domyślnie 1000) i tokenów na jeden wsad, łącznie dla dostawcy głównego i zapasowego |
| `LLM_MAX_OUTPUT_TOKENS`, `LLM_TIMEOUT_S`, `LLM_MAX_RETRIES` | limit wyjścia modelu, limit czasu żądania i liczba ponowień sieciowych (domyślnie 3) |
| `ERROR_EXPORT` | `empty_json` (domyślnie: błąd techniczny dokumentu → `{}`) albo `no_file` |

```sh
export LLM_API_KEY=...   LLM_BASE_URL=https://adres-api/v1   LLM_MODEL=nazwa-modelu    # Linux/macOS
set LLM_API_KEY=...      & set LLM_BASE_URL=https://adres-api/v1 & set LLM_MODEL=nazwa-modelu   # Windows cmd
```

Przed wsadem program wykonuje jedno krótkie wywołanie próbne (self-check). Odrzucony klucz (401/403), wyczerpany limit (429) albo zły adres kończą pracę kodem 2 z komunikatem, bez przetwarzania wsadu. Bez terminala brak klucza jest jawnym błędem; w terminalu program zapyta o klucz z ukryciem znaków.

### Próba pomiaru MiniMax

Podaj ścieżkę do pliku z aktywnym kluczem API poza repozytorium. Osobny katalog pomiaru rozdziela wyniki różnych wersji modelu.

```sh
python scripts/eval_process.py \
  --protocol anthropic --base-url https://api.minimax.io/anthropic/v1/messages \
  --model MiniMax-M3.1-Flash --key-file "$MINIMAX_KEY_FILE" \
  --work .ci/eval-minimax-m31-flash --max-docs 10 --call-budget 200
```

### Dostawca zapasowy (opcjonalny)

Gdy dostawca główny zawiedzie po wyczerpaniu ponowień (429, 5xx, sieć lub limit czasu, 402, odrzucone żądanie, 401/403), dokument trafia do dostawcy zapasowego ([ADR-007](docs/07-decyzje/ADR-007-zapasowy-dostawca-llm.md)). Odpowiedź poza schematem najpierw dostaje ponowienie u tego samego dostawcy. Raport `report.jsonl` zapisuje dla każdego dokumentu, który dostawca i model odpowiedział, oraz powód przełączenia; odrzucony klucz dostawcy głównego zostawia ostrzeżenie `llm_primary_unauthorized`.

| Zmienna | Znaczenie |
|---|---|
| `LLM_FALLBACK_BASE_URL` | adres API dostawcy zapasowego; **brak wartości domyślnej**, brak zmiennej = brak zapasu. Host musi być w `LLM_ALLOWED_HOSTS` |
| `LLM_FALLBACK_MODEL`, `LLM_FALLBACK_PROTOCOL` | model i protokół (`openai` \| `anthropic`) |
| `LLM_FALLBACK_API_KEY` albo `LLM_FALLBACK_KEY_FILE` | klucz albo plik z kluczem poza Git |
| `LLM_FALLBACK_USER_AGENT` | nagłówek `User-Agent`; domyślnie `odwolania2json/<wersja>` |
| `LLM_FALLBACK_HEADERS` | obiekt JSON z nagłówkami dodatkowymi; `{session}` w wartości to identyfikator bieżącego uruchomienia (jeden UUID na proces) |
| `LLM_PROVIDER_COOLDOWN_S` | ile sekund dostawca odpoczywa po błędzie przejściowym (domyślnie 300) |

Przykład (GLM przez OpenCode, plan Go; klucz tylko w pliku):

```sh
export LLM_ALLOWED_HOSTS=api.minimax.io,opencode.ai
export LLM_FALLBACK_BASE_URL=https://opencode.ai/inference/go/openai/v1
export LLM_FALLBACK_MODEL=glm-5.3-flash LLM_FALLBACK_PROTOCOL=openai
export LLM_FALLBACK_KEY_FILE=~/kluczOpenCodeGLM
export LLM_FALLBACK_HEADERS='{"x-opencode-session": "{session}"}'
```

**Ryzyka dostawcy zapasowego (decyzja człowieka, nie programu):** zgodność z wymogiem konkursu „firma i serwery w UE/EOG, model open source” jest dla tego dostawcy **nieznana**; plan Go jest przeznaczony dla agentów kodujących, a ruch jest monitorowany przez dostawcę, więc użycie go do wsadów dokumentów obciąża konto użytkownika. Program przedstawia się własną nazwą (`User-Agent`) i nie udaje innego klienta. Błędna konfiguracja zapasu to tylko ostrzeżenie: wsad działa wtedy na dostawcy głównym.

## Struktura wyniku

Dla każdego `input/<ścieżka>/<nazwa>.pdf` (także `.PDF`) powstaje `output/<ścieżka>/<nazwa>.json` (ta sama nazwa i drzewo katalogów). Dokument obcy (niezaliczony do żadnej z trzech klas) dostaje pusty plik `{}`. Dokument z błędem technicznym też dostaje `{}`, a przyczynę zapisuje `output/report.jsonl` (jeden wiersz na plik wejściowy: stan, klasa, kody błędów, strony nieprzetworzone, flagi pól, dostawca LLM; bez treści dokumentów i bez kluczy). Zapis jest atomowy (plik tymczasowy, `fsync`, zamiana), więc przerwany przebieg nie zostawia pół-pliku. Błędu nigdy nie zastępuje się zmyślonymi danymi.

```
input/                          output/
└── sprawa1/                    └── sprawa1/
    ├── odwolanie.pdf               ├── odwolanie.json
    └── przelew.pdf                 └── przelew.json
```

Katalogi `input/` i `output/` są w repozytorium z plikiem `.gitkeep`, a ich zawartość jest ignorowana przez Git.

## Kody wyjścia

| Kod | Znaczenie |
|---|---|
| 0 | wszystkie dokumenty przetworzone |
| 1 | błąd techniczny albo strony nieprzetworzone w co najmniej jednym dokumencie (pozostałe są przetworzone; błędny dostaje `{}`, szczegóły w `report.jsonl` i na stderr) |
| 2 | błąd użycia, konfiguracji albo self-check LLM: brak katalogu wejściowego, brak klucza, odrzucony klucz, wyczerpany limit; wsad nie jest przetwarzany. Także brak Pythona 3.13+ w skrypcie startowym |

## Rozwiązywanie problemów

| Objaw | Przyczyna i działanie |
|---|---|
| `błąd: potrzebny Python 3.13+` | zainstaluj Pythona 3.13 albo ustaw zmienną `PYTHON` na jego ścieżkę |
| `No matching distribution found for onnxruntime` | Python inny niż 3.13 lub system bez kół (np. ARM Linux); użyj 3.13 na x86-64 |
| błąd instalacji przy braku sieci | `pip install` wymaga PyPI; po instalacji sieć nie jest potrzebna dla OCR |
| katalog `input/` pusty | skrypt kończy się kodem 0 bez wyników; wgraj PDF-y |
| kod 2 i `błąd: llm_authorization` / `llm_rate_limit` | klucz odrzucony albo limit konta wyczerpany: popraw `LLM_API_KEY` lub skonfiguruj dostawcę zapasowego |
| kod 2 i `błąd: invalid_configuration` | sprawdź `LLM_BASE_URL` (https), `LLM_MODEL`, `LLM_PROTOCOL`; host spoza listy dopisz do `LLM_ALLOWED_HOSTS` |
| same `{}` w `output/` i kod 1 | otwórz `output/report.jsonl`: kod błędu jest przy każdym pliku (`ocr_unavailable` = skan bez OCR, `llm_*` = problem z modelem) |

## Sprawdzenie czystej instalacji

```sh
python3 scripts/verify_install.py --python python3.13
```

Skrypt tworzy tymczasowe środowisko, instaluje `requirements.txt` z PyPI, sprawdza obecność wag OCR w kole i uruchamia `process` na trzech małych PDF-ach z lokalną atrapą LLM (`LLM_BASE_URL` wskazuje na `127.0.0.1`). Kody: 0 OK, 1 błąd, 3 SKIP (brak sieci do PyPI; jawnie, nie jako sukces). Test pytest: `O2J_VERIFY_INSTALL=1 python -m pytest tests/unit/test_delivery.py -m slow_install`.

**Windows.** W PowerShellu w katalogu repozytorium uruchom:

```bat
py -3.13 scripts\verify_install.py
.\start.bat
```

Pierwsze polecenie sprawdza instalację; wynik `OK instalacja`, `OK wagi OCR`, `OK process` oznacza powodzenie. Zgłoś wynik w zadaniu Z03.

## Dla deweloperów

```sh
python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements-dev.txt
sh scripts/install_hooks.sh
python3 scripts/verify_docs.py
python scripts/ci.py --stage all
```

Zasady pracy: [AGENTS.md](AGENTS.md), [lokalne CI/CD](docs/00-organizacja/lokalne-ci-cd.md), [zadania dla agentów](docs/00-organizacja/zadania-dla-agentow.md), [backlog](docs/00-organizacja/backlog.md).

## Dokumentacja

1. [Indeks dokumentacji](docs/README.md)
2. [Zadanie](docs/01-zadanie/README.md)
3. [Materiały i pochodzenie](docs/02-materialy/README.md)
4. [Wymagania i odbiór](docs/03-wymagania/README.md)
5. [Architektura i stos](docs/04-architektura/README.md)
6. [Weryfikacja](docs/05-weryfikacja/README.md)
7. [Prezentacja i zgłoszenie](docs/06-prezentacja/README.md)
8. [Decyzje i pytania](docs/07-decyzje/README.md)

Oryginały organizatora w `docs/02-materialy/` są niezmienne; opracowania zespołu leżą poza nimi. Historia zmian: [CHANGELOG](CHANGELOG.md), zasady: [wersjonowanie](docs/00-organizacja/wersjonowanie.md).

## Dostęp i sekrety

Repo ma pozostać prywatne. Klucze API przekazuj jury osobno; aplikacja czyta je ze środowiska. Dane referencyjne pozostają materiałem organizatora. Repo nie nadaje im nowej licencji.
