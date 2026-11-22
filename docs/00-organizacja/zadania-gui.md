---
wersja: 0.1.0
aktualizacja: 2026-11-22
status: lista zadań GUI do wykonania; stan faktyczny ustal w kodzie i testach
---

# Zadania dla agentów: GUI (`apps/web`)

Tylko to, co zostało do zrobienia w GUI. Ogólne zasady pracy, wymagania i zadania silnika: [zadania dla agentów](zadania-dla-agentow.md) (obowiązują także tutaj, zwłaszcza zasady 1–9). Backlog: [backlog](backlog.md). Przepływy: [przepływ urzędnika](../04-architektura/gui/user-flow-urzednik.md), [user flow](../04-architektura/gui/user-flow.md). Decyzje: [ADR-002](../07-decyzje/ADR-002-decyzje-po-recenzji.md) (uzupełnienia 0.7.0 i 0.8.0).

## 1. Stan na 2026-11-22

Fakty sprawdzone komendami na gałęzi po scaleniu z `main`; wartości w kolumnie „Dowód” zostały uruchomione, nie przepisane z raportów.

| Obszar | Stan | Dowód |
|---|---|---|
| Aplikacja `apps/web` (Next 16, React 19.3, TypeScript, Tailwind 4, TanStack Query) | działa **wyłącznie na mocku** w pamięci (`src/lib/api/mock`); brak połączenia z silnikiem | `npm run build`: 19 tras |
| Trasy | `/`, `/dodaj`, `/dokumenty`, `/dokumenty/[id]`, `/dokumenty/eksport`, `/klasy`, `/klasy/[id]`, `/jak-to-dziala`, `/gotowosc`, `/dostepnosc`, `/dziennik`, `/uzytkownicy`, `/uzytkownicy/brak-dostepu`, `/ustawienia`, `/klucz`, `/klucz/kontrola`, `/login`, `/dev-pdf` (tylko demo) | `npm run build` |
| System design | 23 atomy, 28 molekuł, 12 organizmów, 4 szablony, Storybook 10, test zbiorczy axe po wszystkich historiach w obu motywach | `npm run build-storybook`, `npm test` |
| Podgląd PDF | `PdfViewer` na `react-web-pdf-editor` 0.1.6, tylko odczyt, lokalny worker PDF.js, obrys dowodu | `scripts/pdf/REPORT.md` |
| Kontrakt danych | model UI i mock zgodne z `packages/contracts` (klasy `odwolanie`, `pelnomocnictwo`, `przelew`, pusty wynik); test źródła prawdy względem `models.py`/OpenAPI | [`apps/web/REPORT-API-ALIGN.md`](../../apps/web/REPORT-API-ALIGN.md) |
| Makiety | 71 PNG w `apps/web/design/`; pliki FigCraft w [figcraft/](../04-architektura/gui/figcraft/) (trzy pliki uzupełniające) | `ls apps/web/design` |
| Testy | 827 jednostkowych/integracyjnych (Vitest); e2e Playwright desktop+phone, oba motywy, axe | `cd apps/web && npm test` |

**Czego GUI nie robi dziś (najważniejsze):**

1. Nie wywołuje żadnego prawdziwego API: w OpenAPI jest tylko `GET /healthz`, a silnik w `main` to `StubEngine` (zapis `{}`); patrz [ocena architektury](../../experiments/2026-11-21-wybor-modulow/recenzje/fable-ocena-architektury.md) i Z01 w [zadaniach dla agentów](zadania-dla-agentow.md). **Wartość GUI zależy od silnika**: bez Z01 interfejs pokazuje tylko dane syntetyczne.
2. Nie ma edycji pól, szkicu, historii wersji w UI (makiety F11, F15, F24, F33–F35, F53, F12 niezaimplementowane).
3. Nie ma wersji angielskiej (F43–F45).
4. Bramka regresji wizualnej `apps/web/e2e/visual.spec.ts` nie jest zielona dla widoku dokumentu (patrz G05); jej baza zrzutów jest poza Git.
5. Brak bramki CI dla `apps/web` w `scripts/ci.py`; kod TS nie podlega dziś hookom `pre-commit`.

**Wartość punktowa (`docs/01-zadanie/punktacja.md`):** GUI to „inne ciekawe funkcje” (1–10 pkt) w części „elastyczność i rozbudowa” finału; F1 (50% finału) zależy od silnika. Kolejność zadań poniżej wynika z tego.

## 2. Zasady wspólne dla zadań GUI (obowiązują w każdym zadaniu)

