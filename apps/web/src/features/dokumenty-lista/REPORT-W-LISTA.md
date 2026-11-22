# W-LISTA — zamknięcie etapu

## ZROBIONE

Stan na 2026-11-22. Bez commita. Działający klient jest demonstracyjny: przyjmuje metadane PDF, nie przesyła zawartości dokumentów do silnika. Nie potwierdzano rzeczywistego OCR, modelu, licencji ani lokalizacji usług.

### Pliki

- `src/features/dokumenty-lista/DocumentsList.tsx`: rozbicie dużego widoku; obecnie 241 linii przed końcowym formatowaniem. `DocumentTable.tsx`, `QuickStatusFilters.tsx`, `viewStorage.ts`: tabela, szybkie filtry i stan URL/pamięci widoku.
- `src/features/dokumenty-lista/FilterBar.tsx`, `DocumentTile.tsx`, `filters.ts`: atomy Input/Select, biblioteczny kafelek, filtr partii i identyfikatorów dokumentów; zachowane dotychczasowe filtry i sortowanie.
- `src/features/dokumenty-lista/BatchBrowser.tsx`, `BatchBrowser.test.tsx`: partie, „Katalog główny”, grupy spraw, kody, ponawianie wyłącznie błędów, jawne ograniczenia E2.
- `src/features/dokumenty-lista/BatchExportView.tsx`, `BatchExportView.test.tsx`, `src/app/dokumenty/eksport/page.tsx`: `/dokumenty/eksport?partia=B-01`, plan 3/3, osobne JSON-y i raport pominięć.
- `src/features/dodawanie/AddDocumentsView.tsx`, `SelectedFilesPanel.tsx`, `RecentDocuments.tsx`, `useAddDocumentsState.ts`: małe widoki i kontroler, Card/Input/Select/Dialog, kontrola kolizji przed analizą.
- `src/features/dodawanie/BatchProgress.tsx`, `PipelineProgress.tsx`: biblioteczne ProgressBar/Stepper i tabela wyników; faktyczny model `getPipeline`, stany i liczniki zakończonych etapów.
- `src/features/dodawanie/SystemReadiness.tsx`, `ListaFlows.test.tsx`, `AddDocumentsView.test.tsx`: baner OCR, konfiguracja klas, kolizja, anulowanie i potok; istniejący test dodawania został też sformatowany.
- `src/features/pulpit/DashboardView.tsx`: Card i wspólny baner OCR; zachowany wymagany klucz API MiniMax, liczniki i dotychczasowe akcje.
- Nowe komponenty biblioteki: `src/components/molecules/DocumentResultTile.tsx`, `OcrReadinessBanner.tsx`, `src/components/organisms/DocumentResultsTable.tsx`; każdy ma własne `*.stories.tsx` i `*.test.tsx`. Domyślnych istniejących komponentów biblioteki nie zmieniano.
- `src/lib/api/schemas.ts`, `client.ts`, `hooks.ts`: dopisane kontrakty i hooki W-LISTA; `src/lib/api/mock/lista.ts`, `lista.test.ts`: cała nowa logika mocka; w `mock/client.ts` tylko import i wiersz integracji z dokumentami/historią.
- `e2e/wlista.spec.ts`: eksport i kolizja/potok, desktop + telefon, jasny + ciemny, axe i szerokość 320 px.
- `DropZone` był już komponentem biblioteki: pozostał używany bez kopiowania i bez modyfikacji. Nie edytowano `src/features/dokument/**`, istniejących atomów, tokenów, AppShell ani baz obrazów.

### Makieta → implementacja

Obejrzano wszystkie: F28, F42, F54, F07, F05, F57, F58, F65, F65d i pomocniczo F46.

