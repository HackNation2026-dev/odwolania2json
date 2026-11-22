# REPORT-W-DOC

## ZROBIONE

Zakres: przegląd dokumentu; bez commita. Przeczytano reguły apps/web/AGENTS.md, raport DS-B, README, wymagania, pytania otwarte, przepływy urzędnika i techniczne oraz projekt UI §3.3 i §9.1. Obejrzano F08, F09, F10, F13, F14, F16, F17, F18, F19, F23, F38, F39, F40, F41, F51, F52, F57, F58, F60 i F61.

### Pliki

- `src/features/dokument/DocumentView.tsx`: składanie widoku i wybór dowodu; wydzielono `DocumentHeader.tsx`, `DocumentTabs.tsx`, `DocumentFields.tsx`, `DocumentFooter.tsx`, `DocumentExportPolicy.tsx`.
- `DocumentPreview.tsx`: prawdziwy PdfViewer, sterowanie stroną i skalą, prawdziwe miniatury biblioteki, obrysy i powrót do pola.
- `DocumentPageText.tsx`: extractPageText, zapisany OCR przy braku warstwy tekstowej skanu, ładowanie, pusty tekst, błąd i ponowienie.
- `DocumentDiagnosis.tsx`: Drawer 400 px po prawej; pełna szerokość do 768 px; Dokument/Strona/Region, wybory strony i regionu, sygnały, kody, kopiowanie, zamknięcie i fokus.
- `DocumentOcrNotice.tsx`: OCR niedostępny, lista nieprzetworzonych stron, shim i rozwijane ograniczenia.
- `DocumentRegions.tsx`, `DocumentGeometryStyles.tsx`: powiązania pól i grup, kolor z tokenów, ID grupy i numer, wzór linii, aktywny obrys.
- `DocumentField.tsx`: FieldRow i Input z biblioteki, zachowana dotychczasowa edycja; `DocumentJson.tsx`: JsonViewer; `DocumentEvidence.tsx`: DataTable; `DocumentException.tsx`: Card; `DocumentProcessing.tsx`: czytelny JSX, diagnoza wydzielona do Drawer.
- `dokument.module.css`: zachowany układ dwóch paneli, lokalne style zgodności, tablet i telefon, odstęp nad dolnymi akcjami.
- Nowy wspólny organizm `src/components/organisms/DocumentEvidenceRegions.tsx` oraz jego stories/test: kilka obszarów, przechodzenie między stronami, Pola/Grupy, legenda, ostrzeżenie o kolizji i brak geometrii.
- `src/lib/api/mock/document-pdf.ts` i test: wybór demo-PDF oraz geometria z JSON obok PDF; `mock/data.ts`: tylko import i podmiana pola evidence na zlokalizowane dowody; wartości i pozostałe metadane dokumentów pozostawiono.
- Testy: `DocumentView.test.tsx`, `DocumentPageText.test.tsx`, `DocumentGeometryStyles.test.tsx`, `e2e/wdoc.spec.ts`; w `e2e/dokument.spec.ts` nazwa telefonicznej zakładki Dane.
- W `e2e/smoke.spec.ts` moja zmiana dotyczy wyłącznie filtrowania dokładnego komunikatu AbortException/TextLayer task cancelled, z odnośnikiem do scripts/pdf/REPORT.md. Pozostałe równoległe zmiany tego pliku należą do W-SYS; nie wycofywano ich.

Ścieżki skrócone wyżej są względem `apps/web` lub `apps/web/src/features/dokument`. Plików oryginalnych organizatora, istniejących komponentów biblioteki, tokenów, progów i baz wizualnych nie zmieniano.

### Makieta → implementacja

