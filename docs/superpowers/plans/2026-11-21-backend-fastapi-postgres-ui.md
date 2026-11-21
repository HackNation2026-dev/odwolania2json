---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: plan implementacji
---

# Backend FastAPI + Postgres + UI — plan implementacji

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Działający prototyp Odwołania2JSON: PDF → JSON zgodny z kontraktem organizatora, dostępny przez CLI i FastAPI, uruchamiany przez Docker, z opcjonalnym Postgresem i przeglądarkowym UI.

**Architecture:** Kontraktem jest minimalny plik OpenAPI 3.1 (`packages/contracts/openapi.yaml`), z którego generowane są modele pydantic; backend FastAPI i serializacja korzystają z tych samych modeli. Silnik to potok: tekst z PDF (pypdfium2) → klasyfikacja regułowa → ekstrakcja regułowa z normalizatorami → model pydantic → JSON + dowód źródłowy. CLI i API używają tego samego silnika; Postgres jest opcjonalny (bez `DATABASE_URL` kod działa w trybie plikowym), a UI serwuje FastAPI bez etapu budowania.

**Tech Stack:** Python 3.13, FastAPI, Uvicorn, pydantic v2, datamodel-code-generator, openapi-spec-validator, pypdfium2, SQLAlchemy 2.0 Core + pg8000, PostgreSQL 16, Jinja2, pytest, rapidfuzz, Docker (`python:3.13-slim`).

**Spec:** `docs/04-architektura/projekt-backend-fastapi-postgres-ui.md` — plan realizuje tę specyfikację; implementer czyta oba dokumenty.

## Global Constraints

- Python 3.13+ (organizator). Kod kompatybilny też z 3.11, żeby dało się iterować lokalnie; autorytatywna kontrola to kontener.
- `docs/02-materialy/` jest materiałem organizatora: **zakaz modyfikacji**; dane czytamy wyłącznie do odwołań i testów.
- Materiały organizatora muszą pozostać bajtowo zgodne z `docs/02-materialy/manifest.json`; przed każdym commitem `python scripts/verify_docs.py` musi zwrócić `OK`.
- Zależności przypięte w `apps/backend/requirements.txt`; OCR w `apps/backend/requirements-ocr.txt` (poza podstawą).
- Klucze API i hasło bazy wyłącznie w `.env` (ignorowanym przez Git); `.env.example` bez wartości.
- Ścisły JSON: stała kolejność kluczy jak w `oczekiwane-json/`, brak wartości jako `null`, nigdy jako brak klucza.
- Dokument obcy → `{}` zapisany pod nazwą bazową pliku wejściowego (korekta Discord 13:27).
- Nazwa pliku wyniku = nazwa bazowa PDF + `.json`; podfoldery `input/` odtwarzane w `output/`.
- Klasyfikacja po treści dokumentu, nigdy po nazwie pliku.
- Brak danych → `null`, nigdy wartość zmyślona; brak warstwy tekstowej → błąd techniczny, nie `{}`.
- Dokumentacja, komunikaty CLI i nazwy testów po polsku; **identyfikatory w kodzie po angielsku** (wyjątek: `APPEAL_REASONS` jako stała słownika powodów).
- Zmiana stosu wymaga ADR w `docs/07-decyzje/` z konsekwencjami.

## Review Focus

1. **PDF o nazwie z innej klasy** (np. `negatywny przyklad.pdf` z szablonu organizatora) — klasyfikacja musi dać `nieznany` i wynik `{}`, a nie zawartość po nazwie pliku.
2. **Dokument obcy w batchu** — musi powstać plik JSON `{}` pod swoją nazwą; pominięcie pliku to błąd, nie niedopuszczalne „brak danych".
3. **PDF bez warstwy tekstowej** (skan) — jawny błąd techniczny lub wynik z OCR; nigdy pusty JSON udający brak informacji i nigdy zmyślone pola.
4. **Brak bazy danych** (`DATABASE_URL` nieustawione) — API, CLI i UI działają, UI pokazuje banner, nic nie wybucha.
5. **Pole opcjonalne nieobecne w dokumencie** (np. `pesel`, `numer_ted`) — klucz obecny z wartością `null`, nigdy pominięty.

---

### Task 1: Szkielet repozytorium i pakiety

**Files:**
- Create: `requirements.txt` (root), `pytest.ini`, `.dockerignore`
- Create: `packages/contracts/pyproject.toml`, `packages/contracts/odwolania2json_contracts/__init__.py`
- Create: `apps/backend/pyproject.toml`, `apps/backend/requirements.txt`, `apps/backend/requirements-ocr.txt`
- Create: `apps/backend/odwolania2json/__init__.py`, `apps/backend/odwolania2json/__main__.py`
- Modify: `.env.example`

**Interfaces:**
- Produces: pakiet `odwolania2json` (importowalny) i pakiet `odwolania2json_contracts` (importowalny), `pytest.ini` z `testpaths = tests`, polecenie `python -m odwolania2json --help`.

- [ ] **Step 1: Utwórz test szkieletu**

```python
# tests/test_scaffolding.py
def test_cli_help_runs(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "Odwołania2JSON" in capsys.readouterr().out
```
Test ma sprawdzać, że `python -m odwolania2json --help` kończy się kodem 0 i wypisuje „Odwołania2JSON”.

- [ ] **Step 2: Uruchom test, ma paść**

Run: `python -m pytest tests/test_scaffolding.py -v`
Expected: FAIL — brak modułu `odwolania2json`.

- [ ] **Step 3: Utwórz pakiety i pliki**

`apps/backend/requirements.txt` (przypięte wersje sprawdzone na PyPI, Python 3.13):
```
fastapi==0.165.0
uvicorn[standard]==0.54.0
pydantic==2.14.4
python-multipart==0.0.34
jinja2==3.1.6
pypdfium2==5.15.2
SQLAlchemy==2.1.9
pg8000==1.31.6
httpx==0.28.1
rapidfuzz==3.14.6
PyYAML==6.0.4
pytest==9.2.0
datamodel-code-generator==0.99.0
openapi-spec-validator==0.9.0
```
`pytest`, `datamodel-code-generator` i `openapi-spec-validator` są w pliku podstawowym, bo test kontraktowy musi móc odtworzyć modele z `openapi.yaml` w dowolnym środowisku, a dokumentacja wymaga polecenia `python -m pytest` po instalacji z `requirements.txt`.
`apps/backend/requirements-ocr.txt`:
```
-r requirements.txt
rapidocr==3.10.0
onnxruntime==1.32.0
```
`apps/backend/pyproject.toml`: nazwa `odwolania2json`, `requires-python = ">=3.11"` (próg metadanych zgodny z lokalną iteracją na 3.11; wymagany runtime to 3.13 w Dockerze i CI), `dynamic = ["version", "dependencies"]`, `version = {attr = "odwolania2json.__version__"}`, `[tool.setuptools.dynamic] dependencies = {file = ["requirements.txt"]}`.
`packages/contracts/pyproject.toml`: nazwa `odwolania2json-contracts`, `requires-python = ">=3.11"`, `dynamic = ["version"]`, `version = {attr = "odwolania2json_contracts.__version__"}`, jedyna zależność `pydantic==2.14.4`, `[tool.setuptools.package-data] odwolania2json_contracts = ["*.yaml"]` (plik `openapi.yaml` musi trafić do koła).
`requirements.txt` (root):
```
-r apps/backend/requirements.txt
-e ./packages/contracts
-e ./apps/backend
```
`pytest.ini`:
```
[pytest]
testpaths = tests
addopts = -q
markers =
    eval: testy pomiarowe na 60 sprawach organizatora (wolne)
```
`.env.example` dodaje `DATABASE_URL=`, `POSTGRES_USER=`, `POSTGRES_PASSWORD=`, `POSTGRES_DB=`, `OCR_ENABLED=0`.

- [ ] **Step 4: Zainstaluj i uruchom test**

Run: `pip install -e ./packages/contracts -e ./apps/backend && python -m pytest tests/test_scaffolding.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pytest.ini .dockerignore .env.example packages/contracts apps/backend
git commit -m "feat: szkielet pakietów odwolania2json i odwolania2json_contracts"
```

---

### Task 2: Kontrakt OpenAPI i generowane modele pydantic

