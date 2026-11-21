---
wersja: 0.3.0
aktualizacja: 2026-11-21
status: plan implementacji — decyzja zespołu 2026-11-21
---

# Postgres + przeglądarka bazy + Docker — plan implementacji

> **Decyzja zespołu (2026-11-21, obowiązująca).** Zakres i kolejność tego planu są obowiązujące dla bieżącego przebiegu: **Postgres, przeglądarka bazy i Docker powstają teraz**; silnik ekstrakcji, CLI `run` i „główne GUI" (wgrywanie PDF-ów) zostają na później. Rozstrzygnięcie kontrolera z 2026-11-21, według którego planem zapisu pozostawał [plan wdrożenia](2026-11-21-backend-fastapi-postgres-ui.md) z silnikiem najpierw (zadania 3–9), **zostało przez zespół odwołane** 2026-11-21. Z rozstrzygnięcia zachowano: komendę `import-organizer` (zadanie 2 tego planu, w masterze zadanie 10), montaż materiałów organizatora tylko do odczytu w Compose (zadanie 5, master 13), kryteria akceptacji jako podstawę skryptów `verify_docker.*` (zadanie 6, master 15) oraz powstanie ADR-002 przy zadaniu 5 (master 13). W razie rozbieżności treści zadań z masterem obowiązuje ten dokument.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Działający staw: kontener z PostgreSQL, aplikacja FastAPI serwująca przeglądarkę bazy z realnymi danymi organizatora, uruchamialne jednym `docker compose up --build`.

**Architecture:** Warstwa dostępu do bazy (`db/`) na SQLAlchemy 2.0 Core + pg8000 z idempotentnymi migracjami SQL. Dane w bazie pochodzą z importu referencyjnych JSON-ów organizatora (`import-organizer`) — realnych, nie atrapowych. UI to własna przeglądarka bazy na Jinja2 (bez CDN, bez etapu budowania) serwowana przez FastAPI. Baza jest opcjonalna: bez `DATABASE_URL` aplikacja i UI działają, UI pokazuje banner „baza wyłączona". Docker: `python:3.13.18-slim` bez roota, Compose z usługami `api` i `db`.

**Tech Stack:** Python 3.13 (kontener) / 3.11 (lokalna iteracja), FastAPI, Uvicorn, pydantic v2, Jinja2, SQLAlchemy 2.1.9 Core, pg8000, pypdfium2, pytest, httpx (TestClient), Docker + Compose, PostgreSQL 16-alpine.

**Spec:** `docs/superpowers/specs/2026-11-21-postgres-ui-docker-design.md` — przebieg jest częścią planu [2026-11-21-backend-fastapi-postgres-ui.md](2026-11-21-backend-fastapi-postgres-ui.md) (zadania 10–13 + ADR-002).

## Global Constraints

- `docs/02-materialy/` to materiał organizatora: **zakaz modyfikacji**; import tylko czyta.
- Materiały organizatora muszą pozostać bajtowo zgodne z `docs/02-materialy/manifest.json`; przed każdym commitem `python scripts/verify_docs.py` musi zwrócić `OK`.
- `docs/superpowers/specs/` i `docs/superpowers/plans/` to katalogi wyjątków — wyłącznie tam trafiają notatki robocze poza materiałem organizatora.
- Zależności przypięte w `apps/backend/requirements.txt`; nic nowego nie dochodzi (SQLAlchemy, pg8000, jinja2, fastapi, pypdfium2 są już na liście).
- Klucze API i hasło bazy wyłącznie w `.env` (ignorowanym przez Git); `.env.example` bez wartości.
- Dokumentacja, komunikaty CLI i nazwy testów po polsku; **identyfikatory w kodzie po angielsku**.
- Baza jest **opcjonalna**: kod nie wymaga `DATABASE_URL` i nie wybucha bez niego.
- Każdy commit: `python scripts/verify_docs.py` OK, `python scripts/validate_api.py --stage all` OK, `python -m pytest` OK.
- Zmiana stosu wymaga ADR z konsekwencjami (ADR-002 powstaje w zadaniu 6).

## Review Focus

1. **Brak `DATABASE_URL`** → API i UI renderują się, UI pokazuje banner „baza wyłączona", żadna strona nie zwraca 500.
2. **Postgres jeszcze nie gotowy przy starcie kontenera** → aplikacja startuje z `database: down` zamiast awarii; Compose czeka na healthcheck bazy.
3. **Migracja uruchomiona dwa razy** → druga jest pusta (brak nowych wersji), `schema_migrations` zawiera jedną wersję.
4. **Materiały organizatora nie zamontowane w kontenerze** → `import-organizer` kończy się czytelnym komunikatem i kodem wyjścia ≠ 0, bez tracebacku.
5. **Zapytanie zmieniające dane w konsoli SQL UI** (`DELETE`/`UPDATE`/`DROP`) → odrzucone, baza bez zmian.