| Makiety | Implementacja i odstępstwa |
|---|---|
| F09 | Prawdziwy PDF i obrysy zamiast CSS-owej kartki. Strona pozostaje biała w dark. Zasób jest jawnie demonstracyjny, nie jest oryginalnym dokumentem. |
| F16 | Dwa panele przy 1024 px; przycisk miniatur ukryty. Podgląd ma własny scroll i dopasowanie szerokości. |
| F17 | Przy 768 px przejście na zakładki Dokument/Formularz/JSON/Dowody; dodatkowo zachowany Eksport. |
| F18/F19 | Na telefonie Dokument/Dane/JSON; Dowody i Eksport w Więcej widoków. Dodany powrót do wybranego pola i odstęp nad dolnym paskiem. |
| F23 | Drawer po prawej 400 px i pełna szerokość na małym ekranie; trzy poziomy, sygnały i kody. Brak typu strony/jakości w kontrakcie jest jawny, bez wymyślania wartości. Nie ma rozdzielonych wartości orientacji oryginalnej i korekty. |
| F38/F39 | Legenda, Pola/Grupy, ID, kolory i wzory linii oraz następny obszar; kolizja daje osobne ramki i ostrzeżenie. Nie tworzono sztucznej jednej obwiedni. Seed nie zawiera przypadku kilku dowodów jednego pola; stan jest sprawdzony testem organizmu. |
| F13/F14/F40/F41 | Zachowano obcy/błąd/niejednoznaczny/wiele dokumentów, brak fikcyjnego wyniku; klasy i ponowienie z hooków. Nie dopisano nieprzekazanych granic segmentów ani sygnałów kandydatów. |
| F51/F52 | Pięć przyczyn braków pozostaje osobno. Tekst strony pochodzi z extractPageText; dla skanu używa zapisanego OCR. Brak geometrii jest opisany. |
| F57/F58 | Skrót OCR niedostępny i lista stron są widoczne; szczegóły rozwijane. Shim jest oznaczony w UI i metadanych pobieranych dowodów. Metadane OCR są obecną konfiguracją mocka; kontrakt nie przechowuje pełnej historycznej konfiguracji odczytu. |
| F60/F61 | Dowody i raport osobno; eksport i kopiowanie blokuje decyzja wariantu A. Tylko potwierdzony obcy eksportuje dokładnie {}. Wariant B pozostaje opisem odrzuconej polityki, bez aktywnego pobierania. |
| F08/F10 | FieldRow i JsonViewer zastępują ręczny kod. JsonViewer ma własny układ kontrolek i brak numerów linii starego JSON; dokładna zgodność wizualna tej zakładki wymaga dalszego dopracowania. |

Demo-PDF jest krótszy od pełnego mocka: daty, PESEL, rachunki, kwota przelewu i część opisów nie występują w dostarczonym demo. Dla takich pól usunięto fikcyjne box/bbox/words; nadal istnieje cytat zapisany przez mock i jawny brak dokładnej lokalizacji. Odwołanie ma trzy strony, skan jedną; rekord doc-4 opisuje trzy — podgląd pokazuje ostrzeżenie i rzeczywistą liczbę stron zasobu. Dla obcego, awarii i dokumentu wielokrotnego pokazany jest najbliższy demonstracyjny PDF, zgodnie z zakresem zadania.

### Kontrole

Ostatnie ukończone wyniki (logi w /tmp; poniższe nie są deklaracją jeszcze trwających przebiegów):

```text
npm run typecheck
tsc --noEmit
exit 0 (/tmp/wdoc-typecheck-final.log)

npm run lint
3 problems (0 errors, 3 warnings)
exit 0 (/tmp/wdoc-lint-final.log)

npx vitest run <6 plików W-DOC> --maxWorkers=2
Test Files 6 passed (6)
Tests 34 passed (34)
Duration 20.50s
exit 0 (/tmp/wdoc-unit-final.log)

npm run build-storybook
Storybook build completed successfully
exit 0 (/tmp/wdoc-storybook-final.log)

python3 scripts/verify_docs.py
OK: 440 materiałów, 62 dokumentów, odnośniki lokalne i integralność źródeł.
exit 0 (/tmp/wdoc-docs.log)

git diff --check -- <pliki W-DOC>
exit 0
```

Pierwszy pełny npm test pod współdzielonym obciążeniem przekroczył 5 s w kilku plikach, również dwóch testach W-DOC; przerwano wyłącznie własny proces PID 885901. Ponowiono pełny zestaw jako npm test -- --maxWorkers=2 --testTimeout=15000: 107 plików / 825 testów zaliczonych, exit 0, 325.98 s; log /tmp/wdoc-tests-limited.log. Nie zmieniano asercji ani konfiguracji repozytorium.

