# Praca w repozytorium

Pisz po polsku, krótko i jednoznacznie. Status implementacji ustal na podstawie kodu i testów.

Przed implementacją przeczytaj [wymagania](docs/03-wymagania/README.md) i [pytania otwarte](docs/07-decyzje/pytania-otwarte.md).
Zadanie bierz z [zadań dla agentów](docs/00-organizacja/zadania-dla-agentow.md) (szczegółowe instrukcje, kolejność P0/P1/P2) i [backlogu](docs/00-organizacja/backlog.md) (znane długi, definicja ukończenia). Po instalacji hooków (`sh scripts/install_hooks.sh`) reguły egzekwuje `pre-commit`.
Przy zmianie materiałów sprawdź [rejestr źródeł](docs/02-materialy/README.md) i [wersjonowanie](docs/00-organizacja/wersjonowanie.md). Zachowuj niezmienione oryginały; poprawki i interpretacje zapisuj poza katalogami organizatora.
Przy zmianie stosu przeczytaj [architekturę](docs/04-architektura/README.md) i dodaj decyzję z konsekwencjami.
Przed commitem uruchom `python3 scripts/verify_docs.py` oraz kontrole odpowiednie do zmienionego kodu.
Klucze i tokeny przechowuj poza Git. Potwierdzenie API/modelu obejmuje licencję i lokalizację wymaganą w zadaniu.

## Standardy kodu

Stan narzędzi ustal w repozytorium i raporcie lokalnego `scripts/ci.py`; konfiguracja nie dowodzi zielonych kontroli. Wybór i wersje narzędzi opisuje [ADR-003](docs/07-decyzje/ADR-003-lokalne-ci-cd.md).

### Typowanie w Pythonie

- Cały kod w `apps/` i `packages/` ma pełne adnotacje typów (parametry, zwroty, atrybuty). Python 3.13, składnia `X | None`, `list[str]`.
- `mypy --strict` bez błędów jest warunkiem merge'a. Brak `Any` i `# type: ignore` bez komentarza z powodem.
- Granice systemu (HTTP, pliki, LLM, OCR) waliduje pydantic v2; wewnątrz używaj typów, nie surowych `dict`.
- Lint i format: `ruff check` (E, F, I, B, UP, SIM, C4, PT, RUF, N, ANN, S, TID) oraz `ruff format`.
- Baza: SQLAlchemy 2.x + SQLite za `DataRepository` (ADR-004). Importy `sqlite3`, `pg8000`, `psycopg*` dopuszczalne tylko w `apps/backend/odwolania2json/db/engine.py`; reguła TID251 i test architektoniczny pilnują granicy. PostgreSQL jest odłożony.

### Testy

- `pytest`; test pisz przed implementacją (czerwony, potem zielony). Nazwy testów po angielsku.
- Błąd naprawiaj z testem, który bez poprawki zawodzi.
- Pokrycie kodu aplikacji i kontraktów: minimum 90% (`pytest-cov`, ADR-003).
- Testy mutacyjne są **obowiązkowe** dla wzorców regex, normalizatorów i walidatora wyniku: mutacje cyfr, etykiet, formatów i typów. Zakres przyrostowy: pre-commit mutuje linie zmienione w indeksie (`ci.py --profile commit`), pre-push cały moduł zmieniony względem merge-base z `main` (`--profile push`), pełny zakres to ręczne `ci.py --stage mutation` (też z crona). Wynik zielony jest zapamiętany w `.ci/mutation-cache.json` pod skrótem kodu i testów. Próg: 100% zabitych, zero przeżytych, błędów i timeoutów (ADR-003). Przeżyły mutant wymaga testu; błąd testów bazowych jest raportowany jako FAIL modułu, nie jako przeżyły mutant.
- Testy kontraktowe i wstrzykiwanie awarii (OCR, PDF, sieć, 401/403, 429, limity, zapis) według architektury §6.
- Zera w kartach lub brak błędów nie dowodzą odporności.

### API i kontrakt