---

### Task 1: Warstwa Postgres — migracje, migrator, repozytorium

**Files:**
- Create: `apps/backend/odwolania2json/config.py`
- Create: `apps/backend/odwolania2json/db/__init__.py`
- Create: `apps/backend/odwolania2json/db/migrations/0001_initial.sql`
- Create: `apps/backend/odwolania2json/db/migrate.py`
- Create: `apps/backend/odwolania2json/db/repository.py`
- Create: `apps/backend/odwolania2json/cli.py`
- Modify: `apps/backend/odwolania2json/__main__.py`
- Modify: `apps/backend/requirements.txt` (bez zmian — SQLAlchemy i pg8000 już są)
- Test: `tests/unit/test_config.py`, `tests/integration/test_db.py`

**Interfaces:**
- Produces:
  - `odwolania2json.config.Settings` — frozen dataclass: `input_dir: Path`, `output_dir: Path`, `database_url: str | None`, `llm_base_url: str | None`, `llm_model: str | None`, `llm_api_key: str | None`, `ocr_enabled: bool`, `docs_enabled: bool`, `web_dir: Path`; `Settings.from_env(env: Mapping[str, str] | None = None) -> Settings`
  - `odwolania2json.db.migrate.MIGRATIONS_DIR: Path`
  - `odwolania2json.db.migrate.migrate(database_url: str) -> list[str]` — zwraca listę zastosowanych wersji, każda w osobnej transakcji, już zastosowane pomijane
  - `odwolania2json.db.migrate.applied_versions(database_url: str) -> list[str]`
  - `odwolania2json.db.repository.normalize_url(database_url: str) -> str` — `postgresql://` i `postgres://` → `postgresql+pg8000://`
  - `odwolania2json.db.repository.is_configured(database_url: str | None) -> bool`
  - `odwolania2json.db.repository.DocumentRepository(database_url: str)` — metody zapisu: `upsert_document(document_id, filename, sha256, size_bytes, source_path, page_count, has_text_layer) -> None`, `upsert_run(run_id, status, documents_count, duration_ms) -> None`, `upsert_extraction(extraction_id, document_id, run_id, document_class, schema_version, payload, evidence) -> None`; metody odczytu: `count_documents() -> int`, `count_extractions() -> int`, `count_runs() -> int`, `class_counts() -> list[dict]`, `list_documents(limit=50, offset=0, name_filter=None, document_class=None) -> list[dict]`, `get_document(document_id) -> dict | None`, `list_extractions(limit=50, offset=0) -> list[dict]`, `get_extraction(document_id) -> dict | None`, `list_runs(limit=50, offset=0) -> list[dict]`, `list_tables() -> list[str]`, `list_columns(table_name) -> list[dict]`, `applied_migrations() -> list[dict]`, `run_select(sql: str) -> list[dict]`
  - `odwolania2json.db.repository.ReadOnlySqlError(RuntimeError)` — rzucany przez `run_select` dla zapytań niebędących odczytem
  - CLI: `python -m odwolania2json migrate [--database-url URL]` — nakłada migracje i wypisuje po jednej linii na wersję; bez `DATABASE_URL` wypisuje „pominięto: baza nie skonfigurowana" i kończy się kodem 0
- Konsumuje: nic (pakiet startuje od `odwolania2json/__init__.py`).

- [ ] **Step 1: Napisz testy konfiguracji i normalizacji URL**

```python
# tests/unit/test_config.py
def test_settings_from_env_reads_database_url():
    settings = Settings.from_env({"DATABASE_URL": "postgresql://u:p@h:5432/d"})
    assert settings.database_url == "postgresql://u:p@h:5432/d"


def test_settings_without_database_url_is_usable():
    settings = Settings.from_env({})
    assert settings.database_url is None
    assert settings.docs_enabled is False


def test_normalize_url_switches_to_pg8000_driver():
    assert normalize_url("postgresql://u:p@h/db") == "postgresql+pg8000://u:p@h/db"
```

- [ ] **Step 2: Uruchom test, ma paść**

Run: `python -m pytest tests/unit/test_config.py -v`
Expected: FAIL — brak modułu `config`.

- [ ] **Step 3: Zaimplementuj `config.py`**

`Settings.from_env` czyta `INPUT_DIR` (domyślnie `input`), `OUTPUT_DIR` (domyślnie `output`), `DATABASE_URL`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, `OCR_ENABLED` (`0`/`1`, domyślnie `0`), `O2J_DOCS_ENABLED` (domyślnie `0`), `O2J_WEB_DIR` (domyślnie `<repo>/apps/web`, liczone jako `Path(__file__).resolve().parents[2] / "web"`).

- [ ] **Step 4: Napisz testy bazy**

