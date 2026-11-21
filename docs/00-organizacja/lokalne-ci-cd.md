---
wersja: 0.6.1
aktualizacja: 2026-11-21
status: wdrożone kontrole lokalne
---

# Lokalne CI/CD

Wymagane Python 3.13 i Git. Narzędzia i konsekwencje opisuje [ADR-003](../07-decyzje/ADR-003-lokalne-ci-cd.md); bazę [ADR-004](../07-decyzje/ADR-004-sqlalchemy-sqlite-bez-postgres.md).

## Instalacja

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
sh scripts/install_hooks.sh
```

Framework pre-commit zarządza hookami pre-commit i pre-push (hooki ci-commit i ci-push); `.githooks/` nie istnieje. Instalator usuwa stare core.hooksPath=.githooks, ale nie nadpisuje obcej konfiguracji. Hooki wołają python3 z PATH, a ci.py sam przełącza się na interpreter z CI_PYTHON albo .venv/bin/python, więc Git nie wymaga aktywnego środowiska. Odinstalowanie: python -m pre_commit uninstall --hook-type pre-commit --hook-type pre-push.

## Poziomy kontroli

| Poziom | Polecenie | Budżet | Co sprawdza |
|---|---|---|---|
| pre-commit | `python scripts/ci.py --profile commit` | ~10 s | tylko pliki z indeksu: docs przy zmianie dokumentów, Ruff, mypy z cache, testy zmienionych modułów bez pokrycia, API spec przy zmianie kontraktu, mutacje zmienionych linii |
| pre-push | `python scripts/ci.py --profile push` | ~2 min | docs, Ruff, mypy, API, pełne testy z progiem 90%, mutacje modułów zmienionych od merge-base z main |
| pełne mutacje | `python scripts/ci.py --stage mutation` | bez limitu | wszystkie moduły z zakresu; ręcznie lub z crona |
| wydanie | `python scripts/ci.py --stage all` | bez limitu | wszystko plus audit (release.py) |

Wszystkie poziomy są obowiązkowe; **zakaz --no-verify, SKIP i PRE_COMMIT_ALLOW_NO_CONFIG**. Etap bez zmian w zakresie jest jawnym SKIP z powodem. Każdy przebieg profilu kończy się linią `razem` z czasem i oceną budżetu; przekroczenie jest raportowane, nie blokuje. Mutacje zmieniają budżet commita tylko wtedy, gdy zmieniasz plik z zakresu (normalizatory, regex, walidator, modele): płacisz za mutanty zmienionych linii, resztę modułu sprawdza push, a zielony wynik zostaje w cache.

Przykład crona dla pełnych mutacji (nie blokuje pracy, wynik w .ci/mutation-report.txt i logu):

```sh
0 3 * * * cd /ścieżka/do/repo && python3 scripts/ci.py --stage mutation >> .ci/mutation-cron.log 2>&1
```

## Kontrole ręczne

```sh
python scripts/ci.py --fast
python scripts/ci.py --stage all
python scripts/ci.py --stage mutation                 # pełne, z cache
python scripts/ci.py --stage mutation --no-cache      # pełne, bez cache
python scripts/ci.py --stage mutation --since main    # moduły zmienione od merge-base
python scripts/ci.py --stage mutation --changed       # kopia indeksu
python scripts/ci.py --stage lint --files a.py b.py
python scripts/ci.py --stage test --files tests/unit/test_x.py
python scripts/ci.py --stage audit
python scripts/ci.py --stage all --keep-going
pre-commit run --all-files
```

Opcje mutacji: `--jobs N` (domyślnie do 8 równoległych mutantów), `--mutant-timeout S`, `--no-cache`.

| Etap | Kontrola |
|---|---|
| docs | integralność materiałów i linków przez verify_docs.py; błędy są raportowane jawnie |
| lint | Ruff check i format --check (z --force-exclude); reguły w pyproject.toml |
| types | mypy --strict apps/ packages/ scripts/ci.py, cache przyrostowy .ci/mypy |
| api | validate_api.py --stage all; z --fast lub --stage api --spec tylko spec |
| test | pytest bez eval, pytest-cov, próg 90%; z --files tylko testy zmienionych modułów, bez pokrycia |
| mutation | lokalne operatory AST; wymagane 100% zabitych |
| audit | pip-audit zależności backendu; brak sieci = jawny SKIP |

Mutacje działają równolegle na kopiach źródeł w .ci/ (repozytorium nie jest modyfikowane), dla modułu uruchamiają tylko testy go obejmujące, a każdy mutant ma limit czasu. Moduł najpierw przechodzi testy bazowe: ich błąd to FAIL modułu z nazwami testów, a nie przeżyły mutant. Zielony wynik jest zapisany w .ci/mutation-cache.json pod skrótem kodu modułu, jego testów i operatorów; niezmienione moduły są jawnym SKIP (cache). Wynik niezielony nigdy nie trafia do cache. Raport: .ci/mutation-report.txt, niezabite warianty: .ci/mutation-failures/. Kod pytest 1 zabija mutanta; przeżycie, timeout lub inny błąd blokują. Szczegóły i ograniczenia skrótu: [ADR-003](../07-decyzje/ADR-003-lokalne-ci-cd.md).

Kolejność etapów jest stała. Pierwszy FAIL zatrzymuje kolejne; --keep-going zbiera dalsze wyniki. Kody runnera: 0 sukces wybranych kontroli (także jawny SKIP), 1 błąd, 2 błędne argumenty. Brak narzędzia to FAIL z instrukcją instalacji. Cache i kopie trafiają do ignorowanego .ci/. Materiały organizatora są wykluczone ze standardowych hooków naprawiających pliki. Historyczny workflow docs nie zastępuje lokalnej bramki.

## Wydawanie

Uzgodnij VERSION, CHANGELOG i wersje obu pakietów. Z czystego Git uruchom:

```sh
python scripts/release.py
python scripts/release.py --tag
```

Domyślnie runner wykonuje pełne CI, buduje wheel i sdist obu pakietów na kopiach i zapisuje dist/ z SHA-256, bez tagu. Niezgodna wersja artefaktu blokuje wydanie. --tag tworzy lokalny v<VERSION> po sukcesie; istniejący tag nie jest nadpisywany. Nie ma automatycznej publikacji ani push. Dostarczenie jury pozostaje ręczne przez pip. Starsze artefakty w dist/ nie są częścią raportu bieżącej budowy.

## Ograniczenia

Weryfikacja etapu 2 używa CPythona 3.13.18 i przypiętych zależności. Systemowy python3 w środowisku roboczym ma wersję 3.15.2 i nie ma narzędzi projektu; do poleceń należy aktywować środowisko 3.13. Wersje obu pakietów są ujednolicone na 0.6.1 zgodnie z VERSION (`__version__` i pyproject); `release.py` blokuje rozjazd. Wersja `info.version` w `openapi.yaml` (0.5.0) to osobna, niezależnie wersjonowana rewizja kontraktu; zmienia ją zadanie 5 z backlogu.