1. Przeczytaj `AGENTS.md`, `CLAUDE.md`, [`apps/web/AGENTS.md`](../../apps/web/AGENTS.md) i `apps/web/README.md`. Twarde reguły GUI: jedno miejsce wywołań API (`apps/web/src/lib/api`, reguła ESLint zakazuje `fetch` poza nim), tokeny zamiast literałów hex, dostępność WCAG 2.1 AA, eksport wariantu A (ADR-002 0.7.0), klucz API wyłącznie po stronie serwera.
2. Praca w osobnej gałęzi i worktree według zasady 4 z [zadań dla agentów](zadania-dla-agentow.md); **zakaz `--no-verify`, `SKIP`, `PRE_COMMIT_ALLOW_NO_CONFIG`**.
3. Instalacja: `cd apps/web && npm ci`. Wymagany Node 24 (sprawdzono na v24.22.0). Python do hooków: `.venv` według zasady 3.
4. Komendy kontrolne GUI (wszystkie muszą być zielone przed commitem): `cd apps/web && npm run typecheck && npm run lint && npm test && npm run build && npm run build-storybook`. Plus e2e dla zmienionych przepływów (zasada 6 poniżej).
5. **Biblioteka komponentów zamiast własnych stylów.** Nowy ekran składaj z `apps/web/src/components` (atoms, molecules, organisms, templates); brakujący wzorzec dodaj do biblioteki z historią Storybook (`*.stories.tsx`) i testem, nie kopiuj klas Tailwind między widokami. Zasady: [`apps/web/src/components/REPORT-DS-B.md`](../../apps/web/src/components/REPORT-DS-B.md), `apps/web/README.md`. Test zbiorczy `src/components/stories.test.tsx` uruchamia axe po każdej historii w obu motywach.
6. **E2E:** własny port (np. `E2E_PORT=3150`), katalog wyników `--output=/tmp/<nazwa>-out`. Zanim uruchomisz, sprawdź, że port jest wolny: `ss -ltn "sport = :<port>"`; Playwright ma `reuseExistingServer` i **po cichu użyje cudzego serwera** na zajętym porcie. Nie używaj `pkill`/`killall` (zabijają cudze procesy, także własną powłokę); zatrzymuj tylko własne procesy po PID. Uruchamiaj nie więcej niż 3 workery Playwrighta naraz.
7. **Zawsze obejrzyj efekt:** dla zmiany widoku zrób zrzut (Playwright lub `npm run dev`) w jasnym i ciemnym motywie, na 1440 px i 360 px, porównaj z makietą `apps/web/design/F*.png` (odczyt obrazu) i wypisz w raporcie odstępstwa „makieta → implementacja”.
8. **Kod czytelny:** wielowierszowy JSX, pliki do ok. 250 linii, nazwy po angielsku w kodzie, teksty UI po polsku. Dane tylko syntetyczne.
9. Nie edytuj wygenerowanych plików (`src/lib/api/contract.generated.json`, `public/pdf/*`, `public/demo-pdf/*`). Odtwarzaj je skryptami (`scripts/generate-ui-contract.py`, `npm run pdf:assets`, `npm run pdf:demo`).
10. Po zakończeniu: `CHANGELOG.md`, status w tym pliku (wykreśl wykonane zadanie) i raport z wynikami komend (końcówki wyklejone, nie opisane).

## 3. Zadania P0: połączenie GUI z silnikiem

### G01. Kontrakt API v1 dla GUI w `openapi.yaml`

**Cel.** `packages/contracts/odwolania2json_contracts/openapi.yaml` definiuje ścieżki, których potrzebuje GUI, tak by GUI i backend wytwarzały zgodne implementacje. Dziś jest tylko `GET /healthz`.

**Przeczytaj.** [`apps/web/REPORT-API-ALIGN.md`](../../apps/web/REPORT-API-ALIGN.md), sekcja „Brakujące API — propozycje” (tabela metod mocka → ścieżek); `apps/web/src/lib/api/client.ts` (interfejs `ApiClient`, pełna lista metod UI), `schemas.ts`, `processing.ts`, `codes.ts`; `docs/04-architektura/architektura-wewnetrzna.md` §4.3–§4.6, §6, §9; `AGENTS.md` (sekcja „API i kontrakt”); skill `generate-api`; backlog nr 5.

**Kroki.**
1. Utwórz gałąź i worktree (zasada 4). Zrób to **w tym samym zadaniu co Z14** albo po nim, jeśli backend ma już FastAPI; nie duplikuj ścieżek.
2. Dla każdej metody z `ApiClient` zdecyduj: jest w v1 (silnik) czy poza (E3: użytkownicy, audyt, retencja – zostają mockiem). Zapisz decyzję w tabeli w opisie PR.
3. Dopisz do `openapi.yaml` (OpenAPI 3.1) co najmniej: `GET /api/v1/system`, `GET /api/v1/dashboard`, `GET /api/v1/documents`, `GET /api/v1/documents/{id}`, `POST /api/v1/batches`, `POST /api/v1/documents/{id}/runs`, `GET /api/v1/documents/{id}/pipeline`, `GET /api/v1/documents/{id}/diagnosis`, `GET /api/v1/documents/{id}/result`, `GET .../evidence`, `GET .../report`, `GET .../export-decision`, `GET /api/v1/classes`, `GET /api/v1/codes`. Błędy: RFC 7807 (`application/problem+json`) z polem `code` ze słownika `codes.ts`. Każda operacja ma `operationId`.
4. Schematy odpowiedzi budują na istniejących modelach wyniku (`Odwolanie`, `Pelnomocnictwo`, `Przelew`, `PustyWynik`); nie powielaj ich. Dowód wg architektury §4.5 (strona, cytat, źródło `text|ocr`, metoda, przesłanki, pewność opcjonalna, geometria opcjonalna w ułamkach strony 0..1, układ jak w `PdfHighlight`).
5. Wygeneruj modele: `python scripts/generate_contracts.py`; nie edytuj wygenerowanych plików ręcznie.
6. Zaktualizuj migawkę kontraktu GUI: `python3 apps/web/scripts/generate-ui-contract.py` i zatwierdź zmiany `contract.generated.json`; dopasuj `apps/web/src/lib/api/contract.ts` i testy kontraktu tak, by nadal sprawdzały klucze względem `models.py`.
7. Test kontraktowy: `python scripts/validate_api.py --stage all` zielony; dodaj test, który każdą operację z `openapi.yaml` porównuje z listą metod `ApiClient` (nazwa operacji ↔ metoda), tak by dopisanie metody po jednej stronie bez drugiej psuło test.