**Files:**
- Create: `packages/contracts/openapi.yaml`
- Create: `scripts/generate_contracts.py`, `scripts/validate_api.py`
- Create: `packages/contracts/odwolania2json_contracts/models.py` (generowany, w repo)
- Create: `packages/contracts/odwolania2json_contracts/powody.py`
- Modify: `packages/contracts/odwolania2json_contracts/__init__.py`
- Test: `tests/contract/test_openapi.py`, `tests/contract/test_powody.py`

**Interfaces:**
- Produces: `openapi.yaml` (OpenAPI 3.1), `odwolania2json_contracts.models` z klasami `Odwolanie`, `OdwolanieKIO`, `Odwolujacy`, `PelnomocnikOdwolania`, `Zamawiajacy`, `ZamowieniePubliczne`, `Pelnomocnictwo`, `Mocodawca`, `MocodawcaDane`, `Podpisujacy`, `PelnomocnikPelnomocnictwa`, `Przelew`, `PrzelewBankowy`, `PustyWynik`; `odwolania2json_contracts.APPEAL_REASONS: dict[int, str]` (12 pozycji); `odwolania2json_contracts.Wynik` (alias unii typów).
- Konsumuje: nic z wcześniejszych zadań poza strukturą pakietu.

- [ ] **Step 1: Napisz testy kontraktowe**

`tests/contract/test_openapi.py`:
```python
def test_spec_is_valid_openapi():
    # openapi-spec-validator waliduje packages/contracts/openapi.yaml
def test_spec_declares_three_document_schemas():
    # components.schemas zawiera Odwolanie, Pelnomocnictwo, Przelew
def test_generated_models_match_committed_file():
    # ponowne wygenerowanie modeli daje identyczną treść pliku models.py
def test_models_keep_organizer_key_order():
    # lista kluczy model_dump() == kolejność kluczy z oczekiwane-json/odwolanie.json
def test_empty_result_serializes_as_empty_object():
    # PustyWynik().model_dump() == {}
```
`tests/contract/test_powody.py`:
```python
def test_powody_match_organizer_dictionary():
    # 12 pozycji identycznych z main-7590db8/oczekiwane-json/czynnosc_powod_id_dict.md
def test_powod_ids_are_1_to_12():
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/contract -v`
Expected: FAIL — brak `openapi.yaml` i `models.py`.

- [ ] **Step 3: Napisz `openapi.yaml`**

Minimalny OpenAPI 3.1: `info`, `paths` (tymcczasowo tylko `/healthz` → do rozbudowy w Task 11), `components.schemas` z trzema klasami i `PustyWynik`. Klucze w kolejności organizatora; `przez-pelnomocnika` jako `0|1`; `czynnosc_opis` jako `enum` z 12 opisami (diakrytyki jak w `main-7590db8`); `typ` jako enum `osoba_prawna|osoba_fizyczna`; `pesel` jako `string|null`; `kwota` jako `number`; daty jako `string` z formatem `date` lub `null`.

- [ ] **Step 4: Napisz `scripts/generate_contracts.py`**

Uruchamia `datamodel-code-generator` z `--input packages/contracts/openapi.yaml --input-file-type openapi --output packages/contracts/odwolania2json_contracts/models.py --class-name suffix pusty --use-standard-collections --target-python-version 3.13`, waliduje wynik `openapi-spec-validator` i kończy się kodem 0 albo 1.

- [ ] **Step 5: Wygeneruj modele i napisz `powody.py`**

`APPEAL_REASONS` zawiera dokładnie:
```
1=Decyzja o odrzuceniu oferty
2=Ogłoszenie wyboru oferty
3=Decyzja o wykluczeniu wykonawcy
4=Publikacja specyfikacji warunków zamówienia (SWZ)
5=Modyfikacja treści SWZ
6=Odpowiedzi/wyjaśnienia do SWZ
7=Zaniechanie odrzucenia oferty
8=Zaniechanie wykluczenia wykonawcy
9=Decyzja o unieważnieniu postępowania
10=Zaniechanie unieważnienia postępowania
11=Opis przedmiotu zamówienia (OPZ)
12=Projektowane postanowienia umowy
```
`__init__.py` eksponuje `models`, `APPEAL_REASONS`, `Wynik = Union[Odwolanie, Pelnomocnictwo, Przelew, PustyWynik]`.

- [ ] **Step 6: Napisz `scripts/validate_api.py`**

Jeden skrypt walidujący kontrakt, używany później przez CI i hook pre-commit. CLI: `python scripts/validate_api.py [--stage spec|app|all]`, kod wyjścia 0 przy sukcesie, 1 przy niezgodności.

- `--stage spec` (domyślnie): waliduje `openapi.yaml` przez `openapi-spec-validator`; regeneruje modele do katalogu tymczasowego przez `scripts/generate_contracts.py` i porównuje z plikiem `packages/contracts/odwolania2json_contracts/models.py` — rozjazd kończy się błędem „modele nie zgadzają się ze specyfikacją, uruchom scripts/generate_contracts.py".
- `--stage app`: importuje aplikację FastAPI (`odwolania2json.api.app`) i porównuje jej `app.openapi()` ze specyfikacją (ścieżki i metody, `operationId`, schematy składowe, odwołania do schematów w treściach). Jeśli aplikacja jeszcze nie istnieje, skrypt wypisuje „pominięto: aplikacja niedostępna" i kończy się kodem 0 (etap `app` włącza się w Task 11).
- Każdy krok wypisuje `OK <opis>` albo `FAIL <opis> <powód>`.

- [ ] **Step 7: Uruchom testy, mają przejść**

Run: `python -m pytest tests/contract -v` oraz `python scripts/validate_api.py --stage spec`
Expected: PASS; skrypt kończy się kodem 0 i wypisuje `OK` dla walidacji specyfikacji i zgodności modeli.

- [ ] **Step 8: Commit**

```bash
git add packages/contracts scripts/generate_contracts.py scripts/validate_api.py tests/contract
git commit -m "feat: kontrakt OpenAPI, generowane modele pydantic i walidacja API"
```

---

### Task 3: Normalizatory pól

**Files:**
- Create: `apps/backend/odwolania2json/domain/normalize.py`
- Test: `tests/unit/test_normalize.py`

**Interfaces:**
- Produces (wszystkie w `odwolania2json.domain.normalize`):
  - `fold(text: str) -> str` — usuwa diakrytyki, lowercase, scala spacje
  - `collapse_spaces(text: str) -> str`
  - `strip_quotes(text: str) -> str` — usuwa „ ” " ' '
  - `normalize_nip(text: str) -> str | None` — 10 cyfr, suma kontrolna
  - `normalize_regon(text: str) -> str | None` — 9 cyfr, suma kontrolna
  - `normalize_krs(text: str) -> str | None` — 10 cyfr, bez sumy kontrolnej
  - `normalize_pesel(text: str) -> str | None` — 11 cyfr, suma kontrolna
  - `normalize_account(text: str) -> str | None` — 26 cyfr po usunięciu spacji i prefiksu `PL`
  - `normalize_date(text: str) -> str | None` — ISO `YYYY-MM-DD`
  - `normalize_amount(text: str) -> float | None`
  - `normalize_ted(text: str) -> str | None` — `NNNNNN-YYYY`
  - `find_postepowanie_number(text: str) -> str | None`
  - `find_value(text: str, labels: Sequence[str], window: int = 120) -> str | None` — pierwsza etykieta, potem wartość w oknie znaków
  - `odwolania2json.domain.base.Ekstrakcja` — dataclass `model: pydantic.BaseModel`, `evidence: dict[str, tuple[int, int]]` (ścieżka pola → numer strony i pozycja znaku); wspólny typ zwracany przez ekstraktory klas

- [ ] **Step 1: Napisz testy jednostkowe**

