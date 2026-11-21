---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: projekt zatwierdzony do implementacji
---

# Projekt implementacji — backend Python/FastAPI, Postgres, UI

Aktualizacja 0.6.1: w sprawie bazy pierwszeństwo ma [ADR-004](../07-decyzje/ADR-004-sqlalchemy-sqlite-bez-postgres.md): SQLAlchemy 2.x + SQLite za DataRepository. PostgreSQL jest odłożony. Poniższy plan zachowano jako historię, bez aktualnego zobowiązania do wdrożenia serwera PostgreSQL.

Gałąź: `feat/python-fastapi-docker`. Zakres: pionowa wartość ekstrakcji (reguły) + FastAPI + Docker + opcjonalny Postgres + UI bez etapu budowania + kontrakt OpenAPI jako źródło prawdy.

## 1. Cel i dlaczego teraz

Repo zawiera dokumentację i kopie materiałów organizatora, ale nie zawiera aplikacji. Preselekcja jest mierzona w 100% wskaźnikiem F1 na zbiorze testowym organizatora, więc każdy dzień bez działającego silnika jest dniem bez punktów. Celem tej gałęzi jest działający, mierzalny prototyp: PDF → JSON zgodny z kontraktem, uruchamiany lokalnie (CLI) i przez API, z Dockerem jako drogą odtwarzalną.

Wymagania organizatora, które gałąź musi spełnić od razu: Python 3.13+, `requirements.txt`, CLI, foldery `input`/`output`, wyłącznie komponenty open source, praca bez GPU, LLM przez API (nie instalowany na sprzęcie jury), ścisły JSON, obcy dokument → pusty JSON pod oryginalną nazwą. Kontrakt danych: [wymagania](../03-wymagania/README.md), [kontrakt](../03-wymagania/kontrakt-danych.md).

## 2. Zakres

### W zakresie

| Obszar | Zakres |
|---|---|
| Silnik | Odczyt tekstu z PDF (`pypdfium2`), wykrywanie braku warstwy tekstowej, klasyfikacja regułowa 3 klas + obcy, ekstrakcja regułowa + normalizatory, dowód źródłowy dla każdego pola |
| Kontrakt | Minimalny OpenAPI 3.1 jako źródło prawdy; modele pydantic generowane z niego; stała kolejność kluczy; `null` zamiast braku klucza; `czynnosc_opis` literalnie ze słownika 12 pozycji |
| CLI | `run` (batch `input` → `output`), `classify`, `extract`, `evaluate`, `serve` |
| API | FastAPI: upload i analiza PDF, odczyt dokumentów i wyników, health, spis klas |
| Postgres | Opcjonalny magazyn dokumentów, przebiegów i wyników; schemat SQL, warstwa dostępu, migracja idempotentna |
| UI | Przeglądarka bazy Postgres: tabele, wiersze, schemat, migracje, konsola SQL; widok PDF obok JSON odłożony na późniejszy przyrost (decyzja w ADR-002) |
| Dostarczenie | `Dockerfile` (`python:3.13-slim`, użytkownik bez roota, healthcheck), `docker-compose.yml` z Postgres, `start.bat` i `start.sh`, instrukcja uruchomienia |
| Weryfikacja | Testy jednostkowe, kontraktowe i wdrożeniowe; batch na 60 sprawach; własny F1 przybliżony; skrypt testu w Dockerze; raport w dokumentacji |

### Poza zakresem (jawnie)

LLM w wykonaniu (port i konfiguracja tylko), silnik OCR (interfejs gotowy, implementacja odroczona — patrz §6.1), React/TypeScript (UI bez etapu budowania), uwierzytelnianie, kolejka zadań, skalowanie poziome, rozliczalność kosztu tokenów, zgodność z oficjalnym ewaluatorem organizatora (nieosiągalna bez jego kodu).

### Anty-goale

Nie tworzymy interfejsu, który wygląda jak system KIO, ani dashboardu „dla urody”. Baza i UI mają służyć pomiarowi ekstrakcji i transparentności, a nie zastępować pliku `output/`, który organizator odbiera.