```python
# tests/integration/test_db.py
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="brak DATABASE_URL")

def test_migrate_creates_expected_tables():
    # po migrate() istnieją documents, runs, extractions, schema_migrations

def test_migrate_is_idempotent():
    # drugie migrate() zwraca []

def test_upsert_document_is_idempotent_by_sha256():
    # ten sam sha256 dwa razy -> jeden wiersz

def test_run_select_rejects_mutation():
    # run_select("DELETE FROM documents") -> ReadOnlySqlError, baza bez zmian

def test_run_select_returns_rows():
    # run_select("SELECT 1 AS x") -> [{"x": 1}]
```

- [ ] **Step 5: Uruchom testy, mają paść (albo zostać pominięte bez bazy)**

Run: `python -m pytest tests/integration/test_db.py -v`
Expected: SKIPPED bez `DATABASE_URL`; z bazą — FAIL, bo modułu `db` nie ma.

- [ ] **Step 6: Napisz migrację `0001_initial.sql`**

Tabele zgodne ze specyfikacją §8: `documents(id uuid pk, filename text not null, sha256 text not null unique, size_bytes bigint, source_path text, page_count int, has_text_layer bool, created_at timestamptz not null default now())`, `runs(id uuid pk, started_at timestamptz not null default now(), finished_at timestamptz, status text not null, duration_ms int, documents_count int not null default 0)`, `extractions(id uuid pk, document_id uuid not null references documents(id), run_id uuid not null references runs(id), class text not null, schema_version text not null, payload jsonb not null, evidence jsonb not null, created_at timestamptz not null default now())`. Indeksy: `documents(sha256)`, `extractions(document_id)`. Plik używa `CREATE TABLE IF NOT EXISTS`.

- [ ] **Step 7: Zaimplementuj `migrate.py` i `repository.py`**

`migrate()` tworzy tabelę `schema_migrations(version text primary key, applied_at timestamptz not null default now())` (jeśli nie istnieje), wczytuje `*.sql` z `MIGRATIONS_DIR` posortowane po nazwie, każdy niezastosowany plik wykonuje w jednej transakcji i dopisuje wersję. `repository.py` używa `sqlalchemy.create_engine(normalize_url(url), future=True)` i `text()` z parametrami (`bindparam`), nigdy przez f-stringowe sklejanie SQL. `run_select` odrzuca zapytanie, które nie zaczyna się od `SELECT` albo `WITH` (po usunięciu białych znaków i `--` komentarzy) albo zawiera słowa `insert`, `update`, `delete`, `drop`, `alter`, `truncate`, `create`, `grant`, `revoke`, `copy`, `call`, `do`, `vacuum`, `analyze` — i rzuca `ReadOnlySqlError`; dodatkowo wykonuje zapytanie w transakcji `SET TRANSACTION READ ONLY`.

- [ ] **Step 8: Przenieś CLI do `cli.py` i dodaj podkomendę `migrate`**

`apps/backend/odwolania2json/cli.py` zawiera `build_parser()` i `main(argv: list[str] | None = None) -> int`; `__main__.py` robi `from .cli import APP_NAME, build_parser, main` i eksponuje je dalej (test `tests/test_scaffolding.py` importuje `main` z `odwolania2json.__main__` — ten import musi działać). Parser ma podkomendę `migrate` z opcją `--database-url` (domyślnie ze zmiennej `DATABASE_URL`). `main([])` nadal wypisuje pomoc i zwraca 0.