```python
def test_normalize_ted_from_pdf_format():
    assert normalize_ted("2026/S086-999073") == "999073-2026"
def test_normalize_account_removes_spaces():
    assert normalize_account("PL54 7164 9675 2472 1141 8071 4012") == "54716496752472114180714012"
def test_normalize_date_polish_words():
    assert normalize_date("27 czerwca 2026 roku") == "2026-06-27"
def test_normalize_date_dotted():
    assert normalize_date("02.07.2026") == "2026-07-02"
def test_normalize_pesel_rejects_invalid_checksum():
    assert normalize_pesel("85071204279") is None
def test_normalize_nip_accepts_synthetic_prefix():
    assert normalize_nip("9999284065") == "9999284065"
def test_normalize_amount_handles_spaces_and_cents():
    assert normalize_amount("1 000,50 zł") == 1000.5
def test_find_value_uses_label_window():
    assert find_value("KRS: 9999405188\nNIP: 9999284065", ["KRS"]) == "9999405188"
```
Dodatkowo: `normalize_regon` odrzuca błędne sumy, `fold("P E Ł N O M O C N I C T W O")` daje `"p e l n o m o c n i c t w o"`, a `fold` po usunięciu spacji między literami wskazuje to zadanie w Task 5.

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_normalize.py -v`
Expected: FAIL — brak modułu `normalize`.

- [ ] **Step 3: Zaimplementuj normalizatory**

Sygnatury kontrolne: NIP — suma wag `[6,5,7,2,3,4,5,6,7]` modulo 11, reszta 10 znaczy błędne; REGON 9-cyfr — wagi `[8,9,2,3,4,5,6,7]` modulo 11, reszta 10 znaczy błędne; PESEL — wagi `[1,3,7,9,1,3,7,9,1,3]` modulo 10. Daty słowne: słownik miesięcy po polsku (styczeń…grudzień, także formy dopełniacza: „czerwca”, „marca”, „kwietnia”, „maja”, „czerwca”, „lipca”, „sierpnia”, „września”, „października”, „listopada”, „grudnia”). TED: dopasuj `YYYY/S###-NNNNNN` albo `NNNNNN-YYYY` i zwróć `NNNNNN-YYYY`. Kwota: usuń spacje i „zł”, zamień przecinek na kropkę, zwróć `float`.

- [ ] **Step 4: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_normalize.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/odwolania2json/domain tests/unit/test_normalize.py
git commit -m "feat: normalizatory NIP, REGON, KRS, PESEL, dat, kwot, TED i rachunkow"
```

---

### Task 4: Odczyt PDF i interfejs OCR

**Files:**
- Create: `apps/backend/odwolania2json/pdf/__init__.py`, `apps/backend/odwolania2json/pdf/text.py`, `apps/backend/odwolania2json/pdf/ocr.py`
- Create: `apps/backend/odwolania2json/errors.py`
- Test: `tests/unit/test_pdf.py`

**Interfaces:**
- Produces:
  - `odwolania2json.errors.PdfError(RuntimeError)`, `odwolania2json.errors.OcrUnavailableError(RuntimeError)`
  - `odwolania2json.pdf.text.PageText` — dataclass `number: int`, `text: str`
  - `odwolania2json.pdf.text.extract_pages(data: bytes) -> list[PageText]` — rzuca `PdfError` dla pliku niebędącego PDF
  - `odwolania2json.pdf.text.render_page_png(data: bytes, page_number: int) -> bytes`
  - `odwolania2json.pdf.ocr.OcrEngine` — Protocol `recognize(self, image_png: bytes) -> str`
  - `odwolania2json.pdf.ocr.NullOcrEngine` — `recognize` rzuca `OcrUnavailableError`
  - `odwolania2json.pdf.ocr.RapidOcrEngine` — leniwy import `rapidocr`
  - `odwolania2json.pdf.ocr.build_ocr_engine(enabled: bool) -> OcrEngine`

- [ ] **Step 1: Napisz testy**

```python
def test_extract_pages_reads_text_layer():
    # przyklad_01/odwolanie.pdf -> 2 strony, tresc zawiera "Odwołujący"
def test_extract_pages_rejects_non_pdf():
    # b"to nie pdf" -> PdfError
def test_null_ocr_engine_reports_unavailable():
    # NullOcrEngine().recognize(b"") -> OcrUnavailableError
def test_build_ocr_engine_falls_back_to_null_when_disabled():
    # build_ocr_engine(False) -> NullOcrEngine
def test_scan_without_text_layer_is_detected():
    # dokument bez warstwy tekstowej -> lista stron zawiera pusty tekst dla skanu
```
Ścieżki materiałów w testach: `docs/02-materialy/organizator-uzp/dane/przyklad_01/odwolanie.pdf` oraz `docs/02-materialy/organizator-uzp/szablon-aplikacja/input/case1/przyklad odwolanie.pdf` (skan).

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_pdf.py -v`
Expected: FAIL — brak modułu `pdf`.

- [ ] **Step 3: Zaimplementuj**

`extract_pages` używa `pypdfium2.PdfDocument` nad bajtami (`PdfDocument` z `bytes` wejściowym, brak zapisu na dysk), zwraca listę `PageText` z numeracją od 1 i tekstem strony; pusta strona daje `text=""`. `render_page_png` renderuje stronę do bitmapy i koduje PNG. `RapidOcrEngine.recognize` dekoduje PNG przez Pillow, wywołuje `rapidocr.RapidOCR()` i zwraca połączony tekst; brak `rapidocr` → `OcrUnavailableError`.

- [ ] **Step 4: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_pdf.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/odwolania2json/pdf apps/backend/odwolania2json/errors.py tests/unit/test_pdf.py
git commit -m "feat: odczyt tekstu z PDF i interfejs OCR"
```

---

### Task 5: Klasyfikacja dokumentów po treści

**Files:**
- Create: `apps/backend/odwolania2json/domain/classify.py`
- Test: `tests/unit/test_classify.py`, `tests/eval/test_classify_materialy.py`

**Interfaces:**
- Produces:
  - `odwolania2json.domain.classify.KLASY: tuple[str, ...]` — `("odwolanie", "pelnomocnictwo", "przelew")`
  - `odwolania2json.domain.classify.KLASA_NIEZNANA = "nieznany"`
  - `odwolania2json.domain.classify.classify(text: str) -> str`
- Konsumuje: `fold` z Task 3.

- [ ] **Step 1: Napisz testy**

```python
def test_classify_odwolanie():
    assert classify("Prezes Krajowej Izby Odwoławczej ... Odwołujący: ...") == "odwolanie"
def test_classify_pelnomocnictwo_with_spaced_header():
    assert classify("P E Ł N O M O C N I C T W O ...") == "pelnomocnictwo"
def test_classify_przelew():
    assert classify("POTWIERDZENIE WYKONANIA PRZELEWU ...") == "przelew"
def test_classify_unknown_document():
    assert classify("Broszura JPK ... VAT ...") == "nieznany"
```
`tests/eval/test_classify_materialy.py`: parametryzowany po plikach `docs/02-materialy/organizator-uzp/dane/przyklad_*/odwolanie.pdf` → `odwolanie`, `pelnomocnictwo.pdf` → `pelnomocnictwo`, `potwierdzenie_przelewu.pdf` → `przelew`, `docs/02-materialy/organizator-uzp/dane/negatywne/*.pdf` → `nieznany`.

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_classify.py tests/eval/test_classify_materialy.py -v`
Expected: FAIL — brak modułu `classify`.

- [ ] **Step 3: Zaimplementuj reguły**

Punktacja fraz: `odwolanie` — „odwołujący”, „krajowej izby odwoławczej”, „zarzut”, „wnoszę o”; `pelnomocnictwo` — „pełnomocnictw”, „mocodawc”, „udzielamy pełnomocnictwa”, „pełnomocnik”; `przelew` — „potwierdzenie wykonania przelewu”, „polecenie przelewu”, „numer transakcji”, „zleceniodawc”, „odbiorca przelewu”. Prógu `nieznany` nie przekracza klasa z najwyższą punktacją, gdy różnica do drugiego miejsca jest mniejsza niż 2 punkty.

- [ ] **Step 4: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_classify.py tests/eval/test_classify_materialy.py -v`
Expected: PASS — wszystkie 196 PDF-ów sklasyfikowanych poprawnie.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/odwolania2json/domain/classify.py tests/unit/test_classify.py tests/eval/test_classify_materialy.py
git commit -m "feat: klasyfikacja dokumentow po tresci"
```

---

### Task 6: Ekstrakcja przelewu

**Files:**
- Create: `apps/backend/odwolania2json/domain/base.py`, `apps/backend/odwolania2json/domain/extract_przelew.py`
- Test: `tests/unit/test_extract_przelew.py`, `tests/eval/test_extract_przelew_materialy.py`

**Interfaces:**
- Produces: `odwolania2json.domain.extract_przelew.extract_przelew(pages: list[PageText]) -> Ekstrakcja` (model `Przelew` z `packages/contracts` plus `evidence`), oraz `odwolania2json.domain.base.Ekstrakcja` — dataclass `model: BaseModel`, `evidence: dict[str, tuple[int, int]]`.
- Konsumuje: `normalize_*` z Task 3, modele z Task 2.

- [ ] **Step 1: Napisz testy**

```python
def test_extract_przelew_fields():
    # strona z potwierdzeniem -> data_operacji ISO, kwota float, na_rachunek 26 cyfr,
    # numer_transakcji, tytul, z_rachunku
def test_extract_przelew_evidence_points_to_page():
    # evidence["przelew_bankowy.kwota"][0] == numer strony
def test_missing_field_is_null_not_missing():
    # brak numeru transakcji -> model_dump() ma klucz z wartoscia None
```
`tests/eval/test_extract_przelew_materialy.py`: dla każdego `przyklad_*/potwierdzenie_przelewu.pdf` porównaj z `przyklad_*/przelew.json` — identyczny zestaw kluczy i typów oraz zgodność `data_operacji`, `kwota`, `na_rachunek`, `z_rachunku`, `numer_transakcji` (dokładnie) i `tytul` (próg 0,55 rapidfuzz).

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_extract_przelew.py -v`
Expected: FAIL — brak modułu.