**Kryteria akceptacji.** `python scripts/ci.py --stage all` zielone; `validate_api.py --stage all` zielone; każda metoda `ApiClient` mająca odpowiednik w v1 ma operację w `openapi.yaml`; tabela decyzji w PR.

**Weryfikacja.** `.venv/bin/python scripts/validate_api.py --stage all`; `.venv/bin/python scripts/ci.py --stage all`; `cd apps/web && npm test`.

**Pułapki.** Zmiana łamiąca kontrakt wymaga nowej wersji API i ADR. Klucza LLM nie wolno dodawać do żadnej odpowiedzi API. W OpenAPI nie ma polskich etykiet pól (to metadane UI): nie dopisuj ich do kontraktu, zostają w `contract.generated.json`/UI.

**Zależności.** Z01–Z03 (silnik i polityka eksportu). Bez nich kontrakt można zapisać, ale nie zweryfikować na prawdziwych odpowiedziach.

### G02. Klient HTTP i typy z kontraktu zamiast mocka

**Cel.** `apps/web/src/lib/api/index.ts` potrafi wybrać klienta `http` (prawdziwe API) zamiast `mock`, a typy TypeScript API są generowane z `openapi.yaml` (zasada z `AGENTS.md`: „klienty generuj z kontraktu, np. `openapi-typescript`”).

**Przeczytaj.** `apps/web/src/lib/api/index.ts`, `client.ts`, `hooks.ts`, `schemas.ts`, `contract.ts`; `AGENTS.md` (sekcja „API i kontrakt”); dokumentację `openapi-typescript` przez `npx ctx7@latest library "openapi-typescript" "generate types from OpenAPI 3.1"` (nie polegaj na pamięci).

**Kroki.**
1. Dodaj `openapi-typescript` (devDependency, dokładna wersja) i skrypt `npm run api:types`, który z `../../packages/contracts/odwolania2json_contracts/openapi.yaml` generuje `src/lib/api/generated/openapi.d.ts`. Plik oznacz nagłówkiem „wygenerowany, nie edytuj”.
2. Napisz `src/lib/api/http/client.ts` implementujący `ApiClient`: jedna funkcja `request()` (jedyne miejsce `fetch`), baza adresu z `NEXT_PUBLIC_API_BASE_URL` (domyślnie ten sam origin), błędy `application/problem+json` mapowane na `ApiError(code, message)`, brak ponowień dla 401/403 (user-flow §7.8), ponowienia z limitem dla 5xx/sieci tylko dla odczytów (GET).
3. Odpowiedzi parsuj schematami Zod z `schemas.ts` na granicy (zasada: waliduj wejście); niezgodność odpowiedzi to `ApiError("INVALID_RESPONSE")`, nie wyjątek w komponencie.
4. W `index.ts` wybór klienta przez `NEXT_PUBLIC_API_MODE=mock|http` (domyślnie `mock`, tryb demonstracyjny nadal działa bez backendu). Dla metod bez odpowiednika w v1 (użytkownicy, audyt, retencja) w trybie `http` użyj mocka z jawnym oznaczeniem w UI „funkcja demonstracyjna” (zachowaj istniejące oznaczenia „po MVP”).
5. Testy: kontraktowe klienta `http` z atrapą serwera (msw lub `vi.fn` na `fetch` wewnątrz tego jednego pliku), przypadki 200, 404, 409, 401/403 (bez ponowień), 429, 5xx, nieprawidłowy JSON; test, że żaden plik poza `src/lib/api` nie zawiera `fetch(`.
6. E2E: jeden przepływ (dodanie PDF → wynik → pobranie JSON) przeciwko prawdziwemu serwerowi lokalnemu, gdy istnieje (zadanie Z14); do tego czasu przeciwko atrapie serwera HTTP uruchamianej przez Playwright (`webServer`).