- [ ] **Step 9: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_config.py tests/integration/test_db.py tests/test_scaffolding.py -v`
Expected: PASS (testy DB SKIPPED bez `DATABASE_URL`).

- [ ] **Step 10: Uruchom testy bazy na prawdziwym Postgresie z Dockera**

Run:
```
docker run -d --name o2j-test-pg -e POSTGRES_USER=o2j -e POSTGRES_PASSWORD=o2j -e POSTGRES_DB=o2j -p 5433:5432 postgres:16-alpine
$env:DATABASE_URL='postgresql://o2j:o2j@127.0.0.1:5433/o2j'
python -m pytest tests/integration/test_db.py -v
```
Expected: PASS — tabele utworzone, migracja idempotentna, `run_select` odrzuca mutację.

- [ ] **Step 11: Commit**

```bash
git add apps/backend/odwolania2json/db apps/backend/odwolania2json/cli.py apps/backend/odwolania2json/__main__.py apps/backend/odwolania2json/config.py tests/unit/test_config.py tests/integration/test_db.py
git commit -m "feat: warstwa Postgres z migracjami i repozytorium"
```

---

### Task 2: Import referencyjnych danych organizatora

**Files:**
- Create: `apps/backend/odwolania2json/db/import_organizer.py`
- Modify: `apps/backend/odwolania2json/cli.py` (podkomenda `import-organizer`)
- Test: `tests/unit/test_import_organizer.py`, `tests/integration/test_import_organizer.py`

**Interfaces:**
- Produces:
  - `odwolania2json.db.import_organizer.ImportReport` — dataclass `documents: int`, `extractions: int`, `runs: int`, `skipped: list[str]`, `contract_mismatches: list[str]`
  - `odwolania2json.db.import_organizer.KLASY_PDF: tuple[tuple[str, str, str], ...]` — pary `(klasa, nazwa PDF, nazwa JSON)`: `("odwolanie", "odwolanie.pdf", "odwolanie.json")`, `("pelnomocnictwo", "pelnomocnictwo.pdf", "pelnomocnictwo.json")`, `("przelew", "potwierdzenie_przelewu.pdf", "przelew.json")`
  - `odwolania2json.db.import_organizer.pair_documents(data_dir: Path) -> list[tuple[str, Path, Path]]` — lista `(klasa, ścieżka PDF, ścieżka JSON)` dla każdego katalogu `przyklad_*`; para nieznana (brak pliku PDF lub JSON) trafia do raportu
  - `odwolania2json.db.import_organizer.read_pdf_metadata(pdf_path: Path) -> tuple[int, bool]` — `(liczba_stron, ma_warstwe_tekstowa)` z `pypdfium2`
  - `odwolania2json.db.import_organizer.import_organizer(data_dir: Path, repository: DocumentRepository) -> ImportReport`
  - CLI: `python -m odwolania2json import-organizer --data KATALOG [--database-url URL]`
- Konsumuje: `DocumentRepository` z zadania 1 (metody `upsert_document`, `upsert_run`, `upsert_extraction`), `odwolania2json_contracts.models` (walidacja).

- [ ] **Step 1: Napisz testy jednostkowe parowania i metadanych PDF**

```python
def test_pair_documents_finds_three_classes_per_case():
    pary = pair_documents(MAT_DIR)
    assert len(pary) == 180
    assert {klasa for klasa, _, _ in pary} == {"odwolanie", "pelnomocnictwo", "przelew"}


def test_import_missing_data_directory_reports_error(tmp_path, capsys):
    # brak katalogu danych -> komunikat na stdout i kod wyjscia 1, bez tracebacku
    assert main(["import-organizer", "--data", str(tmp_path / "nie-ma")]) == 1
    assert "nie istnieje" in capsys.readouterr().out


def test_read_pdf_metadata_reads_pages_and_text_layer():
    liczba, ma_tekst = read_pdf_metadata(MAT_DIR / "przyklad_01" / "odwolanie.pdf")
    assert liczba >= 1
    assert ma_tekst is True
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_import_organizer.py -v`
Expected: FAIL — brak modułu `import_organizer`.

- [ ] **Step 3: Zaimplementuj parowanie i metadane PDF**

`pair_documents` iteruje po katalogach `przyklad_*` posortowanych po nazwie i dla każdej pary z `KLASY_PDF` sprawdza obecność obu plików; brak któregokolwiek oznacza pominięcie (nazwa pliku trafia do `skipped`). `read_pdf_metadata` używa `pypdfium2.PdfDocument(path)`, zwraca `len(pdf)` i `ma_warstwe_tekstowa` = czy **którakolwiek** strona ma niepusty tekst (czytany przez `page.get_textpage().get_text_range()`).

- [ ] **Step 4: Napisz testy integracyjne importu**

```python
# tests/integration/test_import_organizer.py
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="brak DATABASE_URL")


def test_import_inserts_documents_extractions_and_runs():
    report = import_organizer(MAT_DIR, repo)
    assert report.documents == 180
    assert report.extractions == 180
    assert report.runs == 60


def test_import_is_idempotent():
    import_organizer(MAT_DIR, repo)
    import_organizer(MAT_DIR, repo)
    assert repo.count_documents() == 180
    assert repo.count_extractions() == 180
    assert repo.count_runs() == 60


def test_import_reports_contract_mismatch_without_dropping_row():
    report = import_organizer(MAT_DIR, repo)
    assert len(report.contract_mismatches) == 5
    assert repo.count_extractions() == 180


def test_import_records_payload_and_empty_evidence():
    import_organizer(MAT_DIR, repo)
    dokument = repo.list_documents(limit=1)[0]
    ekstrakcja = repo.get_extraction(dokument["id"])
    assert ekstrakcja["payload"]
    assert ekstrakcja["evidence"] == {}