## 3. Stos i komponenty

| Warstwa | Wybór | Uzasadnienie | Licencja |
|---|---|---|---|
| Język | Python 3.13 | wymóg organizatora | — |
| API | FastAPI + Uvicorn | OpenAPI z automatu, lekka, dobrze współgra z `pydantic` | MIT / BSD-3 |
| Walidacja | pydantic v2 | jeden model dla kontraktu, API i serializacji | MIT |
| Generator modeli | datamodel-code-generator | modele pydantic powstają z `openapi.yaml`, nie z ręcznej kopii | MIT |
| Kontrola kontraktu | openapi-spec-validator | walidacja pliku OpenAPI przed użyciem | Apache-2.0 |
| Tekst z PDF | pypdfium2 (PDFium) | szybki, licencja BSD-3, brak zależności systemowych | Apache-2.0 / BSD-3 |
| OCR (opcjonalnie) | rapidocr + onnxruntime | modele w kole, CPU-only, brak GPU | Apache-2.0 / MIT |
| DB | PostgreSQL 16 + SQLAlchemy 2.0 Core + pg8000 | relational, w kontenerze, sterownik w czystym Pythonie, bez kompilacji w obrazie | PostgreSQL / MIT / BSD-3 |
| Szablony UI | Jinja2 | bez etapu budowania, bez Node u jury | BSD-3 |
| Frontend | HTML + CSS + waniliowy JS serwowane przez FastAPI | brak toolchainu, brak CDN, działa w środowisku COI | — |
| Testy | pytest | standard | MIT |
| Podobieństwo | rapidfuzz | pomiar własnego F1 | MIT |
| Klient LLM | `httpx`, interfejs w kodzie, wyłączony domyślnie | port gotowy, bez zobowiązań wobec dostawcy | BSD-3 |

Wszystkie komponenty open source; model, dostawca i licencja modelu pozostają kwestią otwartą ([U-Q05](../07-decyzje/pytania-otwarte.md)) do czasu decyzji dostawcy w UE/EOG. Wersje przypięte w `apps/backend/requirements.txt`; koła potwierdzone dla Pythona 3.13 (`onnxruntime` ma `cp313`, `rapidfuzz` ma `cp313`, `pypdfium2` ma koła `py3-none-*`).

## 4. Układ repozytorium

```text
apps/
  backend/            pakiet odwolania2json: silnik, CLI, API, warstwa DB, ewaluator
    requirements.txt  jedyne źródło wersji zależności (przypięte)
    requirements-ocr.txt  dodatkowy zestaw OCR (opcjonalny)
    pyproject.toml    metadane pakietu; zależności wczytywane dynamicznie z requirements.txt
  web/                szablony i statyki UI (bez etapu budowania)
packages/
  contracts/          pakiet odwolania2json_contracts: openapi.yaml + modele pydantic
infra/
  docker/
    Dockerfile
    postgres/init.sql
scripts/
  generate_contracts.py     generuje modele pydantic z openapi.yaml
  validate_api.py           walidacja specyfikacji i rozjazdu z aplikacją FastAPI
  precommit.py              kontrola przed commitem (dokumenty, API, testy)
  verify_docker.ps1         test w Dockerze (Windows)
  verify_docker.sh          test w Dockerze (Linux)
.githooks/pre-commit        hook gitowy wskazujący na skrypt precommit
.github/workflows/ci.yml    joby CI: docs, api, test, eval
docs/…                dokumentacja (bez zmian w katalogach organizatora)
input/  output/       foldery aplikacji (ignorowane przez Git)
requirements.txt      ścieżka dla jury: zależności + instalacja pakietów
start.bat  start.sh   uruchomienie przez Docker albo lokalnie
docker-compose.yml    api + postgres
```

`apps/web/` zostaje katalogiem planowym bez etapu budowania: dzisiaj FastAPI serwuje szablony Jinja2, w przyszłości to samo miejsce przyjmie `dist/` z Reacta bez zmiany backendu.