| Makieta | Implementacja i odstępstwo |
| --- | --- |
| F28-partia-filtry.png | Sekcja „Partie i sprawy · E2” w `/dokumenty`, domyślnie zwinięta, otwarta dla `?partia=B-01`. Grupy „Katalog główny”, sprawa-a, sprawa-b, stany i kody. Zachowano nagłówek „Dodane dokumenty” i istniejącą galerię zamiast zastępować cały ekran samą tabelą spraw. ZIP prowadzi do działającego planu z oznaczeniem E2; dowody partii są wyłączone z komunikatem. |
| F42-eksport-czesciowy.png | 3 uwzględnione / 3 pominięte, ścieżki input → output, powody odmowy, „Pobierz 3 wyniki”, oddzielny raport. Nazwy pochodzą z syntetycznych dokumentów, nie z ilustracyjnych a.pdf–f.pdf. Pobierane są trzy osobne JSON-y; nie udajemy ZIP ani odtworzonego drzewa folderów. |
| F54-kolizja-sciezki.png | Dialog przed wysłaniem: nowa wersja / osobna paczka / anuluj. Bez zmiany nazwy na „(2)” i bez utraty starej historii. Nowa wersja dopisuje dokument oraz wynik do historii istniejącego identyfikatora; osobna paczka tworzy nowy rekord. Odstępstwo: przy wielu kolizjach jedna decyzja dotyczy całej listy; UI mówi to jawnie. Brak SHA w dialogu, ponieważ wybór plików przekazuje tylko metadane. |
| F07-wyniki-telefon.png | Widok `?widok=tabela` używa kart: nazwa/link, stan, strony/źródło, klasa, pola, wynik, Przejrzyj/Ponów. Galeria zachowuje dotychczasowe kafelki z miniaturami. |
| F05-analiza-w-toku.png | Postęp dokumentów + rozwijane etapy każdego dokumentu: E, L, T1…T5, Eksport. Stan, czas, kod błędu i liczniki wyłącznie po zakończeniu etapu. Zamiast jednej kolumny z bieżącym etapem pokazujemy pełną, rozwijaną listę Stepper. |
| F57-gotowosc.png / F58-ocr-shim.png | Baner z `getSystemInfo()` na `/dodaj` i pulpicie. Obsługuje unavailable/shim, ponowienie błędu odczytu i ładowanie. Nie deklaruje rzeczywistego OCR ani gotowości usługi. Podgląd dowodu F58 pozostaje w obszarze dokumentu. |
| F46-brak-konfiguracji.png | Istniejący `useClasses()` zwracający pustą listę blokuje analizę, pokazuje błąd i link `/klasy`. Jest to ten sam kontrakt scenariusza no-configuration W-KLASY; bez dublowania konfiguracji. |
| F65-pulpit.png / F65d-pulpit-ciemny.png | Zachowano strukturę działającego pulpitu, Card, klucz i rzeczywiste dane sesji, dodano OCR. Odstępstwa: osiem liczników zamiast sześciu, 12 rzeczywistych dokumentów zamiast ilustracyjnych 24, „Ostatnie dokumenty” zamiast projektowanej listy spraw. Pełna przebudowa pulpitu została odłożona przy zamknięciu etapu. |

### API

Dodano `listBatches`, `getBatchExportPlan(batchId)`, `checkPathCollision(files)` i pomocnicze `addResolvedDocuments({files, choice})`. Eksport zbiorczy w hooku ponownie wywołuje istniejące `exportJson` dla każdego dopuszczonego dokumentu. Plan używa wspólnego `evaluateExport`: niedozwolony null, awaria, niejednoznaczność i wiele dokumentów blokują JSON; tylko potwierdzony dokument obcy daje dokładnie `{}`. Awaria nigdy nie daje zastępczego `{}`.

B-01 to jawny scenariusz syntetyczny grupujący sześć istniejących rekordów; nie zmienia oryginalnych materiałów. Lista partii obejmuje też rzeczywiste identyfikatory partii sesji. Zapis jest w pamięci klienta demonstracyjnego. Raport pominięć jest osobnym pobraniem, poza output/.

### Kontrole — rzeczywiste wyniki