```

- [ ] **Step 5: Uruchom testy na bazie testowej**

Run:
```
$env:DATABASE_URL='postgresql://o2j:o2j@127.0.0.1:5433/o2j'
python -m pytest tests/integration/test_import_organizer.py -v
```
Expected: PASS — 180 dokumentów, 180 ekstrakcji, 60 przebiegów, 5 rozjazdów w raporcie.

- [ ] **Step 6: Zaimplementuj `import_organizer` i podkomendę CLI**

Identyfikatory liczone deterministycznie, żeby powtórny import nie duplikował: `document_id = uuid.uuid5(uuid.NAMESPACE_URL, "odwolania2json/document/" + sha256)`, `run_id = uuid.uuid5(uuid.NAMESPACE_URL, "odwolania2json/run/" + nazwa_katalogu_sprawy)`, `extraction_id = uuid.uuid5(uuid.NAMESPACE_URL, f"odwolania2json/extraction/{run_id}/{document_id}")`. Jeden przebieg na sprawę (`runs.status = "import"`, `documents_count = 3`). `payload` = referencyjny JSON organizatora jako słownik, `evidence` = `{}`, `schema_version` = `odwolania2json_contracts.__version__`. Każdy JSON jest walidowany modelem z `odwolania2json_contracts.models` (`Odwolanie`, `Pelnomocnictwo`, `Przelew`); niezgodność **nie blokuje** importu — trafia do `contract_mismatches` jako `f"{nazwa_pliku}: {opis_błędu}"`. Podkomenda `import-organizer --data KATALOG` wypisuje raport (wstawione dokumenty, ekstrakcje, przebiegi, pominięte pliki, rozjazdy) i kończy się kodem 0; gdy `--data` wskazuje nieistniejący katalog, wypisuje czytelny komunikat i kończy się kodem 1.

- [ ] **Step 7: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_import_organizer.py tests/integration/test_import_organizer.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add apps/backend/odwolania2json/db/import_organizer.py apps/backend/odwolania2json/cli.py tests/unit/test_import_organizer.py tests/integration/test_import_organizer.py
git commit -m "feat: import referencyjnych danych organizatora do bazy"
```

---

### Task 3: Szkielet aplikacji FastAPI

**Files:**
- Create: `apps/backend/odwolania2json/api/__init__.py`
- Create: `apps/backend/odwolania2json/api/app.py`
- Create: `apps/backend/odwolania2json/api/routes.py`
- Modify: `packages/contracts/odwolania2json_contracts/openapi.yaml` (odpowiedź `/healthz`), `packages/contracts/odwolania2json_contracts/models.py` (regenerowany)
- Test: `tests/integration/test_api.py`

**Interfaces:**
- Produces:
  - `odwolania2json.api.app.create_app(settings: Settings | None = None) -> FastAPI` — montuje trasy i UI, `docs_url=None` gdy `settings.docs_enabled` jest fałszywe
  - `odwolania2json.api.app.app` — instancja modułu (`create_app()`), punkt wejścia Uvicorn `odwolania2json.api.app:app`
  - `odwolania2json.api.routes.healthz(request: Request) -> dict` — zwraca `{"status": "ok", "database": "up" | "down"}`
- Konsumuje: `Settings` z zadania 1, `DocumentRepository` i `is_configured` z zadania 1.

- [ ] **Step 1: Napisz testy API**

```python
def test_healthz_ok_without_database():
    with TestClient(create_app(Settings.from_env({}))) as client:
        odpowiedz = client.get("/healthz")
    assert odpowiedz.status_code == 200
    assert odpowiedz.json() == {"status": "ok", "database": "down"}

def test_healthz_reports_database_state():
    # z DATABASE_URL wskazującym na żywą bazę -> "database": "up"

def test_docs_are_disabled_by_default():
    with TestClient(create_app(Settings.from_env({}))) as client:
        assert client.get("/docs").status_code == 404

def test_healthz_reports_down_when_database_unreachable():
    # DATABASE_URL wskazuje na zamkniety port -> "database": "down", bez wyjatku
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/integration/test_api.py -v`
Expected: FAIL — brak modułu `api`.

- [ ] **Step 3: Zaimplementuj `api/app.py` i `api/routes.py`**

`create_app` tworzy FastAPI z tytułem „Odwołania2JSON", ustawia `docs_url=None` i `redoc_url=None` gdy `docs_enabled` jest fałszywe, montuje `StaticFiles` z `settings.web_dir / "static"` (katalog może nie istnieć — wtedy bez montowania) i `Jinja2Templates(directory=str(settings.web_dir / "templates"))` (katalog może nie istnieć — wtedy `templates=None`). `/healthz` sprawdza bazę: `is_configured(settings.database_url)` i próbne połączenie `SELECT 1`; przy błędzie zwraca `"down"` zamiast wyjątku.

Specyfikacja `openapi.yaml` opisuje odpowiedź `/healthz` przez nowy schemat `HealthStatus` (`status`: string, `database`: string z enum `up`/`down`), a `paths./healthz.get.responses.200.content` wskazuje na ten schemat. Po zmianie specyfikacji: `python scripts/generate_contracts.py` (modele generowane, nie edytowane ręcznie).

- [ ] **Step 4: Uruchom testy, mają przejść**