## 5. Kontrakt danych

Trzy klasy, klucze i typy wzięte dosłownie z `oczekiwane-json/`; referencje organizatora mają identyczny zestaw kluczy (sprawdzone na 180 plikach).

### 5.1 OpenAPI jako źródło prawdy

`packages/contracts/odwolania2json_contracts/openapi.yaml` to **jedyny ręcznie pisany kontrakt**: minimalny dokument OpenAPI 3.1 opisujący zarówno API (ścieżki, parametry, odpowiedzi), jak i schematy trzech klas dokumentów w `components.schemas`. Z niego:

1. generowane są modele pydantic (`scripts/generate_contracts.py` → `datamodel-code-generator`, wynik w repo, żeby jury nie musiało mieć generatora);
2. budowany jest backend FastAPI — trasy używają wygenerowanych modeli jako typów żądań i odpowiedzi;
3. sprawdzany jest brak rozjazdu: test porównuje `app.openapi()` z plikiem `openapi.yaml` (zbiór ścieżek i metod, `operationId`, schematy składowe oraz odwołania do schematów w treściach) i kończy się błędem przy różnicy.

Kontrakt jest celowo mały: brak rozbudowanych rozszerzeń, wyłącznie `application/json`, bez paginacji w API dokumentów. Każda zmiana kontraktu idzie najpierw do `openapi.yaml`, potem do kodu.

### 5.2 Klasy dokumentów

| Klasa | Korzeń | Pola |
|---|---|---|
| `odwolanie` | `OdwolanieKIO` | `data` (ISO lub `null`), `czynnosc_dzien` (ISO lub `null`), `czynnosc_powod_id` (int 1–12), `czynnosc_opis` (tekst ze słownika), `miejscowosc` (lub `null`) |
| `odwolanie` | `Odwolujacy[]` | `krs`, `nazwa`, `nip`, `regon`, `przez-pelnomocnika` (0/1), `pelnomocnik{imie_nazwisko,nazwa,mail}` |
| `odwolanie` | `Zamawiajacy[]` | `krs`, `nazwa`, `nip`, `regon`, `prowadzacy_postepowanie` (0/1/`null`) |
| `odwolanie` | `ZamowieniePubliczne` | `numer_bzp`, `numer_postepowania`, `numer_ted`, `tytul` |
| `pelnomocnictwo` | `mocodawca[]` | `data{imie_nazwisko,krs,nazwa,nip,typ}`, `podpisujacy[]{imie_nazwisko}` |
| `pelnomocnictwo` | `pelnomocnicy[]` | `imie_nazwisko`, `pesel` (tekst lub `null`) |
| `przelew` | `przelew_bankowy` | `data_operacji`, `kwota` (liczba), `na_rachunek`, `numer_transakcji`, `tytul`, `z_rachunku` |

W schemacie OpenAPI `czynnosc_opis` jest **enumem** z 12 opisami ze słownika `czynnosc_powod_id_dict.md` w wersji `main` (`7590db8`), `czynnosc_powod_id` to liczba całkowita z zakresu 1–12, a `typ` mocodawcy to enum `osoba_prawna` / `osoba_fizyczna`. Zgodność pary `czynnosc_powod_id` ↔ `czynnosc_opis` (opis 1:1 z numerem) nie da się wyrazić w OpenAPI, więc pilnuje jej walidator pydantic w kodzie. Wynik dokumentu obcego to wariant `{}` (obiekt bez właściwości) w schemacie odpowiedzi.

Reguły serializacji:

1. Kolejność kluczy stała, identyczna ze wzorcem organizatora; brak klucza zapisujemy jako `null`, nigdy jako brak klucza.
2. Serializacja modeli generowanych używa aliasów (`przez-pelnomocnika` ma myślnik, nazwa pola w Pythonie bez niego).
3. `pesel` jako tekst (referencje używają tekstu, wzorzec pokazuje liczbę) — rozbieżność udokumentowana, decyzja zapisana w ADR.
4. `kwota` jako liczba zmiennoprzecinkowa (`200.0`, `17.0`).
5. `czynnosc_opis` zawsze literalnie ze słownika `czynnosc_powod_id_dict.md` w wersji `main` (`7590db8`), razem z `czynnosc_powod_id`.
6. Dokument obcy → `{}` (pusty obiekt JSON) zapisany pod nazwą pliku wejściowego. Reprezentacja `{}` przyjmuje się za domyślną wobec braku odpowiedzi mentora ([U-Q03](../07-decyzje/pytania-otwarte.md)); warianty `{}` i pusty plik 0 B różnią się tylko zapisem, nie treścią merytoryczną.
7. Nazwa pliku wyniku = nazwa bazowa pliku wejściowego + `.json`; podfoldery odtwarzają strukturę `input/`.

## 6. Silnik ekstrakcji

Potok dla jednego PDF-a:

```text
PDF → tekst stron (pypdfium2) → [strona bez tekstu → OCR] → klasyfikacja
    → ekstrakcja regułowa klasy → normalizacja → model pydantic → JSON + dowody
```

**Klasyfikacja po treści, nigdy po nazwie pliku** (organizator tego wymaga; w szablonie jest `negatywny przyklad.pdf`, który odwołaniem nie jest). Reguły: frazy kluczowe per klasa (`odwołanie`: „Odwołujący”, „Prezes Krajowej Izby Odwoławczej”, „zarzut”; `pełnomocnictwo`: „pełnomocnictwo”, „mocodawca”, „udzielamy pełnomocnictwa” — z normalizacją rozstrzelonych nagłówków typu `P E Ł N O M O C N I C T W O`; `przelew`: „potwierdzenie wykonania przelewu”, „polecenie przelewu”, „numer transakcji”). Próg punktowy i fallback „obcy”.

### 6.1 OCR: interfejs gotowy, implementacja odroczona

Moduł `odwolania2json/pdf/ocr.py` definiuje protokół `OcrEngine` z jedną metodą `recognize(page_image) -> str`. Domyślnie działa `NullOcrEngine`, która dla strony bez warstwy tekstowej zwraca **jawny błąd techniczny** („strona bez warstwy tekstowej, OCR niedostępny”), nigdy zmyślone dane. Implementacja `RapidOcrEngine` ładuje `rapidocr` i `onnxruntime` leniwie — jeśli ich nie ma, silnik zgłasza brak OCR, a nie awariuje importu.

Zależności OCR leżą w `requirements-ocr.txt`, poza podstawowym `requirements.txt`. Obraz Dockera **instaluje zestaw OCR domyślnie**, żeby plik demonstracyjny organizatora (`szablon-aplikacja/input/case1/przyklad odwolanie.pdf`, 7 stron bez tekstu) dał wynik, a nie pusty JSON. Ścieżka jury przez `pip install -r requirements.txt` pozostaje lekka i raportuje czytelny brak OCR z instrukcją `pip install -r requirements-ocr.txt`.

### 6.2 Ekstrakcja regułowa

Wyszukiwanie etykiet (`KRS:`, `NIP:`, `REGON:`, `Numer BZP`, `TED`, `Tytuł`, `Kwota`, `Data operacji`, `PESEL`) z oknem kontekstu; typy pól obsłużone przez dedykowane normalizatory:

| Typ | Normalizator | Uwaga z danych |
|---|---|---|
| NIP, REGON, KRS | dokładna długość (10 / 9 lub 14 / 10 cyfr), tolerancja prefiksów `PL`; **suma kontrolna tylko porządkuje kandydatów, nie odrzuca** | organizator generował syntetyczne wartości konwencją „cyfra kontrolna = suma ważona mod 11" (75/129 NIP, 74/123 REGON), a wg reguły oficjalnej przechodzi tylko 33/129 i 30/123; konta: 2/120 mod-97 |
| PESEL | 11 cyfr; suma kontrolna jako sygnał rankingowy | jedyny PESEL w referencjach (`85071204278`) jest poprawny |
| Numery rachunków | usunięcie spacji i prefiksu `PL`, potem 26 cyfr | w PDF występują grupowane spacjami (`PL54 7164 9675 …`); 2/120 kont przechodzi mod-97 IBAN, więc nie odrzucamy |
| Daty | `DD.MM.RRRR`, `R-MM-DD`, daty słowne („27 czerwca 2026 roku”), `dnia`, `r.` | nagłówek bywa w siedmiu różnych miejscach strony 1 |
| Kwoty | `200,00 zł`, `1 000,50` → liczba | — |
| Numery TED | `YYYY/S###-NNNNNN` → `NNNNNN-YYYY` | 47/60 spraw używa innego formatu niż referencja |
| Numery postępowania | wzorce typu `ZP.039.2025`, `ZP/PN/48/2026`, `IR.271-35/2026`, `MCLM/ZP/07/2026` | 23 różne formaty w 60 sprawach |
| Nazwy osób | etykieta + wzorzec nazwiska i imienia | podpis elektroniczny i formy „w imieniu” |
| Powód odwołania | **detektor zaskarżonej czynności** (okno przed pierwszym zarzutem) → słownik 12 pozycji | nagłówek pierwszego zarzutu bywa pułapką (39/60) |
| Tytuł | usunięcie polskich cudzysłowów, sklejenie spacji | w PDF „Zakup i dostawa …”, w referencji bez cudzysłowów |

**Zaskarżona czynność.** Wzorzec organizatora wymaga ustalenia powodu i daty **wyłącznie na podstawie pierwszego zarzutu**. W danych okazuje się, że nagłówek pierwszego zarzutu często nie zawiera identyfikatora czynności (przykład: zarzut „nieopisania parametrów technicznych przedmiotu dostawy” przy poprawnej odpowiedzi `1 = Decyzja o odrzuceniu oferty`). Algorytm: odnaleźć pierwszy zarzut, cofnąć się do zdania opisującego zaskarżoną czynność, dopasować typ czynności do słownika i wyciągnąć datę tej czynności. `czynnosc_dzien` to data **czynności**, nie pierwsza data w dokumencie (dokumenty zawierają daty z cytowań ustaw). Gdy zaskarżonej czynności nie da się ustalić, pola `czynnosc_powod_id`, `czynnosc_opis` i `czynnosc_dzien` pozostają `null` / puste, a nie są zgadywane.

**Dowód źródłowy**: każde pole zapamiętuje numer strony i fragment tekstu, z którego pochodzi wartość. To podstawa transparentności punktowanej w finale i danych dla widoku „pole → dowód” w UI.

**Port LLM**: interfejs `Extractor` z implementacją regułową; klient HTTP zgodny z OpenAI (`base_url`, `model`, `klucz` z env) istnieje, ale domyślnie wyłączony i nie używany w tej gałęzi. Włączenie wymaga potwierdzenia dostawcy w UE/EOG i licencji modelu.

## 7. API

| Metoda | Ścieżka | Opis |
|---|---|---|
| `GET` | `/healthz` | stan usługi i bazy |
| `POST` | `/api/documents` | multipart z PDF; klasyfikacja i ekstrakcja; zapis do bazy, jeśli skonfigurowana |
| `GET` | `/api/documents` | lista dokumentów z filtrami |
| `GET` | `/api/documents/{id}` | dokument z wynikiem i dowodami |
| `GET` | `/api/documents/{id}/pdf` | oryginalny PDF |
| `GET` | `/api/documents/{id}/json` | sam JSON wyniku |
| `GET` | `/api/classes` | rejestr klas ze schematem JSON |
| `GET` | `/docs` | OpenAPI (w obrazie wyłączone na potrzeby jury) |

Błędy: niepoprawny PDF i brak warstwy tekstowej to błąd techniczny z kodem HTTP, nigdy zmyślone dane; obcy dokument to poprawny wynik `{}` z klasą `nieznany`.

## 8. Postgres

