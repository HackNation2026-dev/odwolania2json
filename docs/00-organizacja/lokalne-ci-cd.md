---
wersja: 0.6.1
aktualizacja: 2026-11-21
status: wdrożone skrypty; pełna bramka wymaga zielonego przebiegu
---

# Lokalne CI/CD

Wszystkie polecenia wykonuje deweloper. Wymagany Python 3.13, Git oraz Linux/macOS lub WSL (mutmut wymaga fork). Decyzję i ograniczenia opisuje [ADR-003](../07-decyzje/ADR-003-lokalne-ci-cd.md).

## Instalacja

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
sh scripts/install_hooks.sh
```

Instalator ustawia lokalne `core.hooksPath=.githooks`. Hooki korzystają z `python3` w PATH; można wskazać interpreter zmienną `PYTHON`. Nie należy wskazywać ścieżki ze spacjami wraz z argumentami. Odłączenie: `git config --unset core.hooksPath`.

## Kontrole

```sh
python scripts/ci.py --fast
python scripts/ci.py --stage all
python scripts/ci.py --stage mutation
python scripts/ci.py --stage all --keep-going
```

| Etap | Kontrola |
|---|---|
| docs | `scripts/verify_docs.py`: integralność materiałów i linki |
| lint | `ruff check` i `ruff format --check` całego repo, według wykluczeń w pyproject.toml |
| types | `mypy --strict apps/ packages/`, bez wyłączania błędów istniejącego kodu |
| api | `validate_api.py --stage all`; w `--fast` tylko `--stage spec` |
| test | pytest z `-m "not eval"`; eval uruchamiany osobno |
| mutation | mutmut dla normalizatorów i modeli walidujących, dodatkowe mutacje deklaracji regex i typów pól |

Kolejność jest stała. Domyślnie pierwszy FAIL zatrzymuje kolejne etapy; `--keep-going` zbiera dalsze błędy. Raport pokazuje OK/FAIL/SKIP i czas każdego etapu. Kod 0 oznacza sukces wybranych kontroli, 1 błąd kontroli, 2 błędne argumenty. SKIP dotyczy etapów niewybranych lub zatrzymanych; brak narzędzia jest FAIL z poleceniem instalacji.

Cache, pliki tymczasowe i kopie mutacyjne trafiają do ignorowanego `.ci/`; runner nie formatuje ani nie poprawia kodu. Runner odwzorowuje pakiety do `src/` w kopii roboczej (układ obsługiwany przez mutmut 3); konfiguracja mutmut wskazuje te ścieżki, dlatego uruchamiaj mutacje przez `ci.py`. Kopie robocze mutacji są usuwane po zakończeniu, raport pozostaje na terminalu. Mutacje dotyczą także pojedynczych cyfr, liter wzorców i formatów; dla modeli zmieniają typy i cyfry ograniczeń pattern. Każdy niezabity mutant, błąd przebiegu lub pusty raport blokuje etap. Testy bazowe muszą przechodzić. Aktualizacja mutmut wymaga sprawdzenia formatu metadanych `.meta`.

Pre-commit wykonuje szybkie kontrole. Pre-push wykonuje pełne CI, także mutacje, co może długo trwać. Zielony pełny przebieg jest wymagany przed push i merge również po pominięciu hooka. Istniejący `.github/workflows/docs.yml` zachowano bez zmian; nie jest częścią tej lokalnej bramki.

## Wydawanie

Uzgodnij VERSION, wpis CHANGELOG i `__version__` obu pakietów. Drzewo Git musi być czyste, także bez plików nieśledzonych. Po kontroli i zapisaniu zmian w historii można uruchomić:

```sh
python scripts/release.py
python scripts/release.py --tag
```

Domyślny dry-run wykonuje pełne CI i rzeczywistą budowę wheel oraz sdist dla `packages/contracts` i `apps/backend`. Zapisuje artefakty w `dist/` i wypisuje SHA-256; nie zmienia historii ani tagów. Budowanie odbywa się na kopiach w `.ci/`, żeby setuptools nie zapisywał przy źródłach. Niezgodna wersja zbudowanego pakietu blokuje wydanie. `dist/` może zawierać starsze pliki; raport SHA-256 dotyczy wyłącznie bieżącej budowy.

`--tag` po sukcesie tworzy lokalny `v<VERSION>`; istniejący tag powoduje błąd, nie jest nadpisywany. Skrypt nigdy nie wykonuje push, publikacji ani wdrożenia. Przekazanie pakietów jury pozostaje ręczne. Wycofanie lokalnego błędnego wydania polega na ręcznym usunięciu jego artefaktów; tag usuwa się ręcznie dopiero po sprawdzeniu, czy nie został udostępniony.

## Stan weryfikacji

Znany wcześniejszy błąd linku bezwzględnego w `docs/04-architektura/gui/recenzja-codex-2026-11-21.md` pozostaje bez zmian i blokuje docs. Obecnie pakiety deklarują 0.5.0, podczas gdy VERSION zawiera 0.6.1; wydanie wymaga uzgodnienia tych wersji. Skrypty nie podmieniają ich automatycznie. Instalacja przypiętych narzędzi wymaga weryfikacji na Pythonie 3.13 z dostępem do PyPI; próby pip index oraz pip install --dry-run w tym środowisku nie znalazły dostępnych dystrybucji, a pobieranie przez uv zakończyło się błędem DNS.