- [ ] **Step 3: Zaimplementuj**

Kierunek rachunków: „z rachunku” / „z konta” / „zleceniodawca” → `z_rachunku`; „na rachunek” / „do odbiorcy” / „beneficjent” → `na_rachunek`. Kwota: etykiety „kwota”, „kwota przelewu”, „przelew kwotą”. Data operacji: „data operacji”, „data wykonania przelewu”. Tytuł: „tytuł”, „tytuł przelewu”, „opis". Numer transakcji: „numer transakcji", „identyfikator transakcji" — wzorzec `CEN` + cyfry.

- [ ] **Step 4: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_extract_przelew.py tests/eval/test_extract_przelew_materialy.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/odwolania2json/domain/base.py apps/backend/odwolania2json/domain/extract_przelew.py tests/unit/test_extract_przelew.py tests/eval/test_extract_przelew_materialy.py
git commit -m "feat: ekstrakcja potwierdzenia przelewu"
```

---

### Task 7: Ekstrakcja pełnomocnictwa

**Files:**
- Create: `apps/backend/odwolania2json/domain/extract_pelnomocnictwo.py`
- Test: `tests/unit/test_extract_pelnomocnictwo.py`, `tests/eval/test_extract_pelnomocnictwo_materialy.py`

**Interfaces:**
- Produces: `extract_pelnomocnictwo(pages: list[PageText]) -> Ekstrakcja` (model `Pelnomocnictwo` plus `evidence`).

- [ ] **Step 1: Napisz testy**

```python
def test_extract_mocodawca_and_pelnomocnik():
    # dokument pelnomocnictwa -> mocodawca[0].data.nazwa, nip, typ osoba_prawna, krs
def test_extract_two_pelnomocnikow():
    # lista pelnomocnicy ma dwa elementy zgodnie z dokumentem
def test_pesel_null_when_absent():
    # pesel is None, klucz obecny
def test_typ_enum_values():
    # typ ∈ {"osoba_prawna", "osoba_fizyczna"}
```
`tests/eval/test_extract_pelnomocnictwo_materialy.py`: porównanie z `przyklad_*/pelnomocnictwo.json` — zestaw kluczy, `mocodawca[].data.nazwa` i `nip` dokładnie, `pelnomocnicy[].imie_nazwisko` dokładnie, listy porównywane po treści.

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_extract_pelnomocnictwo.py -v`
Expected: FAIL — brak modułu.

- [ ] **Step 3: Zaimplementuj**

Mocodawca: sekcja po etykiecie „mocodawca” / „udzielający pełnomocnictwa" / „w imieniu"; nazwa z linii „z siedzibą" albo pierwszej linii pod nagłówkiem firmy; KRS i NIP przez etykiety; `typ` = `osoba_fizyczna`, gdy obecne `imie_nazwisko` i brak KRS, inaczej `osoba_prawna`. Podpisujący: etykiety „podpisujący", „podpisuje", „reprezentacja" — imię i nazwisko z linii po etykiecie. Pełnomocnicy: etykiety „pełnomocnikiem", „pełnomocnik", „udzielamy pełnomocnictwa" — imię i nazwisko; PESEL przez `normalize_pesel` na 11 cyfrach.

- [ ] **Step 4: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_extract_pelnomocnictwo.py tests/eval/test_extract_pelnomocnictwo_materialy.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/odwolania2json/domain/extract_pelnomocnictwo.py tests/unit/test_extract_pelnomocnictwo.py tests/eval/test_extract_pelnomocnictwo_materialy.py
git commit -m "feat: ekstrakcja pelnomocnictwa"
```

---

### Task 8: Ekstrakcja odwołania i detektor zaskarżonej czynności

**Files:**
- Create: `apps/backend/odwolania2json/domain/extract_odwolanie.py`, `apps/backend/odwolania2json/domain/zaskarzana_czynnosc.py`
- Test: `tests/unit/test_zaskarzana_czynnosc.py`, `tests/unit/test_extract_odwolanie.py`, `tests/eval/test_extract_odwolanie_materialy.py`

**Interfaces:**
- Produces:
  - `odwolania2json.domain.zaskarzana_czynnosc.ZaskarzanaCzynnosc` — dataclass `powod_id: int | None`, `opis: str | None`, `data: str | None`, `fragment: str | None`
  - `detect_zaskarzana_czynnosc(pages: list[PageText]) -> ZaskarzanaCzynnosc`
  - `odwolania2json.domain.extract_odwolanie.extract_odwolanie(pages: list[PageText]) -> Ekstrakcja` (model `Odwolanie` plus `evidence`)

- [ ] **Step 1: Napisz testy**

```python
def test_detect_powod_from_act_before_first_zarzut():
    # tekst: "...poinformował o odrzuceniu oferty..." + "Zarzut nr 1 ..." -> powod_id 1
def test_detect_powod_ignores_zarzut_header_trap():
    # sam naglowek zarzutu bez opisu czynnosci -> brak pewnosci (powod_id None)
def test_detect_returns_date_of_challenged_act():
    # data czynnosci, nie pierwsza data w dokumencie
def test_opis_matches_dictionary():
    # opis == APPEAL_REASONS[powod_id] dokladnie
```
`tests/unit/test_extract_odwolanie.py`: `Odwołujący[0].nazwa`, `Zamawiający[0].nazwa`, `ZamowieniePubliczne.tytul` odczytane z dokumentu; `przez-pelnomocnika` jako `1`; `prowadzacy_postepowanie` jako `None` gdy brak informacji.
`tests/eval/test_extract_odwolanie_materialy.py`: porównanie z `przyklad_*/odwolanie.json` — zestaw kluczy i typów identyczny, `czynnosc_powod_id` dokładnie, `czynnosc_opis` dokładnie ze słownika `main-7590db8`, `numer_bzp` i `numer_ted` dokładnie po normalizacji, `tytul` i nazwy stron po treści (próg 0,55).

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_zaskarzana_czynnosc.py tests/unit/test_extract_odwolanie.py -v`
Expected: FAIL — brak modułów.

- [ ] **Step 3: Zaimplementuj detektor zaskarżonej czynności**

Krok 1: znajdź pozycję pierwszego zarzutu (regex `zarzut\s+nr\s*1`). Krok 2: cofnij się o okno 1500 znaków przed tą pozycją. Krok 3: w oknie znajdź zdanie zawierające frazę zaskarżonej czynności (z 12 fraz słownika, dopasowanie po `fold`, z tolerancją dla form gramatycznych: „odrzuceniu oferty", „wyboru oferty", „wykluczeniu wykonawcy", „specyfikacji warunków zamówienia", „modyfikacji treści SWZ", „odpowiedzi i wyjaśnień do SWZ", „zaniechania odrzucenia oferty", „zaniechania wykluczenia wykonawcy", „unieważnienia postępowania", „zaniechania unieważnienia postępowania", „opisu przedmiotu zamówienia", „projektowanych postanowień umowy"). Krok 4: jeśli w oknie nie ma frazy, sprawdź sam nagłówek pierwszego zarzutu, ale z niższą pewnością; gdy brak — `powod_id=None`. Krok 5: data czynności — najbliższa data w dokumencie przed pozycją zarzutu, ale wyłącznie w obrębie okna z kroku 2 i w obrębie zdania o czynności.

