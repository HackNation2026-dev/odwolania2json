---
wersja: 0.6.1
aktualizacja: 2026-11-21
status: plan implementacji zadań 1–4
---

# Loader, ewaluator, CLI i zamrożenie zbioru — plan implementacji

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zrealizować zadania 1–4 z backlogu (loader 60 spraw, ewaluator F1, CLI input→output na atrapie, zamrożenie podziału) oraz długu „rozbieżność wersji".

**Architecture:** Cztery niezależne moduły w `apps/backend/odwolania2json/` (loader, evaluator, engine-stub + CLI, dataset) testowane TDD. Loader czyta materiały organizatora tylko do odczytu i nakłada poprawki w pamięci; ewaluator porównuje drzewa JSON pole po polu; CLI przechodzi drzewo katalogów i zapisuje atomowo; podział zbioru jest zamrożony w pliku JSON z testem niezmienności.

**Tech Stack:** Python 3.13, pydantic v2 (granice plików), pytest, ruff + mypy --strict, istniejący `scripts/ci.py`.

**Spec:** docs/00-organizacja/backlog.md (zadania 1–4, długi), docs/03-wymagania/kontrakt-danych.md, docs/04-architektura/architektura-wewnetrzna.md (§1, §11), docs/07-decyzje/ADR-002-decyzje-po-recenzji.md (pkt 14).

## Global Constraints