**Kryteria akceptacji.** `NEXT_PUBLIC_API_MODE=http` uruchamia aplikację przeciwko serwerowi zgodnemu z `openapi.yaml`; `npm run api:types` jest deterministyczne (drugi przebieg bez zmian w git); wszystkie dotychczasowe testy przechodzą w trybie `mock`.

**Weryfikacja.** `cd apps/web && npm run api:types && git diff --exit-code src/lib/api/generated && npm run typecheck && npm test`.

**Pułapki.** Klucza API nie przekazuj z przeglądarki do `localStorage` ani nagłówków innych niż jedyny, który ustali backend (Z04); GUI wysyła klucz tylko w jednym żądaniu zapisu konfiguracji, jeśli ta funkcja powstanie. Nie wprowadzaj drugiego miejsca `fetch`. Wygenerowanych typów nie edytuj.

**Zależności.** G01 (kontrakt). Można zacząć od klienta z atrapą, gdy G01 jest w toku.

### G03. Dostarczenie GUI bez serwera Node (statyczny eksport w pakiecie pip)

**Cel.** GUI uruchamia się z pakietu `pip` bez Node: `pip install` + `odwolania2json serve`. To zapis z ADR-002 0.6.0 (statyczny eksport w pip, bez serwera Node u jury) i backlogu nr 11; [uzupełnienie 0.8.0](../07-decyzje/ADR-002-decyzje-po-recenzji.md) traktuje to jako rozwiązanie zapasowe, bo wymóg „tylko pip” dotyczy etapu 1 (CLI). **Zacznij tylko po decyzji użytkownika**, czy GUI ma być dostarczane przez pip (pytanie 1 w sekcji 6).

**Przeczytaj.** ADR-002 0.6.0 i 0.8.0; `apps/backend/pyproject.toml`; `apps/backend/odwolania2json/cli.py`, `__main__.py`; `apps/web/next.config.ts`; skrypt wydania `scripts/release.py`; Z03 w [zadaniach dla agentów](zadania-dla-agentow.md).

**Kroki.**
1. W `apps/web/next.config.ts` ustaw `output: "export"` (warunkowo przez `NEXT_OUTPUT=export`, aby `npm run dev` działało jak dziś), `trailingSlash: true`, `images: { unoptimized: true }`.
2. Trasy dynamiczne nie eksportują się statycznie. Dziś są dynamiczne: `/dokumenty/[id]`, `/klasy/[id]`, `/dokumenty/eksport` (w `npm run build` oznaczone `ƒ`). Zamień na trasy ze stałą ścieżką i parametrem zapytania (`/dokumenty/szczegoly/?id=…`, `/klasy/szczegoly/?id=…`) albo zrealizuj fallback w serwerze (odpowiedź `index.html` dla nieznanych ścieżek). Zaktualizuj wszystkie linki, testy e2e i dokument [user-flow-urzednik.md](../04-architektura/gui/user-flow-urzednik.md) (mapa tras).
3. Trasę `/dev-pdf` (tylko demo/e2e) wyłącz w eksporcie produkcyjnym (np. zwracaj `notFound()` poza `NODE_ENV !== "production"` albo przenieś poza `src/app`).
4. Skrypt `scripts/build_ui.sh` (i odpowiednik Windows jeśli skrypty startowe powstaną w Z03): `cd apps/web && npm ci && NEXT_OUTPUT=export npm run build` i kopiowanie `apps/web/out/` do `apps/backend/odwolania2json/ui/`.
5. W `apps/backend/pyproject.toml` dodaj `[tool.setuptools.package-data]` obejmujące `odwolania2json/ui/**`, oraz `[project.scripts] odwolania2json = "odwolania2json.__main__:main"`. Przenieś ustawienie UTF-8 wyjścia (dziś tylko w `__main__`) do `main`, aby działało także przez skrypt konsolowy (Windows).
6. Podkomenda `serve` w `cli.py`: serwer na bibliotece standardowej (`http.server`) serwujący katalog `ui/`, domyślnie `127.0.0.1:8000`, opcje `--host`, `--port`, `--open`; nagłówki bezpieczeństwa (CSP bez zasobów zewnętrznych, `X-Content-Type-Options`); bez listowania katalogów. Gdy powstanie API (Z14), `serve` serwuje je pod `/api/v1` z tego samego serwera.
7. Dołącz `ui/` do koła (`scripts/release.py`) i do sdist. Zdecyduj, czy zbudowane pliki są w Git (większa pewność dostarczenia, ryzyko przestarzałości) czy budowane w wydaniu; w obu przypadkach dodaj skrypt `scripts/verify_ui_build.py`, który porównuje hash źródeł `apps/web` z zapisanym hashem budowy i kończy się błędem przy rozbieżności.
8. Test czystej instalacji (`scripts/verify_install.py` lub test integracyjny): nowe `venv`, `pip install <koło>`, `odwolania2json serve --port 0`, pobranie `/` i `/klucz/` (200), brak żądań na zewnętrzne hosty, Playwright przechodzi trasy bazowe na zainstalowanej wersji bez Node w `PATH`.