Pierwsza bramka `E2E_PORT=3111 npx playwright test e2e/visual.spec.ts -g 'doc-|nie-znaleziono' --workers=2 --output=/tmp/wdoc-out`: **30 failed / 2 passed**. Obejrzano zrzuty diff dla doc-full i doc-ocr oraz bazę i actual doc-full. To wcześniejszy przebieg przed lokalnymi stylami zgodności; nie jest dowodem końcowej parytetowości. Celowe różnice A: prawdziwa treść i sterowanie PDF, geometria/cytaty, ostrzeżenia OCR, Drawer, telefoniczne zakładki. Baza i próg pozostają bez zmian. Zrzuty i końcowy przebieg opisane będą po jego ukończeniu.

Pełny przebieg wybranych testów dokument/wdoc: 73 passed / 7 failed (8.2m); końcowe ponowienie błędów opisano poniżej.

Pierwsze e2e wdoc: 4 passed / 4 failed z powodu selektora trafiającego w ukrytą miniaturę canvas; selektor poprawiono na canvas konkretnej strony. Kolejny wspólny przebieg e2e dokument/wdoc ujawnił zbyt wysoki baner OCR przy 1280×720 oraz zbyt szeroki selektor tekstu w ukrytej zakładce Drawer; poprawiono układ i zawężono selektor do aktywnego tabpanelu, bez usuwania asercji.

### Końcowe poprawki zamknięcia etapu

- Naprawiono przechwytywanie kliknięć na telefonie przez powiększone pseudocele i etykiety sąsiednich obrysów; lista obszarów pod PDF udostępnia osobne przyciski co najmniej 44 px. Geometria prostokątów pozostała bez zmiany.
- Kompaktowy skrót OCR nie wypycha pierwszego pola przy 1280×720; szczegóły pozostają dostępne po rozwinięciu.
- E2E dodatkowo sprawdza białą stronę PDF w obu motywach oraz kontrast obrysu co najmniej 3:1.

### Wyniki końcowe po poprawkach

```text
(npm run typecheck && npm run lint)
exit 0; 0 errors, 3 warnings
/tmp/wdoc-final-code-checks.log

npm test -- --maxWorkers=2 --testTimeout=15000
Test Files 107 passed (107)
Tests 825 passed (825)
Duration 325.98s
exit 0; /tmp/wdoc-tests-limited.log

npx vitest run <6 plików W-DOC> --maxWorkers=2
Test Files 6 passed (6)
Tests 34 passed (34)
Duration 2.82s
exit 0; /tmp/wdoc-unit-final.log

npm run build-storybook
Storybook build completed successfully
exit 0; /tmp/wdoc-storybook-final.log

python3 scripts/verify_docs.py
OK: 440 materiałów, 65 dokumentów, odnośniki lokalne i integralność źródeł.
exit 0; /tmp/wdoc-docs-final.log

E2E_PORT=3111 npx playwright test e2e/wdoc.spec.ts e2e/visual.spec.ts -g 'synchronizes real PDF|keeps OCR|visual doc-|visual nie-znaleziono' --workers=2 --output=/tmp/wdoc-out
30 failed / 10 passed (2.0m)
exit 1; /tmp/wdoc-final-e2e-visual.log
```

W ostatniej komendzie **wszystkie 8/8 testów e2e/wdoc.spec.ts przeszło** (desktop + phone × jasny/ciemny × dwa przepływy), z rzeczywistym canvas/tekstem, wyborem obrysu, powrotem do pola, diagnozą, eksportem, 320 px, axe, białą stroną i kontrastem obrysu. Świeże ponowienie telefonicznych przejść po ustabilizowaniu CSS: 2/2 passed (4.2s), jasny 2.7s i ciemny 2.8s, exit 0; /tmp/wdoc-phone-final.log. Pozostałe dwa zaliczenia w komendzie 40 testów to desktopowe 404 w obu motywach. Wszystkie 30 niepowodzeń to porównania obrazów.