Krok 4 zostaje wyłącznie dla dokumentów, w których okno nie zawiera frazy, a wynik ma wtedy oznaczone `pewnosc="niska"` w dowodzie; wartości domyślne to `None`.

- [ ] **Step 4: Zaimplementuj ekstrakcję odwołania**

Sekcje rozpoznawane po etykietach: „Odwołujący", „Zamawiający", „zamówienie", „numer postępowania", „BZP", „TED". Nazwy stron i tytuły z linii po etykiecie, oczyszczone z cudzysłowów (`strip_quotes`). KRS/NIP/REGON przez `normalize_*`. `numer_ted` przez `normalize_ted`. `numer_postepowania` przez `find_postępowanie_number`. `data` i `miejscowosc` z wiersza nagłówka pierwszej strony (wzorzec „Miejscowość, dnia DD.MM.RRRR" albo „Miejscowość, Rrrrr miesiąc RRRR roku"); gdy brak — `None`. `przez-pelnomocnika` = `1` gdy w sekcji odwołującego występuje pełnomocnik, inaczej `0`.

- [ ] **Step 5: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_zaskarzana_czynnosc.py tests/unit/test_extract_odwolanie.py tests/eval/test_extract_odwolanie_materialy.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/backend/odwolania2json/domain/extract_odwolanie.py apps/backend/odwolania2json/domain/zaskarzana_czynnosc.py tests/unit tests/eval
git commit -m "feat: ekstrakcja odwolania i detektor zaskarzanej czynnosci"
```

---

### Task 9: Serializacja, potok dokumentu i CLI

**Files:**
- Create: `apps/backend/odwolania2json/domain/serialize.py`, `apps/backend/odwolania2json/pipeline.py`, `apps/backend/odwolania2json/cli.py`, `apps/backend/odwolania2json/__main__.py`
- Create: `apps/backend/odwolania2json/llm/__init__.py`, `apps/backend/odwolania2json/llm/client.py`
- Modify: `apps/backend/odwolania2json/__main__.py`
- Test: `tests/unit/test_serialize.py`, `tests/integration/test_cli.py`, `tests/unit/test_llm_client.py`

**Interfaces:**
- Produces:
  - `odwolania2json.domain.serialize.dump_json(model) -> str` — `model_dump(by_alias=True)`, kolejność kluczy z modelu, `ensure_ascii=False`, `indent=2`
  - `odwolania2json.domain.serialize.empty_json() -> str` — `"{}"`
  - `odwolania2json.pipeline.ProcessingResult` — dataclass `filename: str`, `sha256: str`, `document_class: str`, `payload: dict`, `evidence: dict`, `page_count: int`, `has_text_layer: bool`, `duration_ms: int`
  - `odwolania2json.pipeline.process_document(data: bytes, filename: str, ocr: OcrEngine | None = None) -> ProcessingResult`
  - `odwolania2json.cli.main(argv: list[str] | None = None) -> int` — podkomendy `run`, `classify`, `extract`, `evaluate`, `serve`
  - `odwolania2json.llm.client.LlmClient` — Protocol `complete(self, prompt: str, schema_hint: dict | None = None) -> str`
  - `odwolania2json.llm.client.NullLlmClient` — `complete` rzuca `LlmDisabledError`
  - `odwolania2json.llm.client.OpenAiCompatibleClient` — `httpx` + `base_url` + `model` + `klucz` z env, nieużywany w tej gałęzi

- [ ] **Step 1: Napisz testy**

```python
def test_dump_json_keeps_alias_and_order():
    # dump_json(model) ma klucz "przez-pelnomocnika" i kolejność jak w wzorcu
def test_dump_json_uses_null_not_missing_key():
    # brak wartosci -> "numer_ted": null w JSON-ie
def test_empty_json_is_empty_object():
    assert empty_json() == "{}"
```
`tests/integration/test_cli.py`:
```python
def test_cli_run_writes_output_tree(tmp_path):
    # input/case1/a.pdf, input/case1/b.pdf (obcy) -> output/case1/a.json, output/case1/b.json
def test_cli_run_keeps_input_names(tmp_path):
    # nazwa wyniku = nazwa bazowa PDF + .json, podkatalogi odtworzone
def test_cli_run_writes_empty_json_for_foreign_document(tmp_path):
    # zawartosc pliku obcego == "{}"
def test_cli_run_does_not_touch_input(tmp_path):
    # katalog input bez zmian (skasowane testy)
def test_scan_without_ocr_raises_clear_error(tmp_path):
    # skan organizatora + brak silnika OCR -> OcrUnavailableError, nie {} i nie awaria
```
`tests/unit/test_llm_client.py`:
```python
def test_null_llm_client_is_disabled():
    # NullLlmClient().complete("x") -> LlmDisabledError
def test_llm_client_not_used_by_default_pipeline():
    # process_document nie woła klienta LLM
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_serialize.py tests/integration/test_cli.py -v`
Expected: FAIL — brak modułów.

- [ ] **Step 3: Zaimplementuj serializację, potok i port LLM**

`process_document`: odczyt PDF → `extract_pages` → jeśli któraś strona ma pusty tekst, `ocr.recognize(render_page_png(...))` i doklej tekst (bez OCR → `OcrUnavailableError`); klasyfikacja po tekście → ekstrakcja właściwej klasy (z `Ekstrakcja` z Task 6–8) → `ProcessingResult`; dla klasy `nieznany` `payload` = `{}` i `evidence` = `{}`.

`odwolania2json/llm/client.py`: `LlmClient` jako Protocol, `NullLlmClient` rzucający `LlmDisabledError`, `OpenAiCompatibleClient` wysyłający przez `httpx` żądanie `POST {base_url}/chat/completions` z modelem i kluczem z env, z ograniczonymi ponowieniami i bez logowania klucza. Klient nie jest wołany przez potok w tej gałęzi.

- [ ] **Step 4: Zaimplementuj CLI**

`run --input DIR --output DIR [--db URL] [--no-ocr]`: przechodzi po drzewie wejścia, dla każdego `*.pdf` liczy `output/<relacja>/<nazwa>.json`, zapisuje `dump_json` albo `empty_json()`, wypisuje linię `OK <klasa> <plik>`. `classify PLIK` wypisuje klasę. `extract PLIK` wypisuje JSON na standardowe wyjście. `evaluate --data DIR --output DIR` uruchamia pomiar z Task 14 (do czasu jego istnienia wypisuje komunikat o braku modułu). `serve --host --port` uruchamia Uvicorn.

- [ ] **Step 5: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_serialize.py tests/unit/test_llm_client.py tests/integration/test_cli.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/backend/odwolania2json tests/unit/test_serialize.py tests/unit/test_llm_client.py tests/integration/test_cli.py
git commit -m "feat: serializacja JSON, potok dokumentu, port LLM i CLI"
```

---

### Task 10: Warstwa Postgres (opcjonalna)

**Files:**
- Create: `apps/backend/odwolania2json/db/__init__.py`, `apps/backend/odwolania2json/db/migrate.py`
- Create: `apps/backend/odwolania2json/db/migrations/0001_initial.sql`
- Create: `apps/backend/odwolania2json/db/repository.py`
- Modify: `apps/backend/odwolania2json/cli.py` (podkomenda `migrate`)
- Test: `tests/integration/test_db.py`