Run: `python -m pytest tests/integration/test_api.py -v`
Expected: PASS.

- [ ] **Step 5: Sprawdź zgodność kontraktu**

Run: `python scripts/validate_api.py --stage app`
Expected: `OK` dla etapu `app` — `app.openapi()` zgadza się ze specyfikacją (ścieżka `/healthz`, `operationId: healthz`).

- [ ] **Step 6: Commit**

```bash
git add apps/backend/odwolania2json/api tests/integration/test_api.py
git commit -m "feat: szkielet aplikacji FastAPI z healthz"
```

---

### Task 4: UI przeglądarki bazy

**Files:**
- Create: `apps/web/templates/base.html`, `apps/web/templates/pulpit.html`, `apps/web/templates/dokumenty.html`, `apps/web/templates/ekstrakcje.html`, `apps/web/templates/ekstrakcja.html`, `apps/web/templates/przebiegi.html`, `apps/web/templates/schemat.html`, `apps/web/templates/konsola.html`
- Create: `apps/web/static/style.css`, `apps/web/static/app.js`
- Create: `apps/backend/odwolania2json/api/ui.py`
- Modify: `apps/backend/odwolania2json/api/app.py` (montowanie tras UI)
- Test: `tests/integration/test_ui.py`

**Interfaces:**
- Produces trasy (wszystkie `GET`):
  - `/` — pulpit: kafelki dokumentów/ekstrakcji/przebiegów, rozkład klas, tabela zastosowanych migracji
  - `/dokumenty` — tabela `documents` z filtrem `?nazwa=`; kolumny: nazwa, klasa, strony, rozmiar, data, link do wyniku
  - `/ekstrakcje` — lista `extractions`
  - `/ekstrakcje/{document_id}` — szczegóły: `payload` i `evidence` obok siebie + tabela „pole → dowód"
  - `/przebiegi` — tabela `runs`
  - `/schemat` — tabele z `information_schema` (kolumna, typ, nullability)
  - `/konsola` — `?sql=` wykonuje wyłącznie `SELECT`, wynik jako tabela; zapytanie zmieniające dane odrzucone z komunikatem
- Konsumuje: `DocumentRepository` z zadania 1 (`list_documents`, `get_document`, `list_extractions`, `get_extraction`, `list_runs`, `list_tables`, `list_columns`, `applied_migrations`, `run_select`, `class_counts`, `count_documents`, `count_extractions`, `count_runs`).

- [ ] **Step 1: Napisz testy UI**

```python
def test_pulpit_renders():
    # GET / -> 200, zawiera "Odwołania2JSON"

def test_pulpit_shows_banner_without_database():
    # bez DATABASE_URL -> zawiera "baza wyłączona"

def test_documents_page_lists_documents():
    # z bazą zimportowaną -> zawiera nazwę pliku PDF

def test_extractions_page_and_detail():
    # GET /ekstrakcje -> 200; GET /ekstrakcje/{id} -> 200, zawiera "payload" i "evidence"

def test_schema_page_lists_tables():
    # zawiera "documents" i "extractions"

def test_sql_console_runs_select():
    # GET /konsola?sql=SELECT+1+AS+x -> 200, zawiera "x"

def test_sql_console_refuses_mutation():
    # ?sql=DELETE+FROM+documents -> komunikat o blokadzie, baza bez zmian

def test_unknown_document_returns_404():
    # GET /ekstrakcje/00000000-0000-0000-0000-000000000000 -> 404
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/integration/test_ui.py -v`
Expected: FAIL — brak szablonów i tras UI.

- [ ] **Step 3: Zaimplementuj szablony i trasy**

`base.html`: nagłówek z nazwą projektu i stanem bazy („baza włączona" / „baza wyłączona"), nawigacja (pulpit, dokumenty, ekstrakcje, przebiegi, schemat, konsola), blok treści. Szablony używają `url_for`. `style.css` i `app.js` leżą w `static/`, bez zewnętrznych zasobów (żadnego CDN). `api/ui.py` pobiera repozytorium z `request.app.state.repository` (ustawiane w `create_app`; `None`, gdy brak `DATABASE_URL`) i przy `None` renderuje stronę z bannerem „baza wyłączona" zamiast wyjątku. Ekstrakcja szczegółowa pokazuje `payload` (pretty-printed JSON) i `evidence` obok siebie oraz tabelę „pole → dowód" zbudowaną z `evidence`.

- [ ] **Step 4: Uruchom testy, mają przejść**

Run: `python -m pytest tests/integration/test_ui.py -v`
Expected: PASS (testy z bazą SKIPPED bez `DATABASE_URL`).

- [ ] **Step 5: Uruchom testy UI na bazie testowej z danymi**

