# Praca w repozytorium

Pisz po polsku, krótko i jednoznacznie. Status implementacji ustal na podstawie kodu i testów.

Przed implementacją przeczytaj [wymagania](docs/03-wymagania/README.md) i [pytania otwarte](docs/07-decyzje/pytania-otwarte.md).
Przy zmianie materiałów sprawdź [rejestr źródeł](docs/02-materialy/README.md) i [wersjonowanie](docs/00-organizacja/wersjonowanie.md). Zachowuj niezmienione oryginały; poprawki i interpretacje zapisuj poza katalogami organizatora.
Przy zmianie stosu przeczytaj [architekturę](docs/04-architektura/README.md) i dodaj decyzję z konsekwencjami.
Przed commitem uruchom `python3 scripts/verify_docs.py` oraz kontrole odpowiednie do zmienionego kodu.
Klucze i tokeny przechowuj poza Git. Potwierdzenie API/modelu obejmuje licencję i lokalizację wymaganą w zadaniu.

## Standardy kodu

Stan narzędzi ustal w repozytorium: dziś działa tylko `.github/workflows/docs.yml` (`verify_docs.py`). Brakujące narzędzia poniżej to wymagania do wdrożenia; ich wybór i wersje zapisz w ADR (zmiana stosu).

### Typowanie w Pythonie

- Cały kod w `apps/` i `packages/` ma pełne adnotacje typów (parametry, zwroty, atrybuty). Python 3.13, składnia `X | None`, `list[str]`.
- `mypy --strict` bez błędów jest warunkiem merge'a. Brak `Any` i `# type: ignore` bez komentarza z powodem.
- Granice systemu (HTTP, pliki, LLM, OCR) waliduje pydantic v2; wewnątrz używaj typów, nie surowych `dict`.
- Lint i format: `ruff check` oraz `ruff format`.

### Testy

- `pytest`; test pisz przed implementacją (czerwony, potem zielony). Nazwy testów po angielsku.
- Błąd naprawiaj z testem, który bez poprawki zawodzi.
- Testy mutacyjne są **obowiązkowe** dla wzorców regex, normalizatorów i walidatora wyniku (ADR-002 pkt 6): mutacje pojedynczych cyfr, etykiet i formatów. Przeżyły mutant = brakujący test. Próg zabitych mutantów ustal w ADR; do tego czasu zero przeżytych w normalizatorach NIP/REGON/KRS/PESEL, dat i kwot.
- Testy kontraktowe i wstrzykiwanie awarii (OCR, PDF, sieć, 401/403, 429, limity, zapis) według architektury §6.
- Zera w kartach lub brak błędów nie dowodzą odporności.

### API i kontrakt

- Kontrakt: `packages/contracts/.../openapi.yaml` (OpenAPI 3.1) jest źródłem prawdy; modele generuje `scripts/generate_contracts.py`, nie edytuj ich ręcznie.
- Backend FastAPI używa wygenerowanych modeli. `app.openapi()` musi zgadzać się ze specyfikacją (ścieżki, metody, `operationId`, schematy): `python scripts/validate_api.py --stage all`. Rozjazd blokuje merge.
- Klienty (typy TypeScript dla GUI) generuj z kontraktu (np. `openapi-typescript`); wygenerowanych plików nie edytuj ręcznie.
- Zmiana łamiąca kontrakt wymaga nowej wersji API i ADR. Szczegóły: skill `generate-api`.

### CI/CD

- CI (GitHub Actions, Python 3.13) uruchamia na każdy push i PR: `docs` (`verify_docs.py`), `lint` (ruff), `types` (mypy), `api` (`validate_api.py --stage all`), `test` (pytest), `mutation` (mutanty dla normalizatorów i regex; może działać na zmienionych plikach lub nocą).
- Joby mają przypięte wersje akcji i narzędzi, minimalne `permissions` i cache zależności.
- Merge do `main` tylko przez PR z zielonym CI. Brak bezpośrednich pushy i `--force` na `main`.
- CD: dostarczenie u jury to wyłącznie pakiet instalowany przez pip; Docker tylko deweloperski (ADR-002). Wydanie = tag zgodny z `VERSION` + wpis w `CHANGELOG.md` + budowa pakietu w CI. Automatycznego wdrożenia nie ma, dopóki nie zapadnie decyzja o serwerze.
- Hook pre-commit (`.githooks/`, `git config core.hooksPath .githooks`) uruchamia szybkie kontrole: docs, ruff, mypy, walidacja spec.

### Dobre praktyki

- Małe, atomowe commity z opisem „dlaczego”; jedna zmiana logiczna na PR.
- Zależności przypięte (`==`), bez nowych bez sprawdzenia licencji open source i obsługi Pythona 3.13.
- Sekrety tylko ze środowiska lub pliku poza Git; nie loguj kluczy ani treści dokumentów. Nie używaj `eval`/`exec` na danych wejściowych.
- Błąd techniczny jest jawny (kod, stan `technical_error`); nigdy zmyślone dane ani cicha podmiana na stary wynik z cache.
- Zapis plików atomowy (plik tymczasowy, `fsync`, zamiana). Brak stanu globalnego; konfiguracja wstrzykiwana.
- Nie edytuj oryginałów organizatora w `docs/02-materialy/`.
- Docstringi i komentarze po polsku, wyjaśniają „dlaczego”; nazwy w kodzie po angielsku.