**Interfaces:**
- Produces:
  - `odwolania2json.db.migrate.MIGRATIONS_DIR: Path` — katalog z plikami migracji `NNNN_nazwa.sql`
  - `odwolania2json.db.migrate.migrate(database_url: str) -> list[str]` — stosuje brakujące migracje po kolei, każdą w własnej transakcji, i zwraca listę zastosowanych wersji; migracja już zastosowana nie jest powtarzana
  - `odwolania2json.db.migrate.applied_versions(database_url: str) -> list[str]`
  - `odwolania2json.db.repository.DocumentRepository(database_url: str)` — metody `migrate()` (woła `migrate`), `save_result(result: ProcessingResult, run_id: str | None) -> str`, `list_documents(limit: int = 50, offset: int = 0, document_class: str | None = None) -> list[dict]`, `get_document(document_id: str) -> dict | None`, `get_extraction(document_id: str) -> dict | None`, `count_documents() -> int`
  - `odwolania2json.db.repository.is_configured(database_url: str | None) -> bool`
  - CLI: `python -m odwolania2json migrate` — stosuje migracje i wypisuje ich wersje

- [ ] **Step 1: Napisz testy**

```python
def test_repository_skipped_without_database_url():
    # pytest.mark.skipif(not os.getenv("DATABASE_URL")) -> testy DB pomijane
def test_migrate_creates_expected_tables():
    # po migrate() tabele documents, runs, extractions, schema_migrations istnieja
def test_migrate_is_idempotent():
    # drugie wywolanie migrate() zwraca pusta liste zastosowanych wersji
def test_save_result_is_idempotent_by_sha256():
    # ten sam PDF dwa razy -> jeden wiersz w documents, dwa w extractions
def test_list_documents_returns_newest_first():
def test_get_document_returns_payload_and_evidence():
```
Testy DB pomijają się bez `DATABASE_URL` (mark `skipif`), a w kontenerze Compose baza jest podłączona i testy muszą przejść.

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/integration/test_db.py -v`
Expected: FAIL — brak modułu `db`.

- [ ] **Step 3: Napisz migrację i migrator**

`migrations/0001_initial.sql` tworzy tabele `documents`, `runs`, `extractions` (kolumny i typy zgodne ze specyfikacją §8) oraz indeksy na `documents(sha256)` i `extractions(document_id)`; plik używa `CREATE TABLE IF NOT EXISTS`, żeby powtórne zastosowanie nie kończyło się błędem.

`migrate.py`: przed migracją zakłada tabelę `schema_migrations(version text primary key, applied_at timestamptz default now())`; wczytuje pliki `*.sql` z `MIGRATIONS_DIR` posortowane po nazwie; każdy niezastosowany plik wykonuje w jednej transakcji i dopisuje wersję do `schema_migrations`; pliki zastosowane są pomijane. Dostęp przez SQLAlchemy Core z `postgresql+pg8000://`.

- [ ] **Step 4: Zaimplementuj repozytorium i podkomendę CLI**

`DocumentRepository.migrate()` woła `migrate(database_url)`. `save_result` zapisuje dokument (deduplikacja po `sha256`) i ekstrakcję (`payload` i `evidence` jako `JSONB`). CLI `migrate` przyjmuje `--database-url` (domyślnie ze zmiennej `DATABASE_URL`), stosuje migracje i wypisuje po jednej linii na wersję.

- [ ] **Step 5: Uruchom testy (bez bazy = pomijane, potem z bazą)**

Run: `python -m pytest tests/integration/test_db.py -v`
Expected: PASS lub SKIPPED z powodu braku `DATABASE_URL`.

- [ ] **Step 6: Commit**

```bash
git add apps/backend/odwolania2json/db apps/backend/odwolania2json/cli.py tests/integration/test_db.py
git commit -m "feat: opcjonalna warstwa Postgres z migracjami"
```

---

### Task 11: API FastAPI

**Files:**
- Create: `apps/backend/odwolania2json/api/__init__.py`, `apps/backend/odwolania2json/api/app.py`, `apps/backend/odwolania2json/api/routes.py`, `apps/backend/odwolania2json/config.py`
- Modify: `packages/contracts/openapi.yaml` (ścieżki API), `packages/contracts/odwolania2json_contracts/models.py` (ponowne wygenerowanie)
- Test: `tests/integration/test_api.py`, `tests/contract/test_openapi.py` (rozszerzenie o ścieżki)

**Interfaces:**
- Produces:
  - `odwolania2json.config.Settings` — dataclass z `input_dir: Path`, `output_dir: Path`, `database_url: str | None`, `llm_base_url: str | None`, `llm_model: str | None`, `llm_api_key: str | None`, `ocr_enabled: bool`, `docs_enabled: bool`; `Settings.from_env() -> Settings`
  - `odwolania2json.api.app.create_app(settings: Settings | None = None) -> FastAPI`
  - Endpointy: `GET /healthz`, `POST /api/documents`, `GET /api/documents`, `GET /api/documents/{id}`, `GET /api/documents/{id}/pdf`, `GET /api/documents/{id}/json`, `GET /api/classes`

- [ ] **Step 1: Napisz testy API**

```python
def test_healthz_ok():
    # GET /healthz -> 200, {"status":"ok"}
def test_healthz_reports_database_state():
    # pole "database": "up" albo "down"
def test_upload_document_returns_class_and_payload():
    # POST /api/documents z przyklad_01/odwolanie.pdf -> 200, klasa odwolanie, klucze payload
def test_upload_foreign_document_returns_empty_object():
    # payload == {}
def test_upload_invalid_file_returns_technical_error():
    # plik nie-PDF -> 422/400 z komunikatem, nie 500
def test_get_document_json_returns_strict_json():
def test_get_unknown_document_returns_404():
def test_classes_endpoint_lists_three_classes():
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/integration/test_api.py -v`
Expected: FAIL — brak modułu `api`.

- [ ] **Step 3: Uzupełnij `openapi.yaml` o ścieżki API**

Ścieżki zgodne z tabelą w specyfikacji §7, `operationId` w formie `healthz`, `upload_document`, `list_documents`, `get_document`, `get_document_pdf`, `get_document_json`, `list_classes`. Odpowiedzi opisane przez modele pydantic (żądanie multipart jako `multipart/form-data`).

- [ ] **Step 4: Wygeneruj modele i zaimplementuj API**

`create_app` montuje trasy, włącza `StaticFiles` z `apps/web/static` i szablony Jinja2 z `apps/web/templates`, ustawia `docs_url=None` gdy `docs_enabled` jest fałszywe. `POST /api/documents` zapisuje PDF w katalogu roboczym, uruchamia `process_document`, zapisuje do bazy, gdy `database_url` jest ustawione, i zwraca `{"document_id": ..., "document_class": ..., "payload": {...}, "evidence": {...}}`.

- [ ] **Step 5: Uruchom testy, mają przejść**

Run: `python -m pytest tests/integration/test_api.py tests/contract/test_openapi.py -v` oraz `python scripts/validate_api.py --stage app`
Expected: PASS — test rozjazdu oraz skrypt potwierdzają zgodność `app.openapi()` ze specyfikacją; skrypt wypisuje `OK` dla etapu `app`.

- [ ] **Step 6: Commit**

```bash
git add apps/backend/odwolania2json/api apps/backend/odwolania2json/config.py packages/contracts tests/integration/test_api.py tests/contract
git commit -m "feat: API FastAPI zgodne z kontraktem OpenAPI"
```

---

### Task 12: UI przeglądarkowa

**Files:**
- Create: `apps/web/templates/base.html`, `apps/web/templates/pulpit.html`, `apps/web/templates/dokument.html`, `apps/web/static/style.css`, `apps/web/static/app.js`
- Test: `tests/integration/test_ui.py`

**Interfaces:**
- Produces: strony `GET /` (pulpit), `GET /dokumenty/{id}` (widok dokumentu), `POST /ui/analiza` (upload formularzem) oraz `GET /api/documents/{id}/pdf` używany przez `<embed>`.

- [ ] **Step 1: Napisz testy UI**

```python
def test_pulpit_renders():
    # GET / -> 200, zawiera znacznik "Odwołania2JSON" i tabelę dokumentow
def test_pulpit_shows_banner_without_database():
    # bez DATABASE_URL -> komunikat "baza wyłączona"
def test_document_view_shows_pdf_and_json():
    # GET /dokumenty/{id} -> 200, zawiera <embed src="/api/documents/{id}/pdf"> i blok JSON
def test_document_view_lists_evidence():
    # tabela dowodow zawiera numer strony
def test_unknown_document_view_returns_404():
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/integration/test_ui.py -v`
Expected: FAIL — brak szablonów.