**Kryteria akceptacji.** Na maszynie bez Node: `pip install`, `odwolania2json serve --open` pokazuje działające GUI (tryb demonstracyjny); test czystej instalacji zielony; zasoby lokalne (brak CDN: worker PDF.js z `/pdf/`).

**Weryfikacja.** `cd apps/web && NEXT_OUTPUT=export npm run build && ls out | head`; `.venv/bin/python scripts/verify_install.py`; `.venv/bin/python scripts/ci.py --stage all`.

**Pułapki.** `public/pdf/pdf.worker.min.mjs` (1,3 MB) i `public/demo-pdf/*` są zasobami vendor (wyjątek w `.pre-commit-config.yaml`); nie dodawaj drugiego workera ani CDN. `basePath` dla statycznego eksportu nie jest przetestowany (raport PDF). Windows nie był sprawdzany (do zrobienia ręcznie, zasada „Do rozstrzygnięcia”, pkt 5).

**Zależności.** Z03 (pakiet pip i skrypty startowe). Opcjonalnie G02.

## 4. Zadania P1: brakujące funkcje GUI

Zadania G05–G08 mają **samodzielne instrukcje (cel, makiety, pliki, kroki, kryteria, komendy, pułapki, zależności)** w raportach wykonawców; to ich pełna treść, nie streszczenie. Przed startem przeczytaj całą sekcję „DO ZROBIENIA” danego raportu.

### G04. Edycja pola, szkic i historia wersji (F11, F15, F24, F33, F34, F35, F53, F12)

**Cel.** Urzędnik poprawia wartość pola z walidacją formatu, zmienia klasę dokumentu, zapisuje poprawkę jako nową wersję wyniku, widzi historię wersji (v1 silnik, v2 korekta, v3 zatwierdzony), porównuje i przywraca wersję (przywrócenie tworzy nową wersję). Wzorce zachowania: [przepływ urzędnika §6](../04-architektura/gui/user-flow-urzednik.md), `projekt-ui.md` §3.3 i §3.5.

**Makiety.** `apps/web/design/F11-walidacja-korekty.png`, `F15-zmiana-klasy.png`, `F24-historia.png`, `F33-niezapisany-szkic.png`, `F34-blad-zapisu.png`, `F35-odmowa-odsloniecia.png`, `F53-zapisywanie.png`, `F12-chroniony-skan.png`.

**Przeczytaj.** `apps/web/src/features/dokument/REPORT-W-DOC.md` (sekcja 4: punkty zaczepienia po refaktorze: `FieldRow` z akcją „Edytuj”, miejsce na pasek szkicu); `apps/web/src/lib/api/schemas.ts` i `client.ts` (`getVersions`, `restoreVersion`, `updateField`); `contract.ts` (walidacja formatów pól względem schematu).

**Kroki.**
1. Zacznij **po** G05 pkt 1 (parytet widoku dokumentu), żeby nie edytować plików równolegle z innym agentem; pracuj w nowym katalogu `apps/web/src/features/dokument-edycja/`.
2. API (dopisz na końcu plików, mock w `src/lib/api/mock/edycja.ts`): `saveFieldDraft`, `commitDraft` (zwraca nową wersję), `changeClassification`, `listVersions`, `compareVersions`, `restoreVersion`. Stany błędu zapisu deterministyczne w mocku (np. dokument `doc-3` zwraca błąd zapisu przy pierwszej próbie).
3. Walidacja pola (F11): użyj `validateFieldValue` z `contract.ts` (format z OpenAPI: NIP, KRS, REGON, TED, kwota, data); komunikat błędu powiązany z polem (`aria-describedby`), „Zastosuj” zablokowane, szkic żyje tylko w pamięci sesji (nie w `localStorage`).
4. Dialogi (biblioteka: `Dialog`): F15 zmiana klasy (lista klas z `listClasses`, „Zmień i wyodrębnij ponownie”, „Anuluj”, fokus w oknie i powrót po zamknięciu), F33 niezapisany szkic przy eksporcie (trzy akcje: zapisz i kontynuuj / odrzuć szkic i kontynuuj / zostań; zamiar kontynuacji zachowany), F35 odmowa odsłonięcia (E3, `Dialog` z `role="alertdialog"`).
5. Stany zapisu: F53 „Zapisywanie…” (przyciski eksportu i zatwierdzenia wstrzymane, `aria-live="polite"`), F34 błąd zapisu (komunikat, „Ponów zapis”, szkic zachowany, eksport wstrzymany).
6. Historia (F24): trasa `/dokumenty/[id]/wersje`: lista wersji dokumentu i wyniku, porównanie dwóch wersji (tabela pól + zakładka „Różnice w JSON”), „Przywróć v1” z potwierdzeniem tworzy nową wersję; po przywróceniu eksport korzysta z najnowszej.
7. Chroniony skan (F12, E3): wariant widoku z zamaskowanymi danymi i „Pokaż dane” zależnym od roli demonstracyjnej; pobranie JSON zablokowane bez flagi. Oznacz „po MVP”.
8. Testy: jednostkowe walidacji i reducerów szkicu, integracyjne każdego dialogu (klawiatura, fokus, Esc), e2e: poprawka pustego pola → szkic → zapis → nowa wersja → eksport odblokowany; błąd zapisu i ponowienie; przywrócenie wersji. Axe w obu motywach.

