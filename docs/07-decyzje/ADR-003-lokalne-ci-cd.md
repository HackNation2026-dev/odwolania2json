---
wersja: 0.6.1
aktualizacja: 2026-11-21
status: przyjęta decyzja użytkownika
---

# ADR-003: lokalne CI/CD

## Decyzja

Kontrole i wydania wykonujemy lokalnie na Pythonie 3.13. Runner scripts/ci.py uruchamia docs, lint, types, api, test, mutation i audit. Kontrole są pogrupowane w poziomy z budżetem czasu, aby bramka nie spowalniała pracy: przed commitem tylko zmiany z indeksu, przed push pełne testy i mutacje przyrostowe, pełne mutacje osobno. Każdy poziom jest obowiązkowy i wykonywany przez hook. [ADR-002](ADR-002-decyzje-po-recenzji.md) nadal określa dostarczenie pip i obowiązek testowania regex, normalizatorów i walidatora.

Jedynym właścicielem hooków jest framework pre-commit. Zastępuje .githooks/, również dla pre-push; unikamy dwóch konfiguracji o różnych bramkach. Instalator usuwa wyłącznie stare lokalne core.hooksPath=.githooks; obce ustawienie zgłasza jako błąd. Pre-commit wykonuje standardowe kontrole plików oraz `ci.py --profile commit`, a pre-push `ci.py --profile push` (hooki ci-commit i ci-push). Obejście przez --no-verify lub zmienne pomijające hooki jest zabronione. Poprzednia wersja uruchamiała przy każdym commicie pełne testy z pokryciem, mypy i mutacje staged, a przy push pełne mutacje; to spowalniało pracę, więc zastąpiono ją poziomami poniżej. Zakres kontroli się nie zmniejszył: to, co pomija commit, nadrabia push, a pełny zakres mutacji sprawdza osobne polecenie.

## Poziomy kontroli i budżety czasu

| Poziom | Polecenie | Cel | Zakres |
|---|---|---|---|
| pre-commit | `ci.py --profile commit` | < ~10 s | docs tylko przy zmianie dokumentów; Ruff (check i format) tylko na plikach z indeksu; mypy strict z cache przyrostowym; testy tylko dla zmienionych modułów i testów, bez pokrycia; API spec tylko przy zmianie kontraktu; mutacje wyłącznie linii zmienionych w indeksie, w plikach z zakresu mutacji |
| pre-push | `ci.py --profile push` | < ~2 min | docs, Ruff, mypy, API, pełne testy z progiem pokrycia 90%, mutacje całych modułów zmienionych od merge-base z `main` (także testów tych modułów) |
| pełne | `ci.py --stage mutation` | bez limitu, poza ścieżką pracy | wszystkie moduły z zakresu; ręcznie lub z crona, np. `0 3 * * * cd REPO && python3 scripts/ci.py --stage mutation >> .ci/mutation-cron.log 2>&1` |
| wydanie | `ci.py --stage all` | bez limitu | wszystko oraz audit; używa go release.py |

Etap bez zmian w zakresie jest jawnym SKIP z powodem, nigdy cichym pominięciem. Każdy przebieg kończy się linią `razem` z czasem i informacją, czy budżet został dotrzymany; przekroczenie budżetu jest raportowane, ale nie blokuje. Pierwsze uruchomienie mypy na zimnym cache trwa dłużej niż kolejne. Commit zmieniający moduł z zakresu mutacji płaci tylko za mutanty w zmienionych liniach; pozostałe linie sprawdza push, a ich zielony wynik zostaje w cache.

Hooki wywołują python3 z PATH, a `ci.py` przełącza się na interpreter z `CI_PYTHON` albo `.venv/bin/python`. Brak narzędzia lub zależności kończy się FAIL z instrukcją instalacji, nigdy cichym pominięciem kontroli.

## Narzędzia i licencje

| Narzędzie | Wersja | Licencja |
|---|---|---|
| Ruff | 0.17.5 | MIT |
| mypy | 1.18.2 | MIT |
| build | 1.3.0 | MIT |
| pre-commit | 4.5.0 | MIT |
| pre-commit-hooks | v6.0.0 | MIT |
| pytest-cov | 7.1.0 | MIT |
| pip-audit | 2.10.1 | Apache-2.0 |
| types-PyYAML | 6.0.12.20260815 | Apache-2.0 |

Wersje są przypięte w requirements-dev.txt i .pre-commit-config.yaml. Instalację zależności aplikacji i narzędzi potwierdzono przez uv pip install -r requirements-dev.txt -r requirements.txt na CPythonie 3.13.18. Licencje i minimalne wersje Pythona sprawdzono w metadanych zainstalowanych dystrybucji; wszystkie dopuszczają 3.13. SQLAlchemy 2.1.9 (MIT) jest istniejącą zależnością produkcyjną; zmianę bazy opisuje [ADR-004](ADR-004-sqlalchemy-sqlite-bez-postgres.md).

## Standardy i progi

