---
wersja: 0.2.0
aktualizacja: 2026-11-21
status: wariant projektu — rozstrzygnięty przez kontrolera 2026-11-21
---

# Projekt przebiegu — Postgres, przeglądarka bazy i Docker

> **Rozstrzygnięcie kontrolera (2026-11-21).** Ten dokument powstał w trakcie implementacji jako wariant kolejności zadań. **Planem zapisu pozostaje** [plan wdrożenia](../plans/2026-11-21-backend-fastapi-postgres-ui.md): najpierw silnik ekstrakcji (zadania 3–9), potem Postgres, API, UI i Docker (10–13). Uzasadnienie: preselekcja jest mierzona w 100% wskaźnikiem F1, więc silnik daje wartość konkursową, a baza i UI są własnym dodatkiem, którego organizator nie wymaga. Z tego dokumentu **przyjęto do planu**: komenda `import-organizer` (zadanie 10), montaż materiałów organizatora tylko do odczytu w Compose (zadanie 13), kryteria akceptacji §4 jako podstawa skryptu `scripts/verify_docker.*` (zadanie 15) oraz powstanie ADR-002 w zadaniu 13, a nie 15. Wersja 0.1.0 deklarowała „zatwierdzone do implementacji" bez zatwierdzenia — zatwierdza zespół, nie autor dokumentu.

## 1. Cel

Ten przebieg dostarcza działający stos **Postgres + przeglądarka bazy + Docker**. Silnik ekstrakcji, CLI i „główne GUI" (wgrywanie PDF-ów) zostają na później i przyjdą w osobnym przebiegu.

Kryterium sukcesu: `docker compose up --build` stawia Postgres i aplikację, `/healthz` odpowiada, przeglądarka bazy pokazuje realne dane z referencyjnych JSON-ów organizatora, a testy przechodzą w kontenerze.

## 2. Co już jest ustalone

Kolejność i zakres pochodzą z planu [2026-11-21-backend-fastapi-postgres-ui.md](../../superpowers/plans/2026-11-21-backend-fastapi-postgres-ui.md), zadania 10–13, oraz ze specyfikacji [projekt-backend-fastapi-postgres-ui.md](../../04-architektura/projekt-backend-fastapi-postgres-ui.md). Ten dokument opisuje **tylko odstępstwa** od tych dokumentów.

| Obszar | Ustalenie | Źródło |
|---|---|---|
| Baza | PostgreSQL 16, SQLAlchemy 2.0 Core + pg8000, baza opcjonalna (bez `DATABASE_URL` kod działa) | specyfikacja §3, §8 |
| Schemat | `documents`, `runs`, `extractions` + `schema_migrations` | specyfikacja §8 |
| Migracje | pliki `NNNN_nazwa.sql`, nakładane idempotentnie, każda w transakcji | specyfikacja §8 |
| UI | własna przeglądarka bazy na Jinja2, bez CDN, bez etapu budowania, bez Node | specyfikacja §9, zadanie 12 planu |
| Strony UI | pulpit, dokumenty, ekstrakcje, przebiegi, schemat, konsola SQL (tylko `SELECT`) | zadanie 12 planu |
| Docker | `python:3.13.18-slim` (digest `sha256:e48f59cdba69…`), użytkownik bez roota, healthcheck na `/healthz` | specyfikacja §10 |
| Compose | usługi `api` i `db` (`postgres:16-alpine`), wolumeny `input`, `output`, `pgdata` | zadanie 13 planu |
| Kontrakt | `packages/contracts/odwolania2json_contracts/openapi.yaml` — jedyna kopia, modele generowane z niej | zadanie 2 planu, ADR-001 |

## 3. Odstępstwa od planu

### 3.1 Zadanie 11 w wersji szkieletowej

`create_app` montuje szablony UI, `/healthz` i statyki. Endpointy `POST /api/documents`, `GET /api/documents…` i `GET /api/classes` **czekają na silnik** (zadanie 9) i dojdą razem z nim — bez silnika nie miałyby wiarygodnej odpowiedzi.

Kontrakt OpenAPI zostaje w obecnej postaci: schematy trzech klas dokumentów + `PustyWynik` + ścieżka `/healthz`. `scripts/validate_api.py --stage app` porównuje `app.openapi()` ze specyfikacją i kończy się błędem przy rozjeździe.

### 3.2 Import referencyjnych danych organizatora

Nowa komenda CLI `python -m odwolania2json import-organizer --data KATALOG`:

- źródło: `docs/02-materialy/organizator-uzp/dane/przyklad_*/` — 60 spraw, po 3 klasy, razem 180 par PDF + JSON;
- mapowanie klas na pliki PDF: `odwolanie.json`↔`odwolanie.pdf`, `pelnomocnictwo.json`↔`pelnomocnictwo.pdf`, `przelew.json`↔`potwierdzenie_przelewu.pdf`;
- `documents`: `filename` (nazwa pliku PDF), `sha256` (liczony z PDF), `size_bytes`, `source_path` (ścieżka względna), `page_count` i `has_text_layer` (odczytane z PDF przez `pypdfium2`);
- `runs`: **60 przebiegów — po jednym na sprawę**, każdy z 3 dokumentami (`documents_count = 3`), `status = 'import'`;
- `extractions`: `class` z pary PDF/JSON, `payload` = referencyjny JSON organizatora jako `jsonb`, `evidence` = `{}` (referencje nie zawierają dowodu źródłowego — nie wymyślamy go), `schema_version` = wersja kontraktu;
- idempotencja: po `sha256` dokumentu; powtórny import aktualizuje wiersze, nie duplikuje;
- raport na stdout: liczba wstawionych dokumentów, ekstrakcji i przebiegów, lista pominiętych plików, lista rozjazdów kontraktu.

### 3.3 Rozjazdy kontraktu przy imporcie

Walidacja każdego JSON-a modelem pydantic z `odwolania2json_contracts` daje raport, **nie bramkę**: plik jest importowany, rozjazd trafia do raportu. Znane odchylenie: 5 spraw (19, 23, 25, 44, 55) ma `czynnosc_opis = "Odpowiedzi i wyjaśnienia do SWZ"`, a słownik `main` (`7590db8`) i kontrakt mają `"Odpowiedzi/wyjaśnienia do SWZ"` — to samo odchylenie opisane w specyfikacji §11.

### 3.4 Materiały organizatora poza obrazem

`docs/02-materialy/` nie trafia do obrazu (`.dockerignore`). W Compose katalog jest montowany tylko do odczytu (`./docs/02-materialy:/materials:ro`), a import w kontenerze idzie poleceniem `docker compose exec api python -m odwolania2json import-organizer --data /materials/organizator-uzp/dane`.

### 3.5 ADR-002 w tym przebiegu

Decyzja o stosie (FastAPI, Postgres opcjonalny, UI bez etapu budowania, OpenAPI jako źródło prawdy) wymaga ADR z konsekwencjami (`docs/07-decyzje/ADR-002-fastapi-postgres-ui.md`). Powstaje w tym przebiegu, nie dopiero w zadaniu 15.

## 4. Kryteria akceptacji

Dowód wymagany przed uznaniem przebiegu za zakończony:

1. `docker compose build` kończy się bez błędu na `python:3.13.18-slim`.
2. `docker compose up -d` stawia `api` i `db`; `db` przechodzi healthcheck, `api` raportuje `{"status":"ok"}` z `database: up`.
3. `docker compose exec api python -m pytest` przechodzi w kontenerze (Python 3.13).
4. `GET /` i strony UI zwracają 200; w HTML widać nazwę projektu i stan bazy.
5. `docker compose exec api python -m odwolania2json import-organizer --data /materials/organizator-uzp/dane` wstawia 180 dokumentów, 180 ekstrakcji i 60 przebiegów; raport wskazuje 5 rozjazdów kontraktu.
6. W bazie `documents`, `extractions` i `runs` mają wiersze odpowiadające importowi; konsola SQL w UI wykonuje `SELECT`, a `DELETE`/`UPDATE` są odrzucane.
7. Bez `DATABASE_URL` API i UI działają, UI pokazuje banner „baza wyłączona", nic nie wybucha.
8. `python scripts/verify_docs.py` oraz `python scripts/validate_api.py --stage all` kończą się kodem 0.

## 5. Poza zakresem

Silnik ekstrakcji, CLI `run`, endpointy API dokumentów, widok „PDF obok JSON", pomiar F1, CI i hook pre-commit. To są zadania 3–9, 14 i 16 planu.

## 6. Ryzyka

| Ryzyko | Skutek | Reakcja |
|---|---|---|
| `pg8000` + `postgresql+pg8000` z URL-em `postgresql://` | brak połączenia | normalizacja schematu URL w `config.py` i test |
| Kontener bez materiałów organizatora | import w kontenerze niemożliwy | montaż tylko do odczytu w Compose + instrukcja w README |
| Pusta baza przy starcie Compose | UI bez danych | migracje idempotentne + osobna komenda importu |
| Rozjazd 5 referencji ze słownikiem powodów | fałszywe FP w przyszłym pomiarze | znane odchylenie opisane w §11 specyfikacji; import raportuje, nie blokuje |