Port 3113 był zajęty przez obcą aplikację przekierowującą do `/pl/...`; własny serwer zwrócił EADDRINUSE. Tamten przebieg przerwano przez SIGINT wyłącznie własnego procesu Playwright. Koordynator przydzielił wolny port 3123; dalsze wyniki dotyczą właściwej aplikacji i `.next-e2e-3123`.

```text
npm run typecheck
> tsc --noEmit
exit 0  (/tmp/wlista-typecheck-last.log)

npm run lint
3 problems (0 errors, 3 warnings)
exit 0  (/tmp/wlista-lint-last.log)

npm test -- --maxWorkers=2 --testTimeout=15000
Test Files 106 passed (106)
Tests 821 passed (821)
Duration 444.89s
exit 0  (/tmp/wlista-test-final.log)

npx vitest run src/features/dokumenty-lista src/features/dodawanie src/features/pulpit src/lib/api/mock/lista.test.ts src/components/molecules/DocumentResultTile.test.tsx src/components/molecules/OcrReadinessBanner.test.tsx src/components/organisms/DocumentResultsTable.test.tsx --maxWorkers=2 --testTimeout=15000
Test Files 11 passed (11)
Tests 29 passed (29)
Duration 48.19s
exit 0  (/tmp/wlista-own-final.log)

npm run storybook -- --port 6113 --ci --smoke-test
Smoke tests passed, exiting.
exit 0  (/tmp/wlista-storybook-dev.log)

npm run build-storybook
Storybook build completed successfully
exit 0  (/tmp/wlista-storybook-final.log)

E2E_PORT=3123 npx playwright test e2e/wlista.spec.ts e2e/dodawanie.spec.ts e2e/dokumenty-lista.spec.ts e2e/pulpit.spec.ts --workers=2 --timeout=60000 --output=/tmp/wlista-out
28 passed (3.1m)
exit 0  (/tmp/wlista-e2e-final.log)

python3 scripts/verify_docs.py
OK: 440 materiałów, 66 dokumentów, odnośniki lokalne i integralność źródeł.
exit 0  (/tmp/wlista-docs-last.log)

git diff --check
exit 0
```

Limit czasu testów zwiększono przy współdzielonym obciążeniu środowiska; asercji, kontroli axe i progów obrazów nie osłabiano. Pierwsze przebiegi miały timeouty oraz przeładowania HMR podczas edycji. Naprawiono rzeczywisty brak linku nazwy w karcie telefonu i niejednoznaczny selektor testu grupy spraw; końcowy przebieg ma wszystkie testy zielone. Ostrzeżenia lint są w istniejących konfiguracjach i atomie Radio.

### Bramka wizualna

```text
E2E_PORT=3123 npx playwright test e2e/visual.spec.ts -g 'pulpit|dodaj|dokumenty-galeria|dokumenty-lista' --workers=2 --output=/tmp/wlista-out
16 failed
exit 1  (/tmp/wlista-visual.log)
```

Wszystkie 4 nazwy tras × 2 projekty × 2 motywy różnią się od starej bazy. To jawny wynik, nie zaliczony test. Bazy i próg pozostały bez zmian. Obejrzano wszystkie 16 obrazów `*-diff.png` w `/tmp/wlista-out/visual-visual-*/`.

Celowe różnice A: `/` i `/dodaj` — nowy baner OCR przesuwa dalszą zawartość; `/dokumenty` i wariant `dokumenty-lista` — nowa sekcja partii przesuwa kafelki. Telefon dodatkowo obejmuje nową mobilną powłokę rozwijaną równolegle w W-SYS, poza zakresem W-LISTA.

Dodatkowe porównanie surowych pikseli desktopowego obszaru x≥240, po odjęciu wyłącznie wysokości nowego bloku A: galerie i trasa nazwana lista mają po 0 pozostałych różniących się pikseli w obu motywach (wstawiony blok 98 px). Dla dodawania pozostało 9/11 pikseli, dla pulpitu 57/57 pikseli przy wstawionym bloku 124 px; są to drobne różnice rasteryzacji krawędzi, znacznie poniżej istniejącego progu 0.002. Nie jest to zastępcze zaliczenie pełnego `visual.spec.ts` ani osobny dowód parytetu telefonu.