Run:
```
$env:DATABASE_URL='postgresql://o2j:o2j@127.0.0.1:5433/o2j'
python -m odwolania2json import-organizer --data docs/02-materialy/organizator-uzp/dane
python -m pytest tests/integration/test_ui.py -v
```
Expected: PASS — strony pokazują 180 dokumentów, 180 ekstrakcji, 60 przebiegów.

- [ ] **Step 6: Commit**

```bash
git add apps/web apps/backend/odwolania2json/api tests/integration/test_ui.py
git commit -m "feat: UI przegladarki bazy Postgres"
```

---

### Task 5: Docker, Compose i skrypty startowe

**Files:**
- Create: `infra/docker/Dockerfile`, `infra/docker/entrypoint.sh`, `infra/docker/postgres/init.sql`
- Create: `docker-compose.yml`, `start.bat`, `start.sh`
- Modify: `.env.example`
- Test: `tests/integration/test_docker_files.py`

**Interfaces:**
- Produces: obraz `odwolania2json:local` (FastAPI na porcie 8000, healthcheck, użytkownik bez roota); `docker compose up --build` stawia `api` i `db`; `start.bat` / `start.sh` uruchamiają Compose i podają instrukcję fallbacku.

- [ ] **Step 1: Napisz test statyczny plików Dockera**

```python
def test_dockerfile_uses_pinned_python_image():
    # zawiera "FROM python:3.13.18-slim" i nie zawiera ":latest"

def test_dockerfile_creates_non_root_user():
    # zawiera "useradd" i linię "USER "

def test_dockerfile_has_healthcheck():
    # zawiera "HEALTHCHECK" i "/healthz"

def test_compose_defines_api_and_db():
    # sekcje "api:" i "db:", postgres:16-alpine, healthcheck

def test_env_example_has_no_secrets():
    # wartości kluczy puste
```

- [ ] **Step 2: Uruchom test, ma paść**

Run: `python -m pytest tests/integration/test_docker_files.py -v`
Expected: FAIL — brak plików.

- [ ] **Step 3: Napisz Dockerfile, Compose i skrypty**

`Dockerfile`: `FROM python:3.13.18-slim`, `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 O2J_WEB_DIR=/app/apps/web`, `WORKDIR /app`, `RUN useradd -m -u 10001 app`, `COPY packages/contracts /app/packages/contracts`, `COPY apps/backend /app/apps/backend`, `COPY apps/web /app/apps/web`, `COPY tests /app/tests`, `RUN pip install --no-cache-dir ./packages/contracts ./apps/backend -r apps/backend/requirements-ocr.txt`, `RUN mkdir -p /app/input /app/output && chown -R app:app /app/input /app/output`, `USER app`, `EXPOSE 8000`, `HEALTHCHECK` odpytujący `/healthz`, `ENTRYPOINT ["/app/infra/docker/entrypoint.sh"]`, `CMD ["uvicorn", "odwolania2json.api.app:app", "--host", "0.0.0.0", "--port", "8000"]`.

`entrypoint.sh`: `set -e`; jeśli `DATABASE_URL` jest ustawione, `python -m odwolania2json migrate` (migracje idempotentne), potem `exec uvicorn …`.

`docker-compose.yml`: `api` (build z `infra/docker/Dockerfile`, port `8000:8000`, `depends_on: db: condition: service_healthy`, wolumeny `./input:/app/input`, `./output:/app/output`, `./docs/02-materialy:/materials:ro`, zmienne `DATABASE_URL` i `O2J_WEB_DIR`), `db` (`postgres:16-alpine`, `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` z `.env` z wartością domyślną `o2j`, healthcheck `pg_isready`, wolumen `pgdata` i `./infra/docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro`).

`start.bat` / `start.sh`: `docker compose up --build`; gdy Dockera brak — instrukcja `pip install -r requirements.txt` i `python -m odwolania2json run`.

`infra/docker/postgres/init.sql`: tylko bootstrap (np. `SET client_encoding = 'UTF8';`), **bez** schematu aplikacji.

- [ ] **Step 4: Uruchom test statyczny, ma przejść**

Run: `python -m pytest tests/integration/test_docker_files.py -v`
Expected: PASS.

- [ ] **Step 5: Zbuduj obraz**

Run: `docker compose build`
Expected: obraz zbudowany bez błędów na `python:3.13.18-slim`.

- [ ] **Step 6: Uruchom stos i sprawdź zdrowie**

Run:
```
docker compose up -d
docker compose ps
curl http://localhost:8000/healthz
```
Expected: `api` i `db` w stanie `running` (db `healthy`), `/healthz` → `{"status":"ok","database":"up"}`.

- [ ] **Step 7: Zaimportuj dane w kontenerze**

Run: `docker compose exec api python -m odwolania2json import-organizer --data /materials/organizator-uzp/dane`
Expected: raport 180 dokumentów, 180 ekstrakcji, 60 przebiegów, 5 rozjazdów.

- [ ] **Step 8: Sprawdź UI i wiersze w bazie**