Baza jest **opcjonalna**. Kod nie wymaga jej; bez `DATABASE_URL` API działa, zapis jest pomijany, a UI pokazuje banner „baza wyłączona”. Uzasadnienie: jury może uruchomić rozwiązanie z `pip install -r requirements.txt` bez Dockera i bez bazy, a Docker Compose uruchamia komplet.

Schemat (SQL w numerowanych plikach migracji, nakładany idempotentnie przy starcie):

```sql
documents(id uuid pk, filename text, sha256 text unique, size_bytes bigint,
          source_path text, page_count int, has_text_layer bool, created_at timestamptz)
runs(id uuid pk, started_at timestamptz, finished_at timestamptz, status text,
     duration_ms int, documents_count int)
extractions(id uuid pk, document_id uuid fk, run_id uuid fk, class text,
            schema_version text, payload jsonb, evidence jsonb, created_at timestamptz)
```

Migracje to pliki `apps/backend/odwolania2json/db/migrations/NNNN_nazwa.sql` nakładane po kolei przez `odwolania2json.db.migrate.migrate()`; zastosowane wersje zapisywane są w tabeli `schema_migrations`, więc migracja nigdy nie wykonuje się dwa razy. Polecenie `python -m odwolania2json migrate` stosuje migracje ręcznie, a kontener `api` stosuje je przy starcie — baza po `docker compose up` jest gotowa do użycia bez ręcznych kroków. Plik `infra/docker/postgres/init.sql` zawiera tylko bootstrap bazy; schemat aplikacji tworzą migracje.

`payload` to pełny JSON wyniku (ta sama postać co plik w `output/`), `evidence` to mapa „ścieżka pola → {strona, fragment}". Deduplikacja po `sha256` dokumentu: ponowne przetworzenie nie tworzy duplikatu, a bieg jest zapisywany w `runs`.

## 9. UI

Serwowane przez FastAPI, bez etapu budowania, bez CDN, bez Node — uruchamialne u jury samym Dockerem. **UI jest przeglądarką bazy danych**, nie podglądem dokumentu (decyzja: w tej gałęzi widok PDF obok JSON zostawiamy na późniejszy przyrost — zapisane w ADR-002).

1. **Pulpit**: kafelki z liczbami dokumentów, ekstrakcji i przebiegów, rozkład ekstrakcji według klas, tabela zastosowanych migracji.
2. **Dokumenty**: tabela `documents` z filtrem po nazwie pliku, liczbą stron, rozmiarem, klasą i linkiem do wyniku.
3. **Ekstrakcje**: lista `extractions` oraz widok szczegółów — `payload` (jsonb) obok `evidence` (jsonb) i tabeli „pole → dowód (strona, fragment)".
4. **Przebiegi**: tabela `runs` (start, koniec, status, czas, liczba dokumentów).
5. **Schemat**: kolumny, typy i nullability każdej tabeli z `information_schema`.
6. **Konsola SQL**: dowolne `SELECT` z widokiem wyniku; zapytania zmieniające dane są odrzucane, sterownik dostaje tylko odczyt.

Brak uwierzytelniania (prototyp lokalny), brak edycji danych, brak mechanizmu sesji. Bez `DATABASE_URL` strony renderują się z bannerem „baza wyłączona" zamiast awarii.

## 10. Docker

`infra/docker/Dockerfile`: `python:3.13.18-slim` z przypiętą wersją (digest `sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90`, sprawdzony 2026-11-21), użytkownik bez roota, `pip install --no-cache-dir` z plików przypiętych w `apps/backend/requirements.txt` oraz `requirements-ocr.txt`, katalog `input/` i `output/` jako wolumeny, healthcheck na `/healthz`, brak modelu LLM w obrazie.