Istniejące e2e/dokument.spec.ts: z szerokiego przebiegu 80 testów zaliczono 73; naprawione przypadki 1280×720 doc-3/doc-4 przeszły następnie na obu projektach (4/4 w /tmp/wdoc-recheck.log). Dwa pozostałe problemy dotyczyły nowych selektorów wdoc i klikania linku powrotu zasłoniętego dolnym paskiem; końcowy przebieg 8/8 potwierdza poprawki. Nie uruchamiano ponownie całych 80 testów po poprawkach. Pominęto tylko osobny blok „visual review ... all tabs”, który zapisuje pomocnicze zrzuty dla wszystkich 12 rekordów; właściwą bramkę uruchomiono osobno bez zmiany progu i bazy.

**Bramka nie jest zielona i refaktor B nie ma dowodu 0 różnic.** Obejrzano końcowe diff dla wszystkich siedmiu klas tras desktop/light, full i OCR desktop/dark oraz full, partial i 404 phone/light; obejrzano również actual full. Klasyfikacja:
- doc-full: zamiana atrapy, skala i legenda PDF; cytat BZP/TED zgodny z rzeczywistym PDF; dodatkowo niewyrównane jeszcze drobne odstępy FieldRow — to zaległość B z instrukcji nr 1, a nie celowa zmiana A.
- doc-partial i doc-ocr: jak wyżej, dodatkowo jawny skrót OCR, lista nieprzetworzonych stron i ostrzeżenie o liczbie stron demo. To przesuwa formularz zgodnie z dodaniem stanu A.
- doc-ambiguous/doc-error/doc-multi: PDF demo, jawna różnica liczby stron i wejście do nowego Drawer zamiast dawnego rozwinięcia diagnozy. Istniejące banery i akcje zachowane.
- doc-foreign: prawdziwy demonstracyjny PDF; decyzja i {} pozostają takie same.
- phone dla dokumentów: nowe zakładki i Więcej widoków (A), domknięcie odstępu dolnego, zmiana powłoki W-SYS (menu i nagłówek) oraz zaległe odstępy FieldRow (B).
- nie-znaleziono: desktop 0 różnic; oba phone różnią się w powłoce W-SYS. W-DOC zachował istniejący widok 404.
- Bramka wykonuje screenshot po stałym czasie 1200 ms. Niektóre actual przechwytują pierwszy, jeszcze niegotowy canvas PDF; e2e funkcjonalne czeka na konkretny canvas i tekst, dlatego weryfikuje rzeczywisty gotowy render. Nie zmieniano wspólnego visual.spec.ts, progu ani baz; dodanie warunku gotowości PDF do bramki wymaga uzgodnienia z koordynatorem.

### Poprawka po odbiorze — task_7906b586eebe

Zakres tej poprawki obejmuje wyłącznie eksport po korekcie i aktualizację e2e diagnozy; wcześniejsze zaległości wizualne opisane niżej nie są jej częścią. Nie wykonano commita.

**Przyczyna pobierania:** po kliknięciu Zapisz mock zapisuje wartość i unieważnia zapytania. Ostatnia decyzja eksportu już była dozwolona, więc oczekiwanie testu na aktywny przycisk mogło zakończyć się przed odświeżaniem. Flaga isFetching następnie wyłączała przycisk w trakcie kliknięcia myszy; Playwright kończył click, ale handler pobrania nie musiał zostać wywołany. Dodatkowo stopka posiadała drugi obserwator decyzji, a handler rodzica potrafił cicho odrzucić przyjęte kliknięcie, gdy widział odświeżanie. Samo usunięcie guard i drugiego obserwatora nie wystarczyło: powtórzenia nadal wykazały niepowodzenia, dopóki odświeżanie przełączało disabled.