**Kryteria akceptacji.** Scenariusz z kroku 8 przechodzi na desktopie i telefonie; wersje widoczne w historii; po poprawce wymaganego pustego pola dokument przechodzi z „Częściowy” do „Pełny” i eksport się odblokowuje; zero zmian w eksporcie wariantu A poza źródłem wersji.

**Weryfikacja.** `cd apps/web && npm run typecheck && npm run lint && npm test && npx playwright test e2e/dokument-edycja.spec.ts` (własny `E2E_PORT`).

**Pułapki.** Szkic nie jest wynikiem: nigdy nie trafia do pobieranego JSON ani do dowodów. Edycja nie może zmieniać dowodów silnika; poprawiona wartość ma stan „poprawione” i pochodzi od użytkownika (wersja v2). F12/F35 zakładają role, a logowania nie ma: tylko demonstracja z przełącznikiem w Storybooku, nie w produkcyjnym UI.

**Zależności.** G05 pkt 1; w trybie `http` G01.

### G05. Zaległości obszaru dokumentu (W-DOC)

Źródło instrukcji: [`REPORT-W-DOC.md`](../../apps/web/src/features/dokument/REPORT-W-DOC.md), sekcja „DO ZROBIENIA”, pozycje 1–5.

1. **Zgodność wizualna refaktoru danych i JSON** (priorytet; odblokowuje G04). Doprowadź refaktor widoku dokumentu do 0 różnic względem bazy zrzutów poza celowymi elementami (prawdziwy PDF, drawer diagnozy).
2. **Pełne, spójne fixture PDF i dowodów** (F38/F39: wiele obszarów jednego pola, kolizja grup).
3. **Źródłowy PDF i historyczne OCR z API** (kontrakt źródła PDF; zależy od G01).
4. **Szkic edycji i historia**: to jest G04; nie rób go w ramach G05.
5. **Stabilne oczekiwanie na gotowy PDF w bramce wizualnej** (patrz G10).

**Kryterium akceptacji całej grupy.** `npx playwright test e2e/visual.spec.ts -g "doc-|nie-znaleziono"` daje 0 niezamierzonych różnic względem bazy odtworzonej według G10; `e2e/wdoc.spec.ts` i `e2e/dokument.spec.ts` zielone.

### G06. Zaległości listy, dodawania i pulpitu (W-LISTA)

Źródło: [`REPORT-W-LISTA.md`](../../apps/web/src/features/dokumenty-lista/REPORT-W-LISTA.md), pozycje 1–4: (1) archiwa ZIP i foldery E2 (F28), (2) indywidualna decyzja dla każdej kolizji ścieżki i wiarygodna tożsamość pliku (F54), (3) pełne dopasowanie pulpitu i gotowości do F65/F65d, (4) rzeczywista trasa tabeli w bramce wizualnej.

### G07. Zaległości klas (W-KLASY)

Źródło: [`REPORT-KLASY.md`](../../apps/web/src/features/klasy/REPORT-KLASY.md), pozycje 1–9, w tym: (1) wpięcie gotowego `useClassConfiguration` i `ConfigurationError` w „Nową analizę” (blokada analizy przy braku konfiguracji klas, F46), (2) rzeczywista walidacja i ekstrakcja po zmianie YAML (zależy od Z11 w [zadaniach dla agentów](zadania-dla-agentow.md)), (3) osobny zapis szkicu przed aktywacją, (4) numerowane wiersze i błąd przy konkretnej linii YAML, (5) układ S07 na tablecie, (6) fizyczne wyłączenie przycisku X podczas aktywacji, (7) strona wersji po nieudanej aktywacji, (8) rzeczywiste przypięcia zadań w podsumowaniu aktywacji, (9) aktywne definicje na liście po demonstracyjnej zmianie.

**Dodatkowa luka testowa (G07a).** Domyślny `npx playwright test` pomija 8 przebiegów dwóch scenariuszy klas (`e2e/klasy-scenarios.spec.ts`: `activation-error` i `no-configuration`), bo wymagają osobnego serwera z `NEXT_PUBLIC_MOCK_CLASS_SCENARIO=<scenariusz>`. Zadanie: dodaj w `apps/web/playwright.config.ts` dwa dodatkowe projekty z własnym `webServer` i `env` (każdy na osobnym porcie i `distDir`), tak by cały zestaw uruchamiał oba scenariusze bez ręcznych kroków; kryterium: `npx playwright test e2e/klasy-scenarios.spec.ts` pokazuje 0 pominiętych.

### G08. Zaległości ekranów systemowych (W-SYS)