- [ ] **Step 3: Zaimplementuj szablony**

Pulpit: tabela (nazwa, klasa, rozmiar, strony, czas, data) z filtrem po klasie i formularzem uploadu. Widok dokumentu: dwie kolumny — `<embed>` z PDF i `<pre>` z pretty-printed JSON; pod spodem tabela „pole / wartość / dowód (strona)" z danych `evidence`. Bez zewnętrznych zasobów (żadnego CDN), CSS i JS w `static/`.

- [ ] **Step 4: Uruchom testy, mają przejść**

Run: `python -m pytest tests/integration/test_ui.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web apps/backend/odwolania2json/api tests/integration/test_ui.py
git commit -m "feat: UI przegladarki z widokiem PDF obok JSON"
```

---

### Task 13: Docker, Compose i skrypty startowe

**Files:**
- Create: `infra/docker/Dockerfile`, `infra/docker/postgres/init.sql`, `docker-compose.yml`, `start.bat`, `start.sh`
- Modify: `.env.example`
- Test: `tests/integration/test_docker_files.py` (test statyczny obrazu i compose)

**Interfaces:**
- Produces: obraz `odwolania2json:local` z aplikacją na porcie 8000 i healthcheckiem; `docker compose up --build` uruchamia `api` i `db`.

- [ ] **Step 1: Napisz test statyczny**

```python
def test_dockerfile_uses_pinned_python_image():
    # zawiera "FROM python:3.13" i nie zawiera "latest"
def test_dockerfile_creates_non_root_user():
    # zawiera "useradd" albo "adduser" i "USER "
def test_compose_defines_api_and_db():
    # sekcje "api:" i "db:", postgres z healthcheckiem
def test_env_example_has_no_secrets():
    # wartosci kluczy puste
```

- [ ] **Step 2: Uruchom test, ma paść**

Run: `python -m pytest tests/integration/test_docker_files.py -v`
Expected: FAIL — brak plików.

- [ ] **Step 3: Napisz Dockerfile i Compose**

`Dockerfile`: `FROM python:3.13.5-slim` (przypięta wersja), `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1`, `WORKDIR /app`, `COPY packages/contracts /app/packages/contracts`, `COPY apps/backend /app/apps/backend`, `COPY apps/web /app/apps/web`, `COPY tests /app/tests`, `RUN pip install --no-cache-dir ./packages/contracts ./apps/backend -r apps/backend/requirements-ocr.txt`, użytkownik bez roota (`useradd -m -u 10001 app`), `COPY input output` jako katalogi, `EXPOSE 8000`, `HEALTHCHECK` na `/healthz`, `CMD ["uvicorn", "odwolania2json.api.app:app", "--host", "0.0.0.0", "--port", "8000"]`.
`docker-compose.yml`: usługa `api` (`build.context: .`, `dockerfile: infra/docker/Dockerfile`, port 8000, wolumeny `input`, `output`, zmienne z `.env`), usługa `db` (`postgres:16-alpine`, `healthcheck: pg_isready`, wolumen `pgdata`).
`infra/docker/postgres/init.sql`: tylko bootstrap bazy (np. rozszerzenia); **schemat aplikacji tworzą migracje**, które `api` stosuje przy starcie przez `python -m odwolania2json migrate`.
`start.bat` i `start.sh`: `docker compose up --build`, a gdy Dockera brak — instrukcja uruchomienia przez `pip install -r requirements.txt` i `python -m odwolania2json run`.

- [ ] **Step 4: Uruchom test i zbuduj obraz**

Run: `python -m pytest tests/integration/test_docker_files.py -v` then `docker compose build`
Expected: PASS; obraz zbudowany bez błędów.

- [ ] **Step 5: Sprawdź, że kontener wstaje**

Run: `docker compose up -d && docker compose ps && curl http://localhost:8000/healthz`
Expected: `api` i `db` w stanie `running`, `/healthz` zwraca `{"status":"ok"}`.

- [ ] **Step 6: Commit**

```bash
git add infra docker-compose.yml start.bat start.sh .env.example tests/integration/test_docker_files.py
git commit -m "feat: obraz Docker, Compose i skrypty startowe"
```

---

### Task 14: Własny ewaluator F1 i raport pomiaru

**Files:**
- Create: `apps/backend/odwolania2json/eval/__init__.py`, `apps/backend/odwolania2json/eval/f1.py`, `apps/backend/odwolania2json/eval/evaluate.py`
- Test: `tests/unit/test_f1.py`, `tests/eval/test_f1_materialy.py`
- Create (wynik): `docs/05-weryfikacja/pomiar-f1.md`

**Interfaces:**
- Produces:
  - `odwolania2json.eval.f1.score_document(prediction: dict, reference: dict, threshold: float = 0.8) -> dict` — zwraca `{"tp": int, "tn": int, "fp": int, "fn": int, "fields": [...]}`
  - `odwolania2json.eval.f1.aggregate(scores: list[dict]) -> dict` — zwraca `{"f1": float, "precision": float, "recall": float, "tp": int, "tn": int, "fp": int, "fn": int}`
  - `odwolania2json.eval.evaluate.evaluate_dataset(data_dir: Path, output_dir: Path, threshold: float) -> dict`

- [ ] **Step 1: Napisz testy**

```python
def test_identical_values_count_as_tp():
def test_missing_value_both_sides_counts_as_tn():
def test_wrong_value_counts_as_fp_and_fn():
def test_long_string_uses_threshold():
    # "Kancelaria Adwokacka Sp. z o.o." vs drobna literowa zmiana -> TP przy 0.8, FP przy 0.95
def test_lists_matched_by_content_not_position():
def test_extra_list_element_is_fp():
def test_aggregate_computes_f1():
    # 2*tp/(2*tp+fp+fn)
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/unit/test_f1.py -v`
Expected: FAIL — brak modułu `eval`.

- [ ] **Step 3: Zaimplementuj pomiar**

Normalizacja tekstu przed porównaniem: `collapse_spaces`, `strip_quotes`, `fold` (porównywanie bez diakrytyków i wielkości liter). Podobieństwo: `rapidfuzz.fuzz.ratio` po normalizacji. Listy: dopasowanie elementów po treści (najlepsze dopasowanie powyżej progu, każdy element użyty raz), nadmiarowy element to FP. Skalarne pola: `null` w obu → TN, wartość vs `null` → FP i FN, różne wartości → FP i FN. Pary dokumentów w materiale organizatora łączone po klasie i numerze sprawy (`przyklad_01/potwierdzenie_przelewu.pdf` ↔ `przyklad_01/przelew.json`), nie po nazwie pliku.

- [ ] **Step 4: Uruchom pomiar na 60 sprawach**

Run: `python -m odwolania2json evaluate --data docs/02-materialy/organizator-uzp/dane --output .tmp/eval --threshold 0.8`
Expected: raport zliczający TP/TN/FP/FN i F1; to samo dla progu 0,55.

- [ ] **Step 5: Zapisz raport**

`docs/05-weryfikacja/pomiar-f1.md` zawiera: opis metody (normalizacja, próg, dopasowanie list), liczby TP/TN/FP/FN i F1 dla obu progów, rozbicie na klasy, listę pól o największej liczbie FP oraz jawne zastrzeżenie, że to przybliżenie, nie wynik oficjalnego ewaluatora.

- [ ] **Step 6: Uruchom testy, mają przejść**

Run: `python -m pytest tests/unit/test_f1.py tests/eval/test_f1_materialy.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/backend/odwolania2json/eval tests/unit/test_f1.py tests/eval/test_f1_materialy.py docs/05-weryfikacja/pomiar-f1.md
git commit -m "feat: wlasny ewaluator F1 i raport pomiaru"
```

---

### Task 15: Skrypty testu w Dockerze, ADR i dokumentacja

**Files:**
- Create: `scripts/verify_docker.ps1`, `scripts/verify_docker.sh`, `docs/07-decyzje/ADR-002-fastapi-postgres-ui.md`
- Modify: `README.md`, `docs/README.md`, `docs/04-architektura/README.md`, `docs/05-weryfikacja/README.md`, `docs/07-decyzje/pytania-otwarte.md`, `CHANGELOG.md`, `VERSION`