**Naprawa kodu:**
- `src/features/dokument/DocumentFooter.tsx` otrzymuje tę samą decyzję co DocumentView; nie tworzy osobnego useExportDecision.
- Dozwolony eksport pozostaje aktywny podczas odświeżania; nadal jest zablokowany bez dozwolonej decyzji i podczas samego pobierania.
- `DocumentView.tsx` realizuje przyjęte kliknięcie przez useExportJson, bez cichego return dla isFetching. API exportJson nadal ponownie wywołuje evaluateExport i odrzuca wynik niezgodny z wariantem A; nie omija się walidacji ani nie tworzy zastępczego {}.
- `DocumentExportRace.test.tsx` odtwarza przyjęte kliknięcie przy odświeżaniu rodzica i sprawdza utworzenie pobrania; drugi test wymusza przestarzałą kontrolkę dla błędu technicznego i potwierdza odmowę API bez kliknięcia linku pliku.
- `DocumentFooter.test.tsx` sprawdza aktywność dozwolonego przycisku przez przejście do stanu odświeżania.
- `e2e/api-align.spec.ts` otwiera Drawer, weryfikuje dialog, wybiera Strona → 2 oraz Region → R3 i sprawdza OCR, kod zla_warstwa_ocr i sygnał niezgodnej warstwy. Asercje stanów przebiegu w toku/oczekuje pozostają; zaktualizowano ścieżkę do zamierzonego interfejsu, bez osłabienia kontroli.
- `e2e/dokument.spec.ts` w tej poprawce nie zmieniono; test dalej wymaga rzeczywistego pobrania i sprawdza poprawioną datę w pobranym JSON.

**Dowód diagnozy i regresji:**
```text
Przed poprawką:
E2E_PORT=3111 npx playwright test e2e/dokument.spec.ts --project=desktop -g 'corrects a nullable' --repeat-each=5 --workers=2
1 failed / 4 passed (33.4s)
/tmp/wdoc-fix-repro.log

Test regresji przed naprawą:
npx vitest run src/features/dokument/DocumentExportRace.test.tsx
1 failed; eksport API nie został wywołany
/tmp/wdoc-fix-race-red.log

Po pełnej poprawce:
E2E_PORT=3111 npx playwright test e2e/dokument.spec.ts --project=desktop -g 'corrects a nullable' --repeat-each=10 --workers=2
10 passed (16.8s)
/tmp/wdoc-fix-repeat2.log

npx vitest run src/features/dokument/DocumentFooter.test.tsx src/features/dokument/DocumentExportRace.test.tsx src/features/dokument/DocumentView.test.tsx
3 files / 21 tests passed (2.50s)
/tmp/wdoc-fix-race-green.log
```

Port 3111 sprawdzono przez ss przed uruchomieniem; był wolny. Poprawka nie wymaga zmiany Blob/anchor ani dłuższego oczekiwania na download; nie zastosowano force, retry ani zmian limitów e2e.

**Końcowe wyniki poprawki po odbiorze:**

```text
npm run typecheck && npm run lint
tsc --noEmit
3 problems (0 errors, 3 warnings)
exit 0; /tmp/wdoc-fix-code-final.log

npm test -- --maxWorkers=2
Test Files 109 passed (109)
Tests 830 passed (830)
Duration 57.52s
exit 0; /tmp/wdoc-fix-tests-final.log

npm run build-storybook
Storybook build completed successfully
exit 0; /tmp/wdoc-fix-storybook-final.log

E2E_PORT=3111 npx playwright test e2e/dokument.spec.ts e2e/api-align.spec.ts e2e/wdoc.spec.ts --workers=2 --output=/tmp/wdoc-fix-out
132 passed (3.2m)
exit 0; /tmp/wdoc-fix-e2e.log

E2E_PORT=3111 npx playwright test e2e/dokument.spec.ts --project=desktop -g 'corrects a nullable' --repeat-each=3 --workers=1
3 passed (9.2s)
exit 0; /tmp/wdoc-fix-single.log

git diff --check -- <pliki poprawki W-DOC>
exit 0
```

Pełny przebieg obejmuje desktop i phone, oba motywy, axe, zapisy pól z rzeczywistym pobraniem oraz wszystkie pomocnicze przeglądy zakładek; nie użyto grep-invert, skip, retry ani zmian timeoutów. Test diagnozy nadal weryfikuje stany przebiegu oraz stronę i region OCR, korzystając z nowego Drawer. Nie zmieniono progów/baz wizualnych.