Źródło: [`REPORT-SYS.md`](../../apps/web/src/features/info/REPORT-SYS.md), pozycje: ścisła deterministyczność pojedynczych pikseli desktopu, ochrona niezapisanego szkicu retencji, pełne zarządzanie rolami E3, retencja i audyt na rzeczywistym serwerze, kontakt/audyt dostępności/identyfikatory incydentów.

### G09. Wersja angielska (F43, F44, F45)

**Cel.** Przełącznik „PL | EN” w nagłówku; pełny widok przeglądu dokumentu po angielsku (F43), reflow 320 px po angielsku (F44, F45). Cytaty i klucze JSON pozostają w języku źródła.

**Makiety.** `apps/web/design/F43-pelny-EN.png`, `F44-reflow-S01.png`, `F45-reflow-S03.png`; opis w `projekt-ui.md` §9.3.

**Kroki.**
1. Wybierz minimalne rozwiązanie bez nowej ciężkiej biblioteki: słowniki `src/lib/i18n/{pl,en}.ts` (typowane kluczami), kontekst `I18nProvider`, hook `useT()`; język w `localStorage` (try/catch) i atrybut `lang` na `<html>`; domyślnie PL. Jeśli rozważasz bibliotekę (np. `next-intl`), sprawdź dokumentację przez `ctx7` i zapisz decyzję w ADR.
2. Wyciągnij teksty UI z widoków do słowników **obszarami**, zaczynając od przeglądu dokumentu i powłoki; test jednostkowy sprawdza, że oba słowniki mają identyczny zestaw kluczy.
3. Zachowaj nazwy pól kontraktu (`numer_bzp`), kody i cytaty bez tłumaczenia.
4. Dodaj `PL | EN` w `SiteHeader` (organizm) z historyjką i testem; fokus i `aria-pressed`.
5. E2E: przełączenie języka zachowuje trasę i stan, `lang` się zmienia, axe w obu językach.

**Kryteria akceptacji.** Widok przeglądu dokumentu w EN zgodny z F43; żaden klucz słownika nie jest pusty w żadnym języku; test zbiorczy axe zielony.

**Pułapki.** Przy wyłączonych obszarach (np. użytkownicy, dziennik) pokaż polski tekst, nie klucz techniczny; nie tłumacz danych syntetycznych.

**Zależności.** G05 (stabilne teksty widoku dokumentu).

## 5. Zadania P2: jakość i porządek

### G10. Bramka regresji wizualnej: odtwarzalna baza i gotowość PDF

**Cel.** `apps/web/e2e/visual.spec.ts` daje powtarzalny wynik na każdej maszynie i nie robi zrzutu niegotowego PDF.

**Stan.** Baza zrzutów (`e2e/visual.spec.ts-snapshots/`) jest poza Git (zależy od systemu i fontów). Wzorzec „stary wygląd” = commit `3dd2b0e` na gałęzi `kacperpaczos/uiui` (przed refaktorem na bibliotekę).

**Kroki.**
1. Odtwórz bazę: `git worktree add ../uiui-baseline 3dd2b0e && cd ../uiui-baseline/apps/web && npm ci && E2E_PORT=<wolny> npx playwright test e2e/visual.spec.ts --update-snapshots --workers=3`; skopiuj katalog `e2e/visual.spec.ts-snapshots/` do swojego worktree. Uruchom bramkę dwa razy i potwierdź 80/80 (powtarzalność).
2. W `visual.spec.ts` zastąp stały `waitForTimeout(1200)` warunkiem gotowości: dla tras z PDF poczekaj na atrybut/element wystawiony przez `PdfViewer` po wyrenderowaniu canvasu i warstwy tekstowej (np. `data-pdf-ready="true"`); dodaj ten atrybut w `src/components/organisms/PdfViewer.tsx` z testem i historią.
3. Trasę tabeli (lista) w bramce oznacz właściwym parametrem widoku (patrz G06 pkt 4).
4. Opisz w `apps/web/README.md`, jak odtworzyć bazę i kiedy ją wolno aktualizować (tylko po obejrzeniu każdej różnicy).

**Kryteria akceptacji.** Dwa kolejne przebiegi bramki dają ten sam wynik; zrzuty tras z PDF zawierają wyrenderowany dokument.

**Pułapki.** Nie podwyższaj progu `maxDiffPixelRatio`, by „zazielenić” bramkę. Zrzuty zawsze porównuj z bazą z tego samego systemu operacyjnego.

### G11. Bramka CI dla `apps/web`

**Cel.** Kod TypeScript podlega tym samym bramkom co Python: `scripts/ci.py` uruchamia etap `web` (typecheck, lint, testy, build, Storybook).

**Przeczytaj.** `scripts/ci.py`, `.pre-commit-config.yaml`, [ADR-003](../07-decyzje/ADR-003-lokalne-ci-cd.md), `docs/00-organizacja/lokalne-ci-cd.md`.

