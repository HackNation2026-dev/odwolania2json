---
wersja: 0.6.1
aktualizacja: 2026-11-21
status: przyjęta decyzja użytkownika
---

# ADR-004: SQLAlchemy + SQLite, bez PostgreSQL

## Decyzja

Na polecenie użytkownika obowiązuje jeden standard: **SQLAlchemy 2.x + SQLite** (sterownik biblioteki standardowej używany przez SQLAlchemy). PostgreSQL usuwamy z kodu i konfiguracji; jego powrót jest odłożony.

- Cały dostęp do bazy w backendzie idzie przez SQLAlchemy (Core) za interfejsem `DataRepository` z [architektury §9](../04-architektura/architektura-wewnetrzna.md). Implementacją v1 jest `SqliteDataRepository` (`db/data_repository.py`): metadane, zadania, rewizje i zatwierdzone wyniki w SQLite, bajty PDF i artefakty w katalogu roboczym (`WORK_DIR`) pod nieprzezroczystym `storage_key`.
- `CatalogRepository`/`DocumentRepository` (`db/repository.py`) to osobny, starszy katalog ekstrakcji (odczyty panelu); nie jest `DataRepository` z §9 i nie zastępuje go.
- Bezpośredni import `sqlite3`, `pg8000`, `psycopg*` jest dozwolony wyłącznie w `db/engine.py`. Granicę wymuszają reguła Ruff TID251 (`pyproject.toml`) i test `tests/unit/test_database_imports.py`, który skanuje importy AST.
- Konfiguracja przyjmuje tylko `sqlite:///plik.db` i `sqlite+pysqlite:///plik.db`; inny sterownik kończy się `ValueError` przed utworzeniem połączenia. Brak `DATABASE_URL` nadal oznacza brak opcjonalnego repozytorium.

Decyzja ma pierwszeństwo przed zapisami PostgreSQL w [ADR-002](ADR-002-decyzje-po-recenzji.md), w [architekturze §9–§10](../04-architektura/architektura-wewnetrzna.md) (`PostgresDataRepository`, „skalowane wdrożenie”) i w [historycznym projekcie backendu](../04-architektura/projekt-backend-fastapi-postgres-ui.md). Te zapisy są **odłożone**, nie unieważnione: zostają jako historia i opis kierunku. Pozostałe decyzje ADR-002 (pip u jury, Docker tylko deweloperski, katalog roboczy, kontrakt §9) obowiązują bez zmian.

## Gwarancje §9 po zamianie typów

Typy PostgreSQL (`uuid`, `jsonb`, `timestamptz`) zastąpiono tym, co SQLite naprawdę egzekwuje:

- identyfikatory i skróty: `text`, walidowane na granicy pydantic (wzorzec identyfikatora, 64 znaki hex); długość skrótu pilnuje też `CHECK`;
- JSON (manifest, ładunki): `text` z `CHECK (json_valid(...))`, zapis w postaci kanonicznej;
- czas: `text` UTC z `CURRENT_TIMESTAMP` (rozdzielczość sekundy; kolejność historii wyznacza `rowid`, nie czas);
- stany i wyniki: `CHECK` na zbiorach `queued/running/done` i pięciu wynikach z §6; `FOREIGN KEY` włączone dla każdego połączenia, zadanie wskazuje dokument tego samego wsadu (złożony klucz obcy);
- niezmienność artefaktów: wyzwalacze `BEFORE UPDATE/DELETE` odrzucają zmianę.

Mechanika kontraktu:

- **Rewizje.** `claim_job`/`update_job` działają w transakcji `BEGIN IMMEDIATE`: odczyt rewizji i zapis są jedną serializowaną operacją, więc spośród równoległych wywołań z tą samą rewizją wygrywa dokładnie jedno; reszta dostaje `RevisionConflictError` bez zmiany stanu. Dozwolone przejścia: `queued→running`, `running→done`; `done` ustawia wyłącznie `commit_run`.
- **`commit_run`.** Jedna transakcja: sprawdzenie, że przebieg jest `running` i niezatwierdzony; weryfikacja skrótów wszystkich artefaktów na dysku; atomowy zapis manifestu (plik tymczasowy, `fsync`, zamiana); wiersz wyniku i stan `done`. Awaria na dowolnym kroku cofa całość; wynik widać dopiero po zatwierdzeniu transakcji.
- **Odczyt.** `get_result`/`get_manifest` widzą wyłącznie zatwierdzone przebiegi; `get_result` weryfikuje skrót manifestu, a `open_document`/`open_artifact` skrót bajtów. Niezgodność to `IntegrityViolationError`, nigdy cicha podmiana.
- **Restart.** `recover_after_restart()`: przerwane `running` kończą jako `done/technical_error` z artefaktem raportu `run_interrupted` (ponowienie to nowy `run_id`, a odświeżenie niczego nie uruchamia); zatwierdzony wynik z brakującym lub zmienionym manifestem albo artefaktem jest jawnie zamieniany na `technical_error` (`storage_inconsistent`); usuwane są niepełne pliki tymczasowe. Operacja jest idempotentna.
- Silnik: `journal_mode=WAL` dla bazy plikowej, `busy_timeout=5000`; zapisy zawsze przez `write_transaction`.

## Konsekwencje

- Usunięto zależność pg8000, adresy PostgreSQL i zapytania do katalogów serwera (`information_schema`). W repo nie znaleziono usługi PostgreSQL w Docker/Compose ani kodu UI/API zależnego od PostgreSQL; nic więcej do usunięcia. Nie ma automatycznego importu danych ze starego PostgreSQL.
- Migracje to pliki SQL (`0001_initial`, `0002_data_repository`) wykonywane przez SQLAlchemy; każdy plik razem z wpisem wersji jest jedną transakcją, ponowne uruchomienie niczego nie zmienia. Pliki `.sql` są dołączone do pakietu pip (`package-data`). Alembic nie jest potrzebny w obecnym zakresie.
- SQLite upraszcza dostarczenie pip i testy bez serwera, ale serializuje zapisy: jeden proces wykonawczy jest zakładaną granicą (zgodnie z §9 dla v1). Baza i katalog roboczy wymagają kopii zapasowych; spójność uzgadnia `recover_after_restart`, a nie kopia „na gorąco”.
- SQLAlchemy jest już przypiętą zależnością (licencja MIT); nie dodajemy sterownika ani infrastruktury.
- Zielone testy na SQLite nie dowodzą gotowości do wdrożenia skalowanego.

## Warunki powrotu do PostgreSQL

Powrót wymaga decyzji użytkownika uzasadnionej pomiarami współbieżności lub wymaganiami wdrożenia, nowego ADR oraz **drugiej implementacji `DataRepository` przez SQLAlchemy** (bez sterownika poza adapterem silnika). Testy kontraktowe `tests/integration/test_data_repository.py` (rewizje, atomowy `commit_run`, odczyt tylko zatwierdzonych wyników, uzgodnienie po restarcie) muszą przechodzić dla obu baz; fixture `repository` jest jedynym miejscem wyboru implementacji. Migrację istniejących danych trzeba zaprojektować osobno. Do czasu decyzji dodatnie zapisy o PostgreSQL w ADR-002 i architekturze §9–§10 pozostają odłożone.