Uwaga: istniejący test nazwany `dokumenty-lista` otwiera `?widok=lista`; parser produkcyjny przyjmuje `tabela`. Zatem ta nazwa w bramce obecnie ponownie sprawdza galerię. Prawdziwa tabela i telefoniczne karty są sprawdzane w E2E przez `?widok=tabela` oraz przełącznik „Lista”. Nie zmieniano cudzej konfiguracji bramki ani baz.

## DO ZROBIENIA

Poniższe zadania są odłożone zgodnie z poleceniem zamknięcia etapu. Nie pozostawiono eksperymentalnych tras, pustych linków ani testów skip/fixme. Obecne trasy działają jako demonstracja w opisanym zakresie.

### 1. Archiwa i foldery E2

**Cel:** rzeczywiste ZIP wyników i dowodów z zachowaniem drzewa; usunąć oznaczenie E2 dopiero po działającym pobraniu.

**Makiety:** `apps/web/design/F28-partia-filtry.png`, `F42-eksport-czesciowy.png`.

**Pliki:** `apps/web/src/features/dokumenty-lista/BatchBrowser.tsx`, `apps/web/src/features/dokumenty-lista/BatchExportView.tsx`, `apps/web/src/lib/api/{schemas.ts,client.ts,hooks.ts}`, `apps/web/src/lib/api/mock/lista.ts`, `apps/web/e2e/wlista.spec.ts`.

**Kroki:**

1. Uzgodnić endpointy `GET /batches`, `GET /batches/{id}/export-plan`, `POST /batches/{id}/exports` i osobny eksport dowodów; plan powinien identyfikować zapisane wersje, ścieżki i blokady.
2. Dopisać kontrakty i hooki na końcu API. Zachować `getBatchExportPlan` i centralną decyzję wariantu A; nie budować JSON w widoku.
3. Przygotować prawdziwe archiwum po stronie API, odrzucać niebezpieczne ścieżki, zachować output/sprawa/plik.json oraz osobne evidence/. Raport pominięć pozostaje osobno.
4. W Button/Banner/DataTable obsłużyć loading, pusty plan, błąd i sukces; przy 0 wynikach nie tworzyć pustego ZIP udającego powodzenie. Dopiero wtedy włączyć przycisk dowodów.
5. Dodać test zawartości i nazw plików ZIP oraz przejście desktop/phone w obu motywach z axe.

**Kryteria:** B-01 daje dokładnie 3 pliki wynikowe, pominięte 3 nie trafiają do output/; raport nie jest w ocenianym JSON; archiwum jest rzeczywiście ZIP; dozwolony obcy ma `{}`. Wszystkie własne testy i bramka przechodzą z opisanymi zmianami A.

**Weryfikacja:** `npm run typecheck`, `npm run lint`, `npx vitest run src/lib/api/mock/lista.test.ts src/features/dokumenty-lista`, `E2E_PORT=<wolny> npx playwright test e2e/wlista.spec.ts --workers=2 --output=/tmp/wlista-out`, `npm run build-storybook`.

**Pułapki/decyzje:** nie zmieniać rozszerzenia JSON na ZIP; nie pobierać blokowanych wyników; trzy osobne pliki to obecny, jawny wariant demonstracji. Zmiana stosu wymaga przeczytania architektury i decyzji.

**Zależności:** kontrakt backendu eksportu i rzeczywiste przesyłanie plików; wybór folderów należy uzgodnić z biblioteką DropZone.

### 2. Indywidualna decyzja dla każdej kolizji i wiarygodna tożsamość pliku

**Cel:** przy kilku kolizjach umożliwić różne decyzje dla różnych ścieżek, pokazać rzeczywiste skróty zamiast polegać wyłącznie na nazwie i rozmiarze.

**Makiety:** `apps/web/design/F54-kolizja-sciezki.png`.