**Kroki.** (1) Dodaj etap `web` do `ci.py` z profilami: `commit` uruchamia tylko gdy w indeksie są zmiany w `apps/web` (typecheck i lint zmienionych plików, testy powiązane), `push` pełny zestaw komend z sekcji 2 pkt 4 bez e2e. (2) Etap pomijany jawnie, gdy brak Node (komunikat, nie ciche przejście). (3) Test jednostkowy `ci.py` dla nowego etapu. (4) Zaktualizuj ADR-003 (zmiana zakresu bramek) i `lokalne-ci-cd.md`.

**Kryteria akceptacji.** `python3 scripts/ci.py --stage web` zielone i czerwone przy celowo zepsutym typie (sprawdź i cofnij); hooki wywołują etap tylko dla zmian w `apps/web`.

**Pułapki.** Zakaz obchodzenia hooków; etap `web` nie może wydłużyć commita powyżej budżetu ok. 10 s (patrz komentarz w `.pre-commit-config.yaml`), więc tylko zmienione pliki.

### G12. Formatowanie kodu (Prettier)

**Cel.** Spójne formatowanie TS/TSX/CSS/MD w `apps/web`.

**Kroki.** (1) Dodaj `prettier` (dokładna wersja) i `.prettierrc` (szerokość 100, podwójne cudzysłowy). (2) `npm run format` i `npm run format:check`. (3) Jedna zmiana **tylko formatująca**, w osobnym commicie bez zmian logiki, wykonana gdy nikt inny nie pracuje w `apps/web` (konflikty). (4) Wyłącz z formatowania pliki wygenerowane i vendor (`src/lib/api/contract.generated.json`, `src/lib/api/generated`, `public/**`, `storybook-static`). (5) Dodaj `format:check` do etapu `web` (G11).

**Kryteria akceptacji.** `npm run format:check` zielone; po formatowaniu typecheck, lint, testy i bramka wizualna bez zmian.

### G13. Porządki

1. `apps/web/tsconfig.json`: `next dev` dopisuje wpisy `.next-e2e-<port>/…` w `include`; sprawdzaj `git diff apps/web/tsconfig.json` przed każdym commitem i cofaj te wpisy (docelowo: ustaw `distDir` poza `include` lub dodaj wzorzec w `exclude`, jak zrobiono dla `.next-*`).
2. Raporty wykonawców (`REPORT*.md` w `apps/web/src/features/*`, `apps/web/REPORT-API-ALIGN.md`, `scripts/pdf/REPORT.md`) przenieś do `docs/05-weryfikacja/gui/` jako dokumenty z nagłówkiem wersji, popraw ścieżki bezwzględne na względne i zaktualizuj odnośniki w tym pliku.
3. Trasa `/dev-pdf` nie powinna istnieć w buildzie produkcyjnym (patrz G03 pkt 3).
4. Usuń nieużywane pliki i zależności po G05–G08 (`npx knip` lub ręcznie), sprawdź rozmiar `public/`.

## 6. Do rozstrzygnięcia przez człowieka (agent nie rozstrzyga)

1. **Dostarczenie GUI:** czy GUI ma być dostarczane w pakiecie pip jako statyczny eksport (ADR-002 0.6.0, backlog nr 11), czy uruchamiane przez Node na prezentacji (ADR-002 0.8.0, wyjaśnienie użytkownika). Od tego zależy G03.
2. **Ciemne kolory statusów:** wartości dobrali niezależnie trzej projektanci makiet; zatwierdź jeden zestaw (propozycja z `work-d2`: Pełny `#1B3326`/`#8FD3A9`, Częściowy `#3A2D14`/`#E9C27A`, Błąd `#3D2223`/`#F0A0A2`, W toku `#17303A`/`#7CC3DB`, Niejednoznaczny `#2C2640`/`#BBA5E8`), potem ujednolić makiety i `tokens.css` (test kontrastu musi przejść).
3. **Pliki makiet:** trzy pliki uzupełniające w [figcraft/](../04-architektura/gui/figcraft/) zamiast jednego; scalenie wymaga ręcznej pracy w FigCraft.
4. **Luki wymagań z [przepływu urzędnika](../04-architektura/gui/user-flow-urzednik.md) §10:** UZP-05 (pip/CLI, dotyczy Z03), UZP-08 (licencja i lokalna instalacja modelu), UZP-11 (praca bez GPU).
5. **Python 3.13:** środowisko pracy agenta miało tylko 3.14 i 3.15; `apps/backend/pyproject.toml` deklaruje `>=3.11`, a wymaganie to 3.13+.
6. **Windows:** GUI ani skrypt `serve` nie były uruchamiane na Windows.

## 7. Zależności i kolejność

```text
Z01–Z03 (silnik, polityka eksportu, pip) ─┬─> G01 (OpenAPI) ─> G02 (klient HTTP) ─> prawdziwy przebieg end-to-end
                                           └─> G03 (statyczny eksport, po decyzji człowieka)
G10 (baza i bramka) ─> G05.1 ─> G04 ─> G09
G06, G07, G08: niezależne od siebie, po G10
G11, G12, G13: w dowolnej chwili; G12 gdy nikt nie pracuje w apps/web
```