Run: `curl http://localhost:8000/` oraz `docker compose exec db psql -U o2j -d o2j -c "select count(*) from documents"`
Expected: strona 200 zawiera „Odwołania2JSON"; `documents` ma 180 wierszy.

- [ ] **Step 9: Uruchom testy w kontenerze**

Run: `docker compose exec api python -m pytest -v`
Expected: PASS na Pythonie 3.13.

- [ ] **Step 10: Posprzątaj**

Run: `docker compose down -v`
Expected: brak kontenerów i wolumenów po zatrzymaniu.

- [ ] **Step 11: Commit**

```bash
git add infra docker-compose.yml start.bat start.sh .env.example tests/integration/test_docker_files.py
git commit -m "feat: obraz Docker, Compose i skrypty startowe"
```

---

### Task 6: ADR-002, skrypty weryfikacji w Dockerze i dokumentacja

**Files:**
- Create: `docs/07-decyzje/ADR-002-fastapi-postgres-ui.md`
- Create: `scripts/verify_docker.ps1`, `scripts/verify_docker.sh`
- Modify: `README.md`, `docs/README.md`, `docs/04-architektura/README.md`, `docs/05-weryfikacja/README.md`, `CHANGELOG.md`, `VERSION`
- Test: `tests/integration/test_verify_scripts.py`

**Interfaces:**
- Produces: `scripts/verify_docker.ps1` (Windows) i `scripts/verify_docker.sh` (Linux) wykonujące 11 kroków ze specyfikacji §11.1 i zwracające kod wyjścia 0 dopiero po pełnym sukcesie; każdy krok wypisuje `OK <krok>` albo `FAIL <krok> <powód>`.

- [ ] **Step 1: Napisz testy statyczne skryptów**

```python
def test_verify_scripts_define_all_steps():
    # oba skrypty zawierają build, up, healthz, pytest, upload, ui, batch, down

def test_verify_scripts_fail_fast():
    # skrypty kończą się exit 1 po pierwszym FAIL
```

- [ ] **Step 2: Uruchom test, ma paść**

Run: `python -m pytest tests/integration/test_verify_scripts.py -v`
Expected: FAIL — brak skryptów.

- [ ] **Step 3: Napisz skrypty weryfikacyjne**

Kroki ze specyfikacji §11.1: build → up → healthcheck z bazą → healthz bez bazy → pytest w kontenerze → import danych → upload (pominięty w tym przebiegu: brak silnika — skrypt wypisuje `OK pominięto: brak silnika ekstrakcji`) → strony UI → wiersze w bazie → batch CLI (pominięty: brak silnika) → `down -v`. Kroki bez wsparcia silnika są pomijane z jawnym powodem, nie udają sukcesu.

- [ ] **Step 4: Napisz ADR-002**

Kontekst (FastAPI, Postgres opcjonalny, UI bez etapu budowania, OpenAPI jako źródło prawdy), decyzja, alternatywy (React/TypeScript, baza obowiązkowa, OCR w podstawie, pgAdmin zamiast własnego UI), konsekwencje (dodatkowa zależność, brak wymagania Node, warunki powrotu do Reacta), status „zaakceptowane 2026-11-21".

- [ ] **Step 5: Zaktualizuj dokumentację i wersjonowanie**

`VERSION` → `0.5.0`. `CHANGELOG.md` — sekcja 0.5.0. `README.md` — stan „aplikacja: warstwa Postgres, przeglądarka bazy i Docker", instrukcja uruchomienia (`docker compose up --build` i ścieżka `pip`), opis testu w Dockerze. `docs/README.md` — wiersz o nowym planie i projekcie przebiegu. `docs/04-architektura/README.md` — odsyłacz i status wdrożenia. `docs/05-weryfikacja/README.md` — stan pomiarów i odsyłacz do skryptów.

- [ ] **Step 6: Uruchom pełną kontrolę**

Run: `python scripts/verify_docs.py` oraz `python scripts/validate_api.py --stage all` oraz `python -m pytest -v`
Expected: trzy razy kod wyjścia 0.

- [ ] **Step 7: Commit**

```bash
git add docs README.md CHANGELOG.md VERSION scripts/verify_docker.ps1 scripts/verify_docker.sh tests/integration/test_verify_scripts.py
git commit -m "docs: ADR-002, skrypty weryfikacji w Dockerze i status wdrozenia"
```

---

## Śledzenie wykonania

- [ ] Task 1: Warstwa Postgres — migracje, migrator, repozytorium
- [ ] Task 2: Import referencyjnych danych organizatora
- [ ] Task 3: Szkielet aplikacji FastAPI
- [ ] Task 4: UI przeglądarki bazy
- [ ] Task 5: Docker, Compose i skrypty startowe
- [ ] Task 6: ADR-002, skrypty weryfikacji i dokumentacja