**Pliki:** `apps/web/src/features/dodawanie/useAddDocumentsState.ts`, `apps/web/src/features/dodawanie/AddDocumentsView.tsx`, `apps/web/src/features/dodawanie/ListaFlows.test.tsx`, `apps/web/src/lib/api/mock/lista.ts`, `apps/web/src/components/molecules/DropZone.tsx`, API w `apps/web/src/lib/api/`.

**Kroki:**

1. Rozszerzyć `checkPathCollision` o stabilny indeks pliku, ścieżkę względną i opcjonalne rzeczywiste SHA; nie wymyślać skrótów w widoku. Rozszerzenie DropZone ma być opcjonalne, zachować jego domyślny wygląd.
2. Dodać typ `PathResolution {incomingIndex, choice}` oraz opcjonalną tablicę resolutions w `addResolvedDocuments` i hooku. Obecny choice pozostawić kompatybilny z istniejącymi testami.
3. W kontrolerze przechowywać indeks bieżącej kolizji i decyzje. Dialog biblioteczny pokazuje jedną ścieżkę naraz; mutację wywołać dopiero po rozstrzygnięciu wszystkich. Anulowanie zachowuje wybór bez częściowego zapisu.
4. Mock ma stosować decyzję per plik, zachować poprzednią historię i nie dopuszczać dwóch nowych wersji tej samej ścieżki w jednym zapisie. Obsłużyć błąd bez zamykania dialogu, loading i ponowienie.
5. Test: dwie kolizje, pierwsza „nowa wersja”, druga „osobna paczka”; poprzednie wyniki pozostają w historii, nazwy bez „(2)”, anulowanie drugiej nie zapisuje pierwszej.

**Kryteria:** różne decyzje dotyczą tylko wskazanych ścieżek; żaden istniejący dokument nie jest tracony; `ListaFlows.test.tsx` i `lista.test.ts` zawierają powyższy przypadek i przechodzą; E2E obu motywów/urządzeń bez serious/critical axe.

**Weryfikacja:** `npx vitest run src/features/dodawanie src/lib/api/mock/lista.test.ts --maxWorkers=2`, `E2E_PORT=<wolny> npx playwright test e2e/wlista.spec.ts --workers=2 --output=/tmp/wlista-out`, typecheck/lint/Storybook.

**Pułapki/decyzje:** obecny upload jest tylko metadanymi, nazwa+rozmiar nie dowodzą identycznej zawartości. Działająca obecna decyzja obejmuje całą listę kolizji; nie opisywać jej jako per ścieżka. Nie mylić wersji dokumentu z wersją wyniku. Klucz nadal wyłącznie w bezpiecznej konfiguracji API, bez localStorage.

**Zależności:** rzeczywisty kontrakt uploadu/wersjonowania; uzgodnienie opcjonalnych propsów wspólnego DropZone.

### 3. Pełne dopasowanie pulpitu i gotowości do F65/F65d

**Cel:** listy ostatnich spraw i gotowość zgodne z makietą, bez fikcyjnych danych i bez utraty istniejących stanów.

**Makiety:** `apps/web/design/F65-pulpit.png`, `F65d-pulpit-ciemny.png`, `F57-gotowosc.png`, `F58-ocr-shim.png`.

**Pliki:** `apps/web/src/features/pulpit/DashboardView.tsx`, `apps/web/src/features/pulpit/DashboardView.test.tsx`, `apps/web/src/features/dodawanie/SystemReadiness.tsx`, `apps/web/src/lib/api/mock/lista.ts`, `apps/web/e2e/pulpit.spec.ts`.

**Kroki:**