- Python 3.13, pełne adnotacje typów, `mypy --strict` bez błędów, `ruff check` + `ruff format`.
- Oryginały organizatora (`docs/02-materialy/`) nienaruszone — kody tylko czytają.
- Poprawki referencji nakładane w pamięci z `docs/02-materialy/organizator-uzp-aktualizacje/main-7590db8/`.
- Nazwy i komentarze: nazwy kodu po angielsku, docstringi/komentarze po polsku („dlaczego").
- F1 = `2*TP/(2*TP+FP+FN)`; przy mianowniku 0 → `0.0` (konserwatywnie, przypięte testem).
- Błąd techniczny jawny, nigdy zmyślone dane; zapis plików atomowy (tmp + `os.replace`).
- Każde zadanie: test przed kodem, atomowy commit, osobny zakres plików.
- Cechy klas: `odwolanie`, `pelnomocnictwo`, `przelew`, `obcy`.

## Review Focus

1. **Brak nałożonych poprawek organizatora** — przykłady 19/23/25/44/55 muszą mieć `czynnosc_opis` = „Odpowiedzi/wyjaśnienia do SWZ"; test: `test_loader_applies_organizer_corrections` (Task 1).
2. **Nazwa wyniku ze stałej klasy zamiast z wejścia** — `potwierdzenie_przelewu.pdf` → `potwierdzenie_przelewu.json`, referencją pozostaje `przelew.json`; test: `test_result_name_follows_input` i `test_loader_maps_transfer_confirmation` (Task 1, Task 3).
3. **Loader modyfikuje oryginały** — test: SHA-256 materiałów przed i po `load_case_references` identyczne (Task 1).
4. **Ewaluator liczy złą wartość jako TN zamiast FP** — test ręczny: różnica wartości pola = 1 FP (nie TN, nie brak zdarzenia) (Task 2).
5. **Błąd jednego dokumentu zabija przetwarzanie reszty** — test: drugi dokument w innym katalogu dostaje wynik mimo błędu pierwszego, kod wyjścia 1 (Task 3).

---

### Task 0: Ujednolicenie wersji pakietów z VERSION

**Files:**
- Modify: `apps/backend/odwolania2json/__init__.py`
- Modify: `packages/contracts/odwolania2json_contracts/__init__.py`

**Interfaces:**
- Produces: `__version__ == "0.6.1"` w obu pakietach; `scripts/release.py` przestaje blokować.

- [ ] **Step 1: Sprawdź stan**

Run: `git grep '__version__' -- apps packages`
Expected: dwa wystąpienia `0.5.0`; `VERSION` = `0.6.1`.

- [ ] **Step 2: Zmień `__version__` na `0.6.1` w obu plikach**

- [ ] **Step 3: Kontrole**

Run: `python scripts/ci.py --profile commit` (po `git add`)
Expected: PASS (lint, mypy, testy zmienionych modułów).

- [ ] **Step 4: Commit**

```bash
git add apps/backend/odwolania2json/__init__.py packages/contracts/odwolania2json_contracts/__init__.py
git commit -m "chore: ujednolicenie wersji pakietow z VERSION (0.6.1)"
```

### Task 1: Loader 60 spraw

**Files:**
- Create: `apps/backend/odwolania2json/loader.py`
- Test: `tests/unit/test_loader.py`

**Interfaces:**
- Produces (używają Task 2/3/4):
  - `MATERIALS_DIR: Path` (repo/docs/02-materialy/organizator-uzp), `CORRECTIONS_DIR: Path` (…-aktualizacje/main-7590db8)
  - `DocumentClass = Literal["odwolanie", "pelnomocnictwo", "przelew", "obcy"]`
  - `CaseReference` (pydantic, frozen): pola `case_id: str`, `input_name: str` (nazwa PDF), `document_class: DocumentClass`, `reference_name: str | None` (nazwa pliku referencji lub `None` dla obcego)
  - `load_case_references(materials_dir: Path = MATERIALS_DIR, corrections_dir: Path | None = CORRECTIONS_DIR) -> list[CaseReference]` — 60 spraw × 3 klasy + wszystkie PDF z `dane/negatywne/` jako `obcy`
  - `load_reference_json(ref: CaseReference, materials_dir: Path = MATERIALS_DIR, corrections_dir: Path | None = CORRECTIONS_DIR) -> dict` — treść referencji z nałożonymi poprawkami; obcy → `{}`; plik referencji mógłby nie istnieć → `{}` jest dozwolone tylko dla `obcy`
  - `result_name_for(input_name: str) -> str` — `"potwierdzenie_przelewu.pdf"` → `"potwierdzenie_przelewu.json"`, `"przyklad odwolanie.pdf"` → `"przykład odwolanie".json` (stem wejścia + `.json`)
  - `input_to_reference_name(input_name: str) -> str | None` — mapowanie `"potwierdzenie_przelewu.pdf"` → `"przelew.json"`, `"odwolanie.pdf"` → `"odwolanie.json"`, `"pelnomocnictwo.pdf"` → `"pelnomocnictwo.json"`, inne → `None`

Decyzje:
- Stałe mapowanie klas na plik referencji tylko dla trzech znanych nazw PDF; `potwierdzenie_przelewu.pdf` ↔ `przelew.json` to jedyny „przezywany" przypadek (ADR-002 pkt 14).
- Poprawki: dla `przyklad_19|23|25|44|55` referencja `odwolanie.json` czytana z `corrections_dir`, nie z `materials_dir` (nakładanie w pamięci: funkcja zwraca treść, nie zapisuje).
- `load_case_references` nie wymaga, by sprawa miała wszystkie trzy PDF-y — buduje wpisy z istniejących plików.

- [ ] **Step 1: Napisz testy (czerwone)**

Kluczowe asercje (nazwy po angielsku):
- `test_loads_all_60_cases_with_three_classes` — 180 wpisów klas „pozytywnych", po 3 na sprawę.
- `test_negatives_are_foreign_documents` — każdy PDF z `dane/negatywne/`: `document_class == "obcy"`, `reference_name is None`.
- `test_loader_applies_organizer_corrections` — dla spraw 19/23/25/44/55 `load_reference_json` zwraca `czynnosc_opis == "Odpowiedzi/wyjaśnienia do SWZ"` tam, gdzie referencja bazowa ma „…i wyjaśnienia…"; pliki w `materials_dir` niezmienione.
- `test_loader_maps_transfer_confirmation` — `input_to_reference_name("potwierdzenie_przelewu.pdf") == "przelew.json"`.
- `test_result_name_follows_input` — `result_name_for("potwierdzenie_przelewu.pdf") == "potwierdzenie_przelewu.json"`.
- `test_loader_does_not_modify_originals` — SHA-256 wszystkich plików materiałów przed i po obu funkcjach identyczne.
- `test_obcy_reference_is_empty_dict` — dla obcego `load_reference_json == {}`.

- [ ] **Step 2: Uruchom testy — zawodzą**

Run: `pytest tests/unit/test_loader.py -v`
Expected: FAIL (brak modułu `loader`).

- [ ] **Step 3: Zaimplementuj `loader.py`**

Minimalna implementacja wg sygnatur powyżej; walidacja wejść pydantic (`CaseReference`); ścieżki materials/corrections jako parametry (bez stanu globalnego).

- [ ] **Step 4: Testy przechodzą**

Run: `pytest tests/unit/test_loader.py -v`
Expected: PASS.

- [ ] **Step 5: Kontrole i commit**

Run: `ruff check apps/backend tests/unit/test_loader.py && ruff format --check apps/backend/odwolania2json/loader.py tests/unit/test_loader.py && mypy --strict apps/backend/odwolania2json/loader.py`
```bash
git add apps/backend/odwolania2json/loader.py tests/unit/test_loader.py
git commit -m "feat: loader 60 spraw z poprawkami organizatora i mapowaniem przelewu"
```

### Task 2: Ewaluator TP/TN/FP/FN i F1

**Files:**
- Create: `apps/backend/odwolania2json/evaluator.py`
- Test: `tests/unit/test_evaluator.py`

**Interfaces:**
- Produces (używa Task 3 raport? nie; Task 9 później):
  - `Verdict = Literal["tp", "tn", "fp", "fn"]`
  - `FieldOutcome` (frozen): `path: str` (kropkowa ścieżka pola), `verdict: Verdict`
  - `DocumentMetrics` (frozen): `case_id: str`, `input_name: str`, `document_class: DocumentClass`, `outcomes: list[FieldOutcome]`, `classification: Verdict | None` (None tylko gdy obie klasy „obcy" — wtedy None)
  - `ClassTotals` (frozen): `tp: int`, `tn: int`, `fp: int`, `fn: int`; property `f1: float` = `2*tp/(2*tp+fp+fn)`, mianownik 0 → `0.0`
  - `compare_document(predicted: dict, reference: dict) -> list[FieldOutcome]` — rekurencyjne porównanie liści
  - `evaluate_document(case: CaseReference, predicted: dict, reference: dict, predicted_class: DocumentClass) -> DocumentMetrics`
  - `summarize(metrics: list[DocumentMetrics]) -> dict` — raport JSON: totaly per pole i klasa, F1 per klasa i dokument, klasyfikacja osobno

Decyzje:
- Porównanie liści: wartość równa → TN (brak jest też „równa": `None`/brak klucza po obu stronach = TN); referencja ma wartość, przewidziana inna → FP + FN (zła wartość to jednocześnie FP i FN); przewidziana wartość przy referencyjnym braku → FP; referencyjna wartość przy przewidywanym braku → FN.
- Listy: dopasowanie po treści — elementy referencyjne bez dopasowania = FN, przewidywane bez dopasowania = FP (na ścieżce listy).
- Struktura (obcy klucz, zmiana typu) liczy się jak pole: obcy klucz w przewidzianym = FP, brakujący klucz referencyjny = FN; liść tylko po jednej stronie = odpowiednio FN/FP.
- Klasyfikacja osobno: `predicted_class == case.document_class` → TP, inaczej FP+FN na węźle `classification`; TN gdy obie `obcy`? Nie — dla `obcy`/`obcy` klasyfikacja jest poprawna i rejestrowana jako TP na `classification` (tnie „obcy wykryty jako obcy"); None rezerwowane dla braku oceny.
- Dowody nie wchodzą do metryk (raport dowodów poza ocenianym JSON-em — kontrakt danych).

- [ ] **Step 1: Napisz testy z ręcznie policzonymi przypadkami (czerwone)**

- `test_identical_documents_all_tn` — identyczne JSON-y: same TN na liściach.
- `test_wrong_value_is_fp_and_fn_not_tn` — referencja `"kwota": 200.0`, przewidziana `"kwota": 100.0` → dokładnie 1 FP i 1 FN na `path == "przelew_bankowy.kwota"`, zero TN.
- `test_missing_field_is_fn` — przewidziany brak klucza referencyjnego → FN.
- `test_extra_field_is_fp` — przewidziany klucz nieobecny w referencji → FP.
- `test_both_missing_is_tn` — `null`/brak klucza po obu stronach → TN.
- `test_lists_matched_by_content` — referencja `["a","b"]`, przewidziana `["b","c"]` → 1 FN („a"), 1 FP („c"), 1 TN („b").
- `test_f1_formula_hand_computed` — dla TP=2, FP=1, FN=1 → F1 = 2*2/(2*2+1+1) = 0.666… (przybliżenie 1e-9).
- `test_f1_zero_when_denominator_zero` — same TN → F1 == 0.0.
- `test_classification_verdict` — `predicted_class="przelew"` przy `document_class="obcy"` → `classification == "fn"` + `"fp"` zapisane jako wspólny `Verdict`? Decyzja: `classification` przychodzi jako `Literal["tp","fp+fn","tn"]`? — Uprość: `classification: Verdict` i zła klasa = 1 FP i 1 FN liczone w `summarize` z jednego pola `classification == "fn"` (konwencja: `fn` oznacza „niezgodność klasy"); test przypina tę konwencję.
- `test_summarize_report_shape` — raport JSON ma klucze `totals`, `per_class`, `per_document`, `classification`.

- [ ] **Step 2: Uruchom testy — zawodzą**

Run: `pytest tests/unit/test_evaluator.py -v`
Expected: FAIL (brak modułu).

- [ ] **Step 3: Zaimplementuj `evaluator.py`**

Sygnatury jak wyżej; bez zależności od loadera poza typem `CaseReference` (parametr `case` może przyjmować tylko potrzebne pola — przekaż `CaseReference` z loadera).

- [ ] **Step 4: Testy przechodzą**

Run: `pytest tests/unit/test_evaluator.py -v`
Expected: PASS.

- [ ] **Step 5: Kontrole i commit**

Run: `ruff check && ruff format --check && mypy --strict apps/backend/odwolania2json/evaluator.py`
```bash
git add apps/backend/odwolania2json/evaluator.py tests/unit/test_evaluator.py
git commit -m "feat: ewaluator TP/TN/FP/FN per pole, klase i dokument z F1"
```

### Task 3: CLI `process` input → output na atrapie silnika

**Files:**
- Create: `apps/backend/odwolania2json/engine.py`
- Modify: `apps/backend/odwolania2json/cli.py` (dodanie podkomendy `process`)
- Test: `tests/unit/test_cli_process.py`

**Interfaces:**
- Consumes: `result_name_for` z loadera (Task 1).
- Produces:
  - `class StubEngine` z `process(pdf: Path) -> tuple[dict, DocumentClass | None]` — atrapa: zawsze zwraca `({}, None)` (klasyfikacja przychodzi w zadaniu 9; CLI już teraz obsługuje oba wyniki)
  - `run_process(input_dir: Path, output_dir: Path, engine: StubEngine) -> int` — kod wyjścia: `0` wszystkie OK, `1` co najmniej jeden błąd techniczny, `2` błąd użycia
  - podkomenda CLI: `process INPUT_DIR OUTPUT_DIR`
  - `write_json_atomic(path: Path, payload: dict) -> None` — tmp + `fsync` + `os.replace` (eksport do ponownego użycia)

Decyzje:
- Przechodzenie: rekurencyjnie `rglob("*.pdf")`; struktura katalogów output odtwarza input (UZP-06).
- Obcy dokument / brak klasyfikacji: `{}` pod nazwą wejścia (`result_name_for`) — korekta Discord 13:27.
- Niezależność dokumentów: błąd jednego pliku (dostęp, uszkodzony PDF) nie przerywa pętli; błąd zapisany do stderr, plik wynikowy nie powstaje, kod wyjścia 1.
- Atrapa nic nie czyta PDF-a poza istnieniem pliku — brak silnika nie jest błędem.

- [ ] **Step 1: Napisz testy (czerwone)**

- `test_tree_is_recreated` — input `a/b.pdf`, `a/c.pdf`, `d/e.pdf` → output odtworzy `a/`, `d/`.
- `test_foreign_document_gets_empty_json_named_after_input` — wynik `n.pdf` → `n.json` zawierający `{}`.
- `test_result_name_follows_input_for_transfer` — `potwierdzenie_przelewu.pdf` → `potwierdzenie_przelewu.json`.
- `test_document_error_does_not_stop_others` — niedostępny PDF (brak uprawnień/śmieciowy plik) w jednym katalogu; drugi katalog dostaje wynik; kod wyjścia 1.
- `test_exit_code_zero_when_all_ok`.
- `test_exit_code_two_on_missing_input_dir` — brakujący input → kod 2.
- `test_atomic_write_leaves_no_partial_file` — monkeypatch `os.replace` rzucający wyjątek raz → w katalogu nie ma plików częściowych (tylko brak wyniku), błąd zarejestrowany.

- [ ] **Step 2: Uruchom testy — zawodzą**

Run: `pytest tests/unit/test_cli_process.py -v`
Expected: FAIL (brak podkomendy `process`).

- [ ] **Step 3: Zaimplementuj `engine.py` i podkomendę w `cli.py`**

`StubEngine` + `run_process` w `engine.py`; `cli.py` tylko wiąże argumenty i zwraca kod wyjścia.

- [ ] **Step 4: Testy przechodzą**

Run: `pytest tests/unit/test_cli_process.py -v`
Expected: PASS.

- [ ] **Step 5: Kontrole i commit**

Run: `ruff check && ruff format --check && mypy --strict apps/backend/odwolania2json/engine.py apps/backend/odwolania2json/cli.py`
```bash
git add apps/backend/odwolania2json/engine.py apps/backend/odwolania2json/cli.py tests/unit/test_cli_process.py
git commit -m "feat: CLI process input->output na atrapie silnika z atomowym zapisem"
```

### Task 4: Zamrożenie zestawu rozwojowego i kontrolnego

**Files:**
- Create: `data/podzial.json`
- Create: `apps/backend/odwolania2json/dataset.py`
- Test: `tests/unit/test_dataset.py`

**Interfaces:**
- Produces:
  - `data/podzial.json` — `{"metoda": "…", "rozwojowy": ["przyklad_01", …], "kontrolny": ["przyklad_05", …]}` (identyfikatory całych spraw)
  - `Split` (pydantic, frozen): `rozwojowy: frozenset[str]`, `kontrolny: frozenset[str]`
  - `load_split(path: Path = DATA_SPLIT) -> Split` — walidacja rozłączności i pokrycia 60 spraw

Decyzje:
- Podział po **całych sprawach** (identyfikator `przyklad_NN`); negatywne i szablonowe PDF-y nie mają rodzin w 60 sprawach — trafiają do `rozwojowego` (wpis `negatywy: "rozwojowy"` w `metoda`).
- Rodziny duplikatów wśród 60 spraw: przed podziałem sprawdzisz `experiments/2026-11-21-przypadki-brzegowe` (raporty rodzin A/B/C); jeśli istnieją rodziny dzielone między przykłady — cała rodzina do jednej strony podziału. Gdy nie znajdziesz dowodów rodzin w 60 sprawach, stosujesz deterministyczny podział co piąta sprawa do kontrolnego (`przyklad_05,10,…,60` → 12 spraw kontrolnych) i wpisujesz `metoda: "co-piata-sprawa; brak potwierdzonych rodzin duplikatow"`.
- Test niezmienności: SHA-256 pliku `data/podzial.json` zaszyte w teście; zmiana pliku wymaga świadomej zmiany testu.

- [ ] **Step 1: Napisz testy (czerwone)**

- `test_split_covers_all_60_cases` — suma obu stron = 60 unikalnych identyfikatorów `przyklad_NN`.
- `test_split_is_disjoint`.
- `test_split_file_frozen` — SHA-256 pliku równy zaszytemu skrótowi (skrót uzupełnisz po utworzeniu pliku — dwa commity: plik, potem test ze skrótem; lub test ze skrótem wyliczonym z pierwszego utworzonego pliku w tym samym commicie).
- `test_load_split_validates_coverage` — plik z brakującą sprawą → błąd walidacji.

- [ ] **Step 2: Uruchom testy — zawodzą**

Run: `pytest tests/unit/test_dataset.py -v`
Expected: FAIL.

- [ ] **Step 3: Ustal podział i zapisz `data/podzial.json`**

Najpierw sprawdź eksperymenty pod kątem rodzin duplikatów (patrz decyzje), potem zapisz plik.

- [ ] **Step 4: Zaimplementuj `dataset.py` i testy przechodzą**

Run: `pytest tests/unit/test_dataset.py -v`
Expected: PASS.

- [ ] **Step 5: Kontrole i commit**

Run: `ruff check && ruff format --check && mypy --strict apps/backend/odwolania2json/dataset.py`
```bash
git add data/podzial.json apps/backend/odwolania2json/dataset.py tests/unit/test_dataset.py
git commit -m "feat: zamrozenie podzialu zbioru rozwojowy/kontrolny z testem niezmienności"
```

### Task 5: Weryfikacja całości

- [ ] **Step 1: Pełne CI**

Run: `python scripts/ci.py --stage all`
Expected: raport kończy się linią `razem` i jest zielony (docs, lint, types, api, testy z pokryciem, mutacje zmienionych modułów, audit).

- [ ] **Step 2: Raport do użytkownika**

Podsumowanie: co jest gotowe, wynik CI, znalezione odchylenia od planu.