Dodatkowo wykonane python3 scripts/verify_docs.py zwróciło exit 1 z powodu niezależnych, nieistniejących odnośników w docs/00-organizacja/zadania-gui.md do zadania-dla-agentow.md, backlog.md, recenzji fable-ocena-architektury.md oraz ADR-003-lokalne-ci-cd.md. Tej dokumentacji nie zmieniano; wymaga sprawdzenia przez koordynatora poza zakresem naprawy eksportu. Wszystkie kontrole wymagane w zleceniu poprawki są zaliczone; wcześniejsza zaległość parytetu wizualnego pozostaje opisana w osobnych instrukcjach poniżej.

## DO ZROBIENIA

### 1. Zgodność wizualna refaktoru danych i JSON

**Cel:** doprowadzić refaktor B do identycznego wyglądu poza zaakceptowanymi nowymi elementami A.

**Makiety:** apps/web/design/F08-przeglad.png, F10-json.png, F16-uklad-posredni.png, F17-tablet.png, F18-telefon.png, F60-dowody.png.

**Pliki:** apps/web/src/features/dokument/{DocumentField.tsx,DocumentJson.tsx,DocumentEvidence.tsx,dokument.module.css}; ewentualne nowe komponenty w apps/web/src/components/molecules.

**Kroki:**
1. Odczytać bazę e2e/visual.spec.ts-snapshots, raport i aktualne diff/actual; oddzielić treść podglądu PDF i nowe ostrzeżenia A od zmian istniejących kontrolek.
2. Dopracować lokalny wariant FieldRow tak, aby stare wyrównania, odstępy i wysokości były identyczne. Nie zmieniać domyślnego wariantu biblioteki.
3. Dodać do CodeBlock/JsonViewer opcjonalne numery linii i wariant zgodny ze starym układem JSON; nowe propsy muszą mieć stories i test. Uzgodnić edycję istniejącego komponentu z właścicielem DS.
4. Porównać tabelę i karty dowodów z F60 oraz zachować wariant A, blokadę kopiowania i brak zastępczego JSON.
5. Ponowić wskazaną bramkę; obejrzeć każdy typ różnicy.

**Kryteria akceptacji:** 0 różnic dla samego refaktoru B; wszystkie różnice A opisane konkretnie; jednostkowe W-DOC i axe nadal zielone.

**Weryfikacja:** cd apps/web; npm run typecheck; npm run lint; npx vitest run src/features/dokument/DocumentView.test.tsx; E2E_PORT=3111 npx playwright test e2e/visual.spec.ts -g 'doc-|nie-znaleziono' --workers=2 --output=/tmp/wdoc-next-out.

**Pułapki/decyzje:** zakaz aktualizacji bazy i progu; biała strona PDF w dark; nie odtwarzać atrapy PDF; shell może być jednocześnie zmieniany przez W-SYS.

**Zależności:** stabilna wersja powłoki W-SYS i uzgodnienie zmian biblioteki DS.

### 2. Pełne, spójne fixture PDF i dowodów

**Cel:** usunąć różnice między pełnymi wartościami kontraktu mocka a skróconymi źródłami demo i udostępnić reprodukowalny przykład F38/F39.

**Makiety:** apps/web/design/F09-dowod-geometryczny.png, F38-wiele-obrysow.png, F39-kolizja-grup.png, F51-wyjatek.png, F52-wyjatek.png.

