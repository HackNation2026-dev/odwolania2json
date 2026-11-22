# Odwołania2JSON — UZP

Konwerter PDF-ów spraw odwoławczych (odwołanie, pełnomocnictwo, przelew) do ścisłego JSON. Rozwiązanie na HackNation 2026 (zadanie Urzędu Zamówień Publicznych). Repozytorium prywatne; organizacja docelowa: `HackNation2026-dev`.

## Stan implementacji (sprawdzony w kodzie)

> **Uwaga: polecenie `process` działa dziś na atrapie silnika.** Przechodzi po PDF-ach, odtwarza strukturę katalogów i zapisuje dla każdego plik `{}`. Klasyfikacja i ekstrakcja pól (OCR, reguły, LLM) trafią do polecenia po zadaniu Z01 ([zadania dla agentów](docs/00-organizacja/zadania-dla-agentow.md)); ta sekcja zostanie wtedy zaktualizowana. Instalacja, skrypty startowe, katalogi `input/` i `output/`, kody wyjścia i atomowy zapis działają już teraz i są objęte testami.
>
> Liczby jakości (F1) pochodzą z uprzęży pomiarowej w `experiments/`, nie z produktu: zobacz [raport eksperymentów](experiments/2026-11-21-wybor-modulow/RAPORT.md).

## Wymagania

- Python **3.13** lub nowszy (koła `onnxruntime` i `pypdfium2` w przypiętych wersjach są gotowe dla 3.13 na Linuksie i Windows; inne wersje Pythona mogą nie mieć kół).
- Linux, macOS lub Windows; procesor x86-64, **bez GPU**. Do pracy z OCR zalecane 16 GB RAM (szczyt ok. 0,9 GB na proces).
- Dostęp do PyPI tylko przy instalacji. **Po instalacji OCR działa bez sieci**: wagi modeli (3 pliki ONNX) są w kole `rapidocr` i nic nie jest pobierane przy starcie.
- Miejsce na dysku: ok. 500 MB na środowisko wirtualne (`.venv`); czysta instalacja trwa ok. 1 minuty przy szybkim łączu.
- Klucz API modelu językowego (LLM po API; dostawca z UE/EOG): patrz [Klucz API](#klucz-api).

## Instalacja i uruchomienie jednym poleceniem

Umieść PDF-y w `input/` (podkatalogi są przeszukiwane rekurencyjnie), potem:

**Linux / macOS**

```sh
sh run.sh
```

**Windows** (PowerShell lub cmd, w katalogu repozytorium)

```bat
start.bat
```

Skrypt tworzy `.venv`, instaluje `requirements.txt`, tworzy `input/` i `output/` (jeśli ich brak) i uruchamia `python -m odwolania2json process input output`. Kolejne uruchomienia pomijają tworzenie środowiska i doinstalowują tylko braki. Jeśli domyślny interpreter jest za stary, wskaż właściwy: `PYTHON=/ścieżka/python3.13 sh run.sh` (Windows: `set PYTHON=C:\Python313\python.exe`).

### Ręcznie

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt      # Windows: .venv\Scripts\python.exe
.venv/bin/python -m odwolania2json process input output
```

`requirements.txt` zawiera wyłącznie zależności uruchomieniowe, przypięte (`==`), z OCR (`rapidocr`, `onnxruntime` w wersji CPU) i pakietami lokalnymi instalowanymi bez `-e`. Narzędzia deweloperskie (pytest, ruff, mypy, generatory kontraktu) są w `requirements-dev.txt`.

## Klucz API

Aplikacja czyta konfigurację LLM ze zmiennych środowiskowych. **Klucza nie zapisuj w repozytorium ani w plikach śledzonych przez Git** (`.env` jest w `.gitignore`).

| Zmienna | Znaczenie |
|---|---|
| `LLM_API_KEY` | klucz API dostawcy |
| `LLM_BASE_URL` | adres API zgodnego z OpenAI, np. `https://adres-api/v1` |
| `LLM_MODEL` | nazwa modelu |

```sh
export LLM_API_KEY=...   LLM_BASE_URL=https://adres-api/v1   LLM_MODEL=nazwa-modelu    # Linux/macOS
set LLM_API_KEY=...      & set LLM_BASE_URL=https://adres-api/v1 & set LLM_MODEL=nazwa-modelu   # Windows cmd
```

Skrypty startowe ostrzegają, gdy `LLM_API_KEY` nie jest ustawiony. Atrapa silnika (stan obecny) nie wywołuje LLM, więc działa bez klucza.

## Struktura wyniku

Dla każdego `input/<ścieżka>/<nazwa>.pdf` powstaje `output/<ścieżka>/<nazwa>.json` (ta sama nazwa i drzewo katalogów). Dokument obcy (niezaliczony do żadnej z trzech klas) dostaje pusty plik `{}`. Zapis jest atomowy (plik tymczasowy, `fsync`, zamiana), więc przerwany przebieg nie zostawia pół-pliku. Błędu nigdy nie zastępuje się zmyślonymi danymi.

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
| 1 | błąd co najmniej jednego dokumentu (pozostałe są przetworzone; dla błędnego nie powstaje plik wyniku, komunikat na stderr) |
| 2 | błąd użycia: np. brak katalogu wejściowego, brak Pythona 3.13+ w skrypcie startowym |

## Rozwiązywanie problemów

| Objaw | Przyczyna i działanie |
|---|---|
| `błąd: potrzebny Python 3.13+` | zainstaluj Pythona 3.13 albo ustaw zmienną `PYTHON` na jego ścieżkę |
| `No matching distribution found for onnxruntime` | Python inny niż 3.13 lub system bez kół (np. ARM Linux); użyj 3.13 na x86-64 |
| błąd instalacji przy braku sieci | `pip install` wymaga PyPI; po instalacji sieć nie jest potrzebna dla OCR |
| katalog `input/` pusty | skrypt kończy się kodem 0 bez wyników; wgraj PDF-y (`.pdf`, małe litery) |
| nic nie zapisuje się w `output/` i kod 1 | sprawdź stderr: błąd dokumentu jest raportowany z nazwą pliku |
| brak ostrzeżenia o kluczu, a LLM nie odpowiada | sprawdź `LLM_BASE_URL` (z `/v1`) i `LLM_MODEL` |

## Sprawdzenie czystej instalacji

```sh
python3 scripts/verify_install.py --python python3.13
```

Skrypt tworzy tymczasowe środowisko, instaluje `requirements.txt` z PyPI, sprawdza obecność wag OCR w kole i uruchamia `process` na trzech małych PDF-ach z lokalną atrapą LLM (`LLM_BASE_URL` wskazuje na `127.0.0.1`). Kody: 0 OK, 1 błąd, 3 SKIP (brak sieci do PyPI; jawnie, nie jako sukces). Test pytest: `O2J_VERIFY_INSTALL=1 python -m pytest tests/unit/test_delivery.py -m slow_install`.

**Windows: do uruchomienia przez człowieka** (zespół nie ma maszyny z Windows do testów zdalnych). W PowerShellu w katalogu repozytorium:

```bat
py -3.13 scripts\verify_install.py --python py
start.bat
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