**Interfaces:**
- Produces: `scripts/verify_docker.ps1` i `scripts/verify_docker.sh` wykonujące 11 kroków ze specyfikacji §11.1 i zwracające kod wyjścia 0 przy pełnym sukcesie.

- [ ] **Step 1: Napisz skrypt testowy**

Kroki w kolejności ze specyfikacji §11.1: build → up → healthz z bazą → healthz bez bazy → pytest w kontenerze → upload PDF ze sprawy → porównanie z referencją → upload skanu z szablonu organizatora → strony UI → wiersze w bazie → batch CLI → down -v. Każdy krok wypisuje `OK <krok>` albo `FAIL <krok> <powód>`; skrypt kończy się `exit 1` po pierwszym `FAIL`. Materiały montowane tylko do odczytu.

- [ ] **Step 2: Uruchom skrypt, ma przejść**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify_docker.ps1`
Expected: wszystkie kroki `OK`, kod wyjścia 0, zapisany raport w `docs/05-weryfikacja/`.

- [ ] **Step 3: Napisz ADR-002**

Treść: kontekst (FastAPI, Postgres, UI bez etapu budowania, OpenAPI jako źródło prawdy), decyzja, alternatywy (React/TypeScript, baza obowiązkowa, OCR w podstawie), konsekwencje (dodatkowa zależność, brak wymagania Node, warunki powrotu do Reacta), status (zaakceptowane 2026-11-21).

- [ ] **Step 4: Zaktualizuj dokumentację i wersjonowanie**

`VERSION` → `0.5.0`. `CHANGELOG.md` — nowa sekcja 0.5.0 z listą zmian. `README.md` — stan „aplikacja zaimplementowana", instrukcja uruchomienia (Docker i pip), opis testu w Dockerze. `docs/README.md` — wiersz o nowym dokumencie projektu. `docs/04-architektura/README.md` — odsyłacz do projektu i status wdrożenia. `docs/05-weryfikacja/README.md` — stan pomiarów i odwołanie do raportu. `docs/07-decyzje/pytania-otwarte.md` — dopisek, że U-Q03 przyjęto roboczo jako `{}` i do potwierdzenia.

- [ ] **Step 5: Uruchom kontrolę dokumentacji**

Run: `python scripts/verify_docs.py`
Expected: `OK: ... materiałów, ... dokumentów, ...`.

- [ ] **Step 6: Uruchom pełny zestaw testów**

Run: `python -m pytest -v` oraz `docker compose exec api python -m pytest -v`
Expected: PASS w obu środowiskach.

- [ ] **Step 7: Commit**

```bash
git add scripts docs README.md CHANGELOG.md VERSION
git commit -m "docs: ADR-002, instrukcja uruchomienia, raport pomiaru i skrypty testu w Dockerze"
```

### Task 16: CI/CD i hook pre-commit

**Files:**
- Create: `scripts/precommit.py`
- Create: `.githooks/pre-commit`
- Create: `.github/workflows/ci.yml`
- Modify: `README.md` (instrukcja włączenia hooka i opis CI)
- Test: `tests/integration/test_ci_files.py`

**Interfaces:**
- Produces:
  - `scripts/precommit.py` — CLI `python scripts/precommit.py [--fast]`; kod wyjścia 0 przy sukcesie, 1 przy błędzie; domyślnie uruchamia w kolejności: `scripts/verify_docs.py`, `scripts/validate_api.py --stage all`, `python -m pytest`; z `--fast` pomija `pytest` i etap `app` walidacji API (szybka kontrola przed commitem)
  - `.githooks/pre-commit` — skrypt sh uruchamiający `python scripts/precommit.py --fast`; włączany poleceniem `git config core.hooksPath .githooks`
  - `.github/workflows/ci.yml` — cztery joby na `ubuntu-latest` z `actions/setup-python@v5` i Pythonem 3.13: `docs` (`python3 scripts/verify_docs.py`), `api` (`python scripts/validate_api.py --stage all`), `test` (`python -m pytest`), `eval` (`python -m pytest -m eval`)

- [ ] **Step 1: Napisz testy statyczne**

```python
def test_ci_workflow_defines_required_jobs():
    # .github/workflows/ci.yml zawiera joby docs, api, test, eval
def test_ci_workflow_uses_python_313():
def test_ci_runs_api_validation():
    # w jobie api jest krok z validate_api.py
def test_precommit_hook_calls_script():
    # .githooks/pre-commit wywoluje scripts/precommit.py
def test_precommit_script_help_runs():
    # python scripts/precommit.py --help -> kod 0
```

- [ ] **Step 2: Uruchom testy, mają paść**

Run: `python -m pytest tests/integration/test_ci_files.py -v`
Expected: FAIL — brak plików CI i hooka.

- [ ] **Step 3: Napisz `scripts/precommit.py`**

Skrypt uruchamia kolejno polecenia jako procesy, wypisuje `OK <opis>` lub `FAIL <opis> <powód>` dla każdego kroku i kończy się kodem 1 po pierwszym błędzie. Kroki: kontrola dokumentacji, walidacja API (etap `all`), testy. Opcja `--fast` ogranicza się do kontroli dokumentacji i walidacji etapu `spec`. Skrypt nie wymaga dodatkowych zależności poza standardową biblioteką.

- [ ] **Step 4: Napisz hook i workflow**

`.githooks/pre-commit`:
```sh
#!/bin/sh
exec python scripts/precommit.py --fast
```
Po utworzeniu pliku ustaw bit wykonywalności w indeksie: `git update-index --chmod=+x .githooks/pre-commit`.

`.github/workflows/ci.yml`: workflow `on: [push, pull_request]`, `permissions: contents: read`, każdy job z `actions/checkout@v4`, `actions/setup-python@v5` (`python-version: '3.13'`, `cache: pip`) i instalacją **pliku `requirements.txt` z korzenia repozytorium** (`pip install -r requirements.txt`), który instaluje zależności oraz oba pakiety lokalne w trybie edytowalnym — samo `apps/backend/requirements.txt` nie instaluje pakietów `odwolania2json` i `odwolania2json_contracts`, a testy ich importują.

- [ ] **Step 5: Uruchom testy, mają przejść**

Run: `python -m pytest tests/integration/test_ci_files.py -v` oraz `python scripts/precommit.py`
Expected: PASS; skrypt wypisuje `OK` dla każdego kroku i kończy się kodem 0.

- [ ] **Step 6: Sprawdź hook w praktyce**

Run: `git config core.hooksPath .githooks` potem próba commita bez zmian — hook nie blokuje; przy celowo zepsutej specyfikacji hook kończy się błędem (sprawdź na kopii, bez commitowania).

- [ ] **Step 7: Opisz w README**

Sekcja „Kontrola jakości”: jak włączyć hook (`git config core.hooksPath .githooks`), co sprawdza (`scripts/precommit.py`), jakie są joby CI i jak uruchomić pełną weryfikację w Dockerze (`scripts/verify_docker.ps1` / `.sh`).

- [ ] **Step 8: Commit**

```bash
git add scripts/precommit.py .githooks/pre-commit .github/workflows/ci.yml tests/integration/test_ci_files.py README.md
git commit -m "feat: CI, skrypt walidacji API i hook pre-commit"
```

---

## Śledzenie wykonania

- [ ] Task 1: Szkielet repozytorium i pakiety
- [ ] Task 2: Kontrakt OpenAPI i generowane modele pydantic
- [ ] Task 3: Normalizatory pól
- [ ] Task 4: Odczyt PDF i interfejs OCR
- [ ] Task 5: Klasyfikacja dokumentów po treści
- [ ] Task 6: Ekstrakcja przelewu
- [ ] Task 7: Ekstrakcja pełnomocnictwa
- [ ] Task 8: Ekstrakcja odwołania i detektor zaskarżonej czynności
- [ ] Task 9: Serializacja, potok dokumentu i CLI
- [ ] Task 10: Warstwa Postgres (opcjonalna)
- [ ] Task 11: API FastAPI
- [ ] Task 12: UI przeglądarkowa
- [ ] Task 13: Docker, Compose i skrypty startowe
- [ ] Task 14: Własny ewaluator F1 i raport pomiaru
- [ ] Task 15: Skrypty testu w Dockerze, ADR i dokumentacja
- [ ] Task 16: CI/CD i hook pre-commit