**Pliki:** apps/web/scripts/pdf/generate-demo-pdfs.ts; apps/web/public/demo-pdf/*; apps/web/src/lib/api/mock/{document-pdf.ts,document-pdf.test.ts,data.ts}; apps/web/src/features/dokument/{DocumentPreview.tsx,DocumentRegions.tsx}.

**Kroki:**
1. Rozszerzyć wyłącznie syntetyczny generator o istniejące dane appealResult/powerResult/transferResult, bez zmiany kontraktu i oryginałów organizatora.
2. Wygenerować zgodne PDF oraz geometrię; skan powinien mieć tyle stron, ile wskazuje świadomie wybrany rekord demonstracyjny.
3. Dodać kilka obszarów jednego pola na różnych stronach oraz osobny przypadek przecięcia grup. Powiązać evidenceIds, box/bbox i cytaty bez sztucznej dużej obwiedni.
4. W razie wielu prostokątów jednego dowodu zdefiniować jednoznaczny kontrakt ich stron; obecny box opisuje jedną stronę i jeden obszar.
5. Dodać e2e przejścia Następny obszar przez strony, kolizji, numerów i kolorów oraz braku geometrii.

**Kryteria akceptacji:** pdf:verify przechodzi; każdy obrys trafia w swój cytat (<2 px jak e2e/pdf-viewer.spec.ts); kwota 200.00 i PESEL 85120133547 mają prawdziwe źródło; F38/F39 można odtworzyć na trasie bez manipulowania DOM.

**Weryfikacja:** npm run pdf:demo; npm run pdf:verify; npx vitest run src/lib/api/mock/document-pdf.test.ts; E2E_PORT=3111 npx playwright test e2e/wdoc.spec.ts --workers=2 --output=/tmp/wdoc-next-out.

**Pułapki/decyzje:** obecnie brak box jest uczciwszy niż ramka na innym tekście. Nie dopasowywać daty/kwoty do niezgodnego fragmentu. Nie zmieniać metadanych i wyników innych obszarów bez uzgodnienia.

**Zależności:** zgoda na rozszerzenie zakresu scripts/pdf/public oraz właściciel kontraktu API.

### 3. Źródłowy PDF i historyczne OCR z API

**Cel:** zastąpić mapowanie klas na zasoby demo autoryzowanym źródłem dokumentu i historycznym pochodzeniem odczytu.

**Makiety:** apps/web/design/F23-diagnoza.png, F52-wyjatek.png, F57-gotowosc.png, F58-ocr-shim.png, F60-dowody.png.

**Pliki:** apps/web/src/lib/api/{schemas.ts,client.ts,hooks.ts}; nowy mock apps/web/src/lib/api/mock/dokument.ts; apps/web/src/features/dokument/{DocumentPreview.tsx,DocumentPageText.tsx,DocumentDiagnosis.tsx,DocumentOcrNotice.tsx,DocumentView.tsx}.

**Kroki:**
1. Uzgodnić getDocumentSource(id) i hook useDocumentSource: bezpieczny PDF URL/pochodna, rzeczywista liczba stron, rewizja dokumentu i informacja o dostępności. Nowe definicje dopisywać zgodnie z regułami współpracy API; nie wywoływać fetch w widoku.
2. Przechować przy wyniku źródło tekstu każdej strony i regionu, OCR mode/name/version, jakość, orientację oryginalną i korektę oraz processed/unprocessed, zamiast odczytywać aktualną konfigurację jako historyczną.
3. Obsłużyć ładowanie/brak/błąd/odmowę źródła PDF i odczytu; brak PDF nie może przywrócić poprzedniego dokumentu.
4. Zasilić Drawer nowymi polami; Nie przekazano/Nie oceniono pozostawić dla danych nieobecnych.
5. Pobierane dowody i raport powiązać z documentVersion/resultVersion i historycznym OCR. Oceniany JSON pozostaje bez tych metadanych.

**Kryteria akceptacji:** komponenty używają tylko hooków API; zmiana bieżącego OCR nie zmienia etykiety zapisanego dowodu; odmowa nie wysyła oryginału PDF; wszystkie stany mają testy.

**Weryfikacja:** npm run typecheck; npm run lint; npm test -- --maxWorkers=2; E2E_PORT=3111 npx playwright test e2e/wdoc.spec.ts --workers=2 --output=/tmp/wdoc-next-out.

**Pułapki/decyzje:** nie ma backendu; nie sugerować autoryzacji przez CSS. Tekst skanu pochodzi z zapisanego OCR, nigdy z extractPageText pustego obrazu. Wyjątek TextLayer filtrować wyłącznie dokładnym komunikatem w testach.

**Zależności:** backend/kontrakt PDF i historycznej diagnozy; współpraca W-SYS przy gotowości.

### 4. Szkic edycji i historia — oddzielnie zlecony kolejny etap

**Cel:** zastąpić dotychczasowy natychmiastowy zapis pola pełnym szkicem, bez ingerowania w działający podgląd dowodu.

**Makiety:** apps/web/design/F11-walidacja-korekty.png, F24-historia.png, F33-niezapisany-szkic.png, F34-blad-zapisu.png, F53-zapisywanie.png.

**Pliki:** apps/web/src/features/dokument/{DocumentField.tsx,DocumentFields.tsx,DocumentView.tsx,DocumentProcessing.tsx,DocumentFooter.tsx} oraz API właściwe dla zapisu wersji.

**Kroki:**
1. Przejąć akcję onEdit FieldRow w DocumentField i podnieść stan szkicu do DocumentView, tak aby zmiana zakładki i breakpointu go zachowywała.
2. Wypełnić miejsce data-document-draft-slot paskiem szkicu i akcjami zapisu/anulowania; aktualna implementacja zachowuje starszy useUpdateField i nie udaje szkicu.
3. Zastąpić blok historii w DocumentProcessing osobnym małym komponentem; użyć Dialog, Banner, Select i hooków useVersions/useRestoreVersion.
4. Dodać walidację, zachowanie szkicu po awarii, blokadę wyjścia i zapis nowej wersji z odświeżeniem decyzji eksportu.

**Kryteria akceptacji:** błąd nie gubi wpisanej wartości; zapis tworzy nową wersję; zmiana zakładki nie usuwa szkicu; JSON i eksport dotyczą jawnie zapisanej wersji; istniejące e2e pól i dowodów nadal przechodzą.

**Weryfikacja:** testy szkicu i historii; npm run typecheck; npm run lint; npm test -- --maxWorkers=2; E2E_PORT=3111 npx playwright test e2e/dokument.spec.ts e2e/wdoc.spec.ts --workers=2 --output=/tmp/wdoc-next-out.

**Pułapki/decyzje:** obecne data-document-draft-slot jest niewidocznym punktem integracji, a nie gotową funkcją; wymaganie szkicu świadomie odroczono w zleceniu W-DOC.

**Zależności:** osobny wykonawca edycji i wersjonowania.


### 5. Stabilne oczekiwanie na gotowy PDF w bramce

**Cel:** porównywać gotowy render, bez przypadkowego przechwytywania startowego canvas o rozmiarze domyślnym.

**Makiety:** apps/web/design/F09-dowod-geometryczny.png, F16-uklad-posredni.png, F52-wyjatek.png.

**Pliki:** apps/web/e2e/visual.spec.ts; apps/web/src/features/dokument/DocumentPreview.tsx; ewentualnie apps/web/src/components/organisms/pdf/PdfViewerClient.tsx po uzgodnieniu właściciela DS.

**Kroki:**
1. Uzgodnić ze wszystkimi właścicielami wspólnego visual.spec.ts zmianę wyłącznie oczekiwania na gotowość, bez zmiany bazy/progu.
2. Dla widocznego PDF czekać na canvas konkretnej strony o rzeczywistych wymiarach i zakończony render/warstwę tekstową; skan musi używać gotowości canvas, bo nie ma tekstu.
3. Dla ukrytego podglądu na telefonie nie czekać na niewidoczny canvas.
4. Rozważyć opcjonalny onPageRenderSuccess/data-ready w PdfViewer, z tests/stories i zachowaniem domyślnego API.
5. Uruchomić bramkę ponownie i rozdzielić oczekiwane różnice treści PDF od zaległości B z instrukcji nr 1.

**Kryteria akceptacji:** kolejne przebiegi dają ten sam gotowy render; screenshot nie zawiera białych startowych canvas 300×150; żaden test nie używa większej tolerancji lub aktualizacji bazy.

**Weryfikacja:** E2E_PORT=3111 npx playwright test e2e/visual.spec.ts -g 'doc-|nie-znaleziono' --workers=2 --output=/tmp/wdoc-next-out; E2E_PORT=3111 npx playwright test e2e/wdoc.spec.ts --workers=2 --output=/tmp/wdoc-next-flow-out.

**Pułapki/decyzje:** onLoadSuccess dokumentu nie jest tym samym co gotowy canvas strony; nie rozwiązywać problemu arbitralnym długim sleep.

**Zależności:** koordynator wspólnego visual.spec.ts i właściciel PdfViewer.