Ruff sprawdza E, F, I, B, UP, SIM, C4, PT, RUF, N, ANN, S i TID oraz format. Wyjątki dla asercji testowych, procesów narzędziowych i Unicode są jawne w pyproject.toml. Modele generowane z kontraktu są wyłączone z formatowania ręcznego; ich identyczność kontroluje test regeneracji. Typowanie apps/ i packages/: mypy --strict.

Pokrycie aplikacji i kontraktów mierzymy przez pytest-cov, bez testów eval. Próg wynosi **90%**, wobec stanu bazowego około **92%** dla 162 testów. Pozostawia mały margines dla obsługi błędów, a blokuje większe regresje. Pokrycie nie zastępuje mutacji ani testów awarii.

## Mutacje

Zamiast zależności mutmut stosujemy lokalny runner AST oparty na bibliotece standardowej Pythona. Nie deklarujemy niezgodności mutmut z Pythonem 3.13: poprzednie środowisko nie potwierdziło działającego przebiegu. Własny runner nie wymaga fork, formatu .meta ani specjalnego układu pakietów i obsługuje wykonywalne deklaracje modeli pydantic. To jawna zmiana narzędzia, a nie wyłączenie etapu.

Zakres wykrywany jest w apps/ i packages/: moduły normalizacji i walidacji, używające regex oraz generowane modele wyniku. Operatory zmieniają pojedyncze liczby, wartości logiczne, cyfry i separatory wzorców, etykiety Literal/alias, politykę extra i typy pól. To określony zestaw operatorów, nie dowód odporności na każdą możliwą zmianę kodu. Próg: **100% zabitych**, zero przeżytych, błędów i timeoutów. Moduł bez żadnego mutanta w pełnym przebiegu jest FAIL. Błąd wewnętrzny pytest nie zabija mutanta: wymagany kod 1.

Wykonanie: mutanty działają równolegle (`--jobs`, domyślnie do 8), każdy w jednej z kopii źródeł `apps/` i `packages/` w .ci/ (repozytorium nigdy nie jest modyfikowane, więc przerwanie nie zostawia zmutowanego kodu), z PYTHONPATH wskazującym kopię; runner sprawdza, że mutant faktycznie jest ładowany z kopii. Dla modułu uruchamiane są tylko pliki testowe wspominające jego nazwę (modele: tests/contract i test_base; brak dopasowania daje cały zestaw), pytest z `-x`. Limit czasu na mutanta wynika z czasu testów bazowych (5×, od 10 do 120 s) albo z `--mutant-timeout`; timeout jest FAIL. Przed mutantami każdy moduł przechodzi testy bazowe: ich błąd to FAIL modułu z nazwami padających testów, bez uruchamiania mutantów i bez udawania, że mutant przeżył.

Cache `.ci/mutation-cache.json` zapisuje moduł jako zaliczony wyłącznie po przebiegu w pełni zielonym, pod skrótem: kod modułu, pliki wybranych testów, wszystkie conftest.py, pytest.ini i operatory mutacji. Zmiana któregokolwiek unieważnia wpis; wynik niezielony usuwa wpis. Trafienie w cache to jawny SKIP z powodem. Skrót nie obejmuje innych modułów, które testy wywołują pośrednio, więc zmiana zależności nie unieważnia cache; pełne `--stage mutation --no-cache` omija to ograniczenie. Przebiegi dla zmienionych linii (`--profile commit`) są częściowe i nigdy nie trafiają do cache. `--max-survivors` przerywa uruchamianie reszty mutantów po zadanej liczbie niezabitych (commit: 3, push: 10), by szybko zwrócić błąd; raport wskazuje liczbę nieuruchomionych.

Zakresy: `--changed` (kopia indeksu z checkout-index, poprawki unstaged nie maskują wad commita), `--since REF` (pliki zmienione od merge-base z REF, także niezacommitowane; brak merge-base daje jawne ostrzeżenie i zakres pełny), domyślnie wszystko. Brak zmian w zakresie to jawny SKIP. Raport .ci/mutation-report.txt i niezabite warianty .ci/mutation-failures/ powstają przy każdym przebiegu.

## Audit i wydawanie

--stage audit używa pip-audit dla przypiętych zależności backendu. Brak sieci do PyPI daje jawny SKIP z powodem; brak narzędzia, podatności i inne błędy dają FAIL. Ten etap nie zastępuje pełnego audytu zależności przechodnich.

Wydanie wymaga czystego Git, zgodności VERSION/CHANGELOG/wersji obu pakietów oraz pełnego CI. scripts/release.py buduje kopie wheel i sdist w .ci/, zapisuje je atomowo do dist/ z SHA-256. --tag tworzy tylko lokalny tag. Push i publikacja pozostają ręczne. Dwie definicje pakietów pip pozostają; ich ujednolicenie według ADR-002 jest osobnym zadaniem. Hooki wymagają instalacji, a lokalny wynik nie stanowi niezależnej bramki chmurowej.

Instrukcja: [lokalne CI/CD](../00-organizacja/lokalne-ci-cd.md).