1. Rozszerzyć model partii o nazwę sprawy, datę i podsumowanie stanów. Pobierać przez `useBatches` lub rozszerzone `useDashboard`, nigdy przez fetch w widoku.
2. Wydzielić mały panel „Ostatnie sprawy” składany z Card i linków do `/dokumenty?partia=...`; obsłużyć loading/empty/error/success oraz retry.
3. Uzgodnić sześć kafelków z makiety z rzeczywistymi ośmioma stanami: nie gubić running ani multi; jeśli grupować, link musi filtrować wszystkie zgrupowane stany. Nie wpisywać na stałe liczby 24.
4. Integrując gotowość W-SYS, odróżnić metadane modelu od wyniku faktycznej kontroli. Sam configured/shim nie dowodzi dostępności API. Zachować ostrzeżenie o braku klucza MiniMax.
5. Przepisać testy pulpitu na nowe sprawy i liczniki, przetestować oba motywy i 320/768/1440 px, odnotować celową zmianę A w bramce.

**Kryteria:** panel pokazuje rzeczywiste partie i prowadzi do filtrowanych dokumentów; brak klas/klucza nie jest gotowością; błędy odczytu dają ponowienie; `DashboardView.test.tsx`, `pulpit.spec.ts` i axe przechodzą.

**Weryfikacja:** `npx vitest run src/features/pulpit`, `E2E_PORT=<wolny> npx playwright test e2e/pulpit.spec.ts --workers=2 --output=/tmp/wlista-out`, bramka `-g pulpit`, typecheck/lint/Storybook.

**Pułapki/decyzje:** obecny pulpit celowo zachowuje ostatnie dokumenty i osiem liczników z działającego ekranu. Gotowość modelu nie potwierdza licencji ani lokalizacji. Nie zmieniać tokenów ani domyślnych komponentów biblioteki.

**Zależności:** W-SYS (kontrakt gotowości) i metadane partii; aktywna konfiguracja klas W-KLASY jest już integrowana przez `useClasses`.

### 4. Rzeczywista trasa tabeli w istniejącej bramce

**Cel:** bramka o nazwie dokumenty-lista ma faktycznie weryfikować tabelę/karty, a nie ponownie galerię.

**Makiety:** `apps/web/design/F06-wyniki-lista.png`, `F07-wyniki-telefon.png`, `F28-partia-filtry.png`.

**Pliki:** `apps/web/e2e/visual.spec.ts`, `apps/web/src/features/dokumenty-lista/filters.ts`, `apps/web/src/features/dokumenty-lista/filters.test.ts`.

**Kroki:**

1. Koordynator wybiera zmianę adresu testu na `?widok=tabela` albo obsługę zgodnego aliasu lista w parserze. Nie zmieniać tolerancji obrazu.
2. Dodać test parsera i asercję widoku: na desktopie tabela, na telefonie karty bez miniaturek z F07.
3. Porównać ze starą bazą i udokumentować celową zmianę A (karty F07). Bazy pozostają poza Git; ich aktualizacja wymaga oddzielnej decyzji użytkownika, nie jest częścią tego raportu.
4. Po zakończeniu równoległych zmian powłoki oddzielnie sprawdzić telefon i 768 px. Zachować testy wyszukiwania, klas, statusów, kodów i powrotu z dokumentu.

**Kryteria:** nazwa dokumenty-lista odpowiada tabeli/kartom; żadna asercja nie sprawdza omyłkowo galerii; działają oba motywy i projekty; poza opisanymi zmianami A brak regresji przekraczających istniejący próg.

**Weryfikacja:** `npx vitest run src/features/dokumenty-lista`, `E2E_PORT=<wolny> npx playwright test e2e/visual.spec.ts -g 'dokumenty-galeria|dokumenty-lista' --workers=2 --output=/tmp/wlista-out` oraz `e2e/dokumenty-lista.spec.ts`.

**Pułapki/decyzje:** obecne 16 błędów obrazów jest jawnie opisane powyżej; nie przedstawiać ich jako zaliczonej bramki. Nie stosować `--update-snapshots` w kontynuacji bez nowego polecenia. Zmiany mobilnej powłoki należą do W-SYS.

**Zależności:** koordynator wspólnego `visual.spec.ts`, finalna powłoka W-SYS i decyzja o zaakceptowaniu obrazów nowych funkcji A.