`docker-compose.yml`: usługi `api` (FastAPI na porcie 8000) i `db` (`postgres:16-alpine`, hasło z `.env`), wolumen `input`, `output`, `pgdata`. Klucze API i hasło bazy wyłącznie w `.env` (ignorowanym przez Git); `.env.example` dostaje `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.

Start: `docker compose up --build` (komplet) albo `start.bat` / `start.sh`; lokalnie `pip install -r requirements.txt` i `python -m odwolania2json run`.

## 11. Weryfikacja

| Poziom | Zakres |
|---|---|
| Jednostkowy | normalizatory (sumy NIP/REGON/PESEL, daty, kwoty, numery TED i rachunków, pozycje postępowania), klasyfikacja, detektor zaskarżonej czynności, serializacja kolejności kluczy i `null`, wynik `{}` dla obcego dokumentu |
| Kontraktowy | `openapi.yaml` przechodzi `openapi-spec-validator`; `app.openapi()` zgadza się ze specyfikacją (ścieżki, `operationId`, schematy); modele referencji organizatora mają identyczny zestaw kluczy i typów (180 plików) |
| Wdrożeniowy | `POST /api/documents` na PDF ze sprawy, odczyt JSON i dowodu, batch `input` → `output` z zachowaniem drzewa, plik demonstracyjny organizatora (skan) obsłużony przez OCR w obrazie Docker |
| Jakość | własny F1 przybliżony na 60 sprawach: TP/TN/FP/FN per pole, listy dopasowywane po treści (nie pozycji), raport przy dwóch progach podobieństwa (0,55 z `ground_truth.yaml` organizatora i 0,80 z komunikatu Discord) |
| Dostarczenie | budowa obrazu, `docker compose up`, healthcheck, czysty start na zależnościach z `requirements.txt` |

Metoda pomiaru jest opisana jawnie wraz z ograniczeniami, a wynik nie jest nazywany wynikiem oficjalnego ewaluatora. Słownik przyczyn w pomiarze to wersja `main` (`7590db8`) — inaczej pięć spraw z id 6 pokazałoby fałszywe FP.

Materiały organizatora są czytane wyłącznie do odwołań; nic w `docs/02-materialy/` nie jest modyfikowane.

### 11.1 Test w Dockerze (wymagany artefakt)

Powtarzalny skrypt sprawdzający, czy całość działa w kontenerze: `scripts/verify_docker.ps1` (Windows, środowisko autora) i `scripts/verify_docker.sh` (Linux, środowisko jury). Oba wykonują ten sam zestaw kroków i zwracają kod wyjścia 0 dopiero po pełnym sukcesie:

1. `docker compose build` — obraz buduje się bez błędów, na `python:3.13-slim`.
2. `docker compose up -d` — kontenery `api` i `db` wstają, `db` przechodzi healthcheck.
3. `GET /healthz` zwraca 200 i `db: up` (osobny wariant sprawdza, że bez bazy API nadal działa i raportuje `db: down`).
4. `docker compose exec api pytest` — testy jednostkowe, kontraktowe i wdrożeniowe przechodzą w kontenerze na Pythonie 3.13.
5. Wgranie PDF ze sprawy (`POST /api/documents`, katalog materiałów montowany tylko do odczytu) — odpowiedź ma poprawną klasę, komplet pól i dowody źródłowe.
6. Porównanie odpowiedzi z referencyjnym JSON-em organizatora: identyczny zestaw kluczy, zgodne typy, wartości zgodne w 80% dla pól długich.
7. Wgranie pliku demonstracyjnego organizatora (skan) — wynik nie jest pusty, potwierdza działanie OCR w obrazie.
8. UI: strony `/` i widok dokumentu zwracają 200, a w HTML występuje oznaczenie kontenera danych; sprawdzany jest też 404 dla nieistniejącego dokumentu.
9. Baza: zapytanie do `db` potwierdza wiersze w `documents` i `extractions` odpowiadające wgranemu plikowi.
10. Batch CLI: `input/` z dwoma podkatalogami i plikami PDF daje `output/` o tej samej strukturze i nazwach plików (w tym pusty JSON dla dokumentu obcego).
11. `docker compose down -v` nie zostawia stanu; powtórzenie skryptu przechodzi bez ręcznych poprawek.

Skrypt wypisuje raport krok po kroku (OK/FAIL) i zapisuje go do `docs/05-weryfikacja/`.

### 11.2 Walidacja API, CI i hook pre-commit

Jedno narzędzie sprawdza kontrakt w trzech miejscach, więc rozjazd specyfikacji i kodu wychodzi na jawę:

| Narzędzie | Zadanie |
|---|---|
| `scripts/generate_contracts.py` | generuje modele pydantic z `packages/contracts/odwolania2json_contracts/openapi.yaml` do pliku `models.py` |
| `scripts/validate_api.py --stage spec` | waliduje `openapi.yaml` (openapi-spec-validator) i porównuje wygenerowane modele z plikiem w repo — rozjazd oznacza, że ktoś zmienił spec without regenerowania |
| `scripts/validate_api.py --stage app` | porównuje `app.openapi()` aplikacji FastAPI ze specyfikacją: ścieżki i metody, `operationId`, schematy składowe, odwołania do schematów w treściach |
| `scripts/precommit.py` | uruchamia kontrolę dokumentacji, walidację API i testy; `--fast` pomija testy i etap `app` |
| `.githooks/pre-commit` | hook gitowy włączany poleceniem `git config core.hooksPath .githooks`; blokuje commit, gdy kontrakt się rozjechał |
| `.github/workflows/ci.yml` | joby na Pythonie 3.13: `docs` (kontrola dokumentacji), `api` (walidacja API, etap `all`), `test` (pełny zestaw testów), `eval` (pomiar F1 na 60 sprawach) |

Pełna weryfikacja w kontenerze pozostaje skryptem z §11.1; CI używa tego samego kodu walidacji, więc rozjazd kontraktu blokuje i lokalnie, i na serwerze.

## 12. Ryzyka

| Ryzyko | Skutek | Reakcja |
|---|---|---|
| Reguły nadążają za szablonami 60 spraw, ale ukryty zbiór ma nowe układy | niższy F1 | pomiar F1 na 60 sprawach pokazuje lukę; port LLM gotowy na następny krok; ryzyko opisane w dokumentacji |
| Ukryty zbiór zawiera skany | brak wyniku dla skanów | interfejs OCR gotowy, zestaw OCR w obrazie Docker, jawne braki w ścieżce pip |
| Baza dodatkowa zależność w drodze do jury | ryzyko niesprawnego startu | baza opcjonalna; ścieżka jury bez Dockera i bez bazy działa samodzielnie |
| `pypdfium2`, `rapidocr`, `onnxruntime` na Pythonie 3.13 | brak kół | koła potwierdzone dla 3.13 przed komitem; OCR w zestawie dodatkowym |
| UI bez etapu budowania ogranicza późniejszy React | konflikt z planem `apps/web/` | to samo miejsce katalogu, brak zmian w API; decyzja w ADR |
| Rozbieżność `pesel`, `czynnosc_opis` (diakrytyki), `numer_ted` w referencjach | cichy błąd F1 | reguły normalizacji i jawnie opisana metoda pomiaru; pytanie do mentora |

## 13. Decyzje do zapisania

`ADR-002` w `docs/07-decyzje/`: FastAPI jako API, Postgres jako baza opcjonalna, UI bez etapu budowania w `apps/web/`, OpenAPI jako źródło prawdy dla kontraktu, odejście od propozycji React/TypeScript z [pełnej aplikacji](pelna-aplikacja.md) — z konsekwencjami i warunkami powrotu do Reacta. Aktualizacja [README architektury](README.md) o statusie wdrożenia oraz [planu weryfikacji](../05-weryfikacja/README.md) o stan pomiarów.

## 14. Co zostaje do decyzji

1. Reprezentacja pustego wyniku: przyjęto `{}` — do potwierdzenia z mentorem ([U-Q03](../07-decyzje/pytania-otwarte.md)).
2. Dostawca i model LLM w UE/EOG — poza zakresem tej gałęzi.
3. Czy w finale wracamy do Reacta (`apps/web/dist`) — decyzja po zmierzeniu F1.
4. Czy ukryty zbiór zawiera skany i nowe układy dokumentów — odpowiedź organizatora; ryzyko opisane w §12.