- Kontrakt: `packages/contracts/.../openapi.yaml` (OpenAPI 3.1) jest źródłem prawdy; modele generuje `scripts/generate_contracts.py`, nie edytuj ich ręcznie.
- Backend FastAPI używa wygenerowanych modeli. `app.openapi()` musi zgadzać się ze specyfikacją (ścieżki, metody, `operationId`, schematy): `python scripts/validate_api.py --stage all`. Rozjazd blokuje merge.
- Klienty (typy TypeScript dla GUI) generuj z kontraktu (np. `openapi-typescript`); wygenerowanych plików nie edytuj ręcznie.
- Zmiana łamiąca kontrakt wymaga nowej wersji API i ADR. Szczegóły: skill `generate-api`.

### CI/CD

- CI działa lokalnie na Pythonie 3.13 w dwóch poziomach hooków z budżetem czasu (raport kończy się linią `razem`, przekroczenie budżetu jest jawnie zgłaszane): **pre-commit** `ci.py --profile commit` (cel poniżej ~10 s: tylko zmienione pliki, ruff na staged, mypy z cache, testy zmienionych modułów bez pokrycia, mutacje zmienionych linii; etapy bez zmian są jawnym SKIP) oraz **pre-push** `ci.py --profile push` (cel poniżej ~2 min: docs, lint, types, api, pełne testy z progiem pokrycia, mutacje modułów zmienionych od merge-base z `main`). `python scripts/ci.py --stage all` (docs, lint, types, api, test bez eval, pełne mutacje, audit) uruchamia release; audit może zgłosić jawny SKIP wyłącznie z powodu braku sieci. Przed każdym push i merge wymagany jest zielony wynik pozostałych etapów.
- Narzędzia mają przypięte wersje w `requirements-dev.txt`. Brak narzędzia lub niepełny raport mutacji oznacza FAIL z instrukcją instalacji. Hooki wołają `python3`; `ci.py` przełącza się na `CI_PYTHON` albo `.venv/bin/python` projektu.
- Framework `pre-commit` zarządza oboma hookami (jedna definicja, bez `.githooks/`): `ci-commit` i `ci-push` z `.pre-commit-config.yaml`. Konfiguracja: `.pre-commit-config.yaml`, instalacja: `sh scripts/install_hooks.sh`. `.githooks/` zastąpiono frameworkiem (ADR-003).
- Zakaz `--no-verify`, `SKIP` do omijania hooków i `PRE_COMMIT_ALLOW_NO_CONFIG`; popraw przyczynę blokady i ponów kontrole. Bez `--force` na `main`.
- CD działa lokalnie: `python scripts/release.py` sprawdza czysty Git, VERSION, CHANGELOG, pełne CI i buduje pakiety pip do `dist/` z sumami SHA-256. `--tag` tworzy lokalny tag `v<VERSION>` po udanej budowie. Push i publikacja pozostają ręczne.
- Dostarczenie u jury wyłącznie przez pip; Docker tylko deweloperski (ADR-002). Automatycznego wdrożenia nie ma. Instrukcja: [lokalne CI/CD](docs/00-organizacja/lokalne-ci-cd.md).

### Dobre praktyki

- Małe, atomowe commity z opisem „dlaczego”; jedna zmiana logiczna na PR.
- Zależności przypięte (`==`), bez nowych bez sprawdzenia licencji open source i obsługi Pythona 3.13.
- Sekrety tylko ze środowiska lub pliku poza Git; nie loguj kluczy ani treści dokumentów. Nie używaj `eval`/`exec` na danych wejściowych.
- Błąd techniczny jest jawny (kod, stan `technical_error`); nigdy zmyślone dane ani cicha podmiana na stary wynik z cache.
- Zapis plików atomowy (plik tymczasowy, `fsync`, zamiana). Brak stanu globalnego; konfiguracja wstrzykiwana.
- Nie edytuj oryginałów organizatora w `docs/02-materialy/`.
- Docstringi i komentarze po polsku, wyjaśniają „dlaczego”; nazwy w kodzie po angielsku.
