# PDF-SPIKE — raport implementacji

Wybrane rozwiązanie: `react-web-pdf-editor` **0.1.6**, zgodnie z ADR-002. Wersja rozwiązuje `pdfjs-dist` **5.7.284**. Jest to prawdziwy podgląd źródłowego PDF, z canvas, warstwą tekstową i oddzielną warstwą dowodów.

## Uzasadnienie i geometria

W `node_modules/react-web-pdf-editor/dist/index.js` komponent `PdfPage` tworzy względny element `.rpe-page[data-page-number]` i umieszcza w nim canvas oraz `.textLayer`. Adapter w `src/components/organisms/pdf/editorDom.ts` izoluje wyszukiwanie tych stron. Ramki są portalami React do tych elementów: procentowe położenie dziedziczy rzeczywisty rozmiar strony przy zoomie, przewijaniu i zmianie szerokości. MutationObserver śledzi podmianę elementów, ResizeObserver zmianę kontenera. Kontrola adaptera jest w teście jednostkowym; geometrię rzeczywistego renderu sprawdza Playwright.

Biblioteka pozostaje z domyślnym narzędziem `select`. Własny pasek udostępnia strony, zoom, dopasowanie, wyszukiwanie, miniatury i tekst. Narzędzia modyfikacji, eksport i operacje dodawania/usuwania/przestawiania stron są niedostępne. `drop`/`dragover` są blokowane w fazie capture, ponieważ edytor dodaje upuszczone obrazy także w trybie `select`. Własne miniatury korzystają z `SidebarApi.pdf`, ale trafiają portalem do osobnego kontenera; natywny mobilny drawer i przycisk edytora są ukryte.

Aktywna ramka ma 2 px `--evidence-border`, wypełnienie `--evidence-bg` o kryciu 55%, numer, etykietę i stan `aria-pressed`. Cel dotykowy jest powiększony pseudoelementem bez zmiany bbox obrysu. Zmiana aktywnego dowodu wywołuje kontrolowaną zmianę strony. PageUp/PageDown i strzałki zmieniają strony; fokus ma obrys z tokena. Po błędzie otwarcia kolejnego pliku wrapper chowa poprzedni PDF i pokazuje polski alert (sam edytor potrafi zachować poprzedni podgląd i ukryć swój błąd).

## API

`PdfViewer` przyjmuje `file: PdfSource | string`, opcjonalne `page`, `onPageChange`, `scale`, `onScaleChange`, `highlights`, `onHighlightClick`, `onLoadSuccess({numPages})`, `onLoadError(Error)`, `emptyState`, `className`.

`PdfHighlight = { id, page, box: {x,y,w,h}, label?, active? }`; strony są numerowane od 1, geometria od górnego lewego rogu w ułamkach 0..1. `extractPageText(file, page): Promise<string>` jest eksportowany z modułu komponentu; czyta `getTextContent`, zwalnia dokument i daje pusty tekst dla skanu. Zakładka tekstowa rozróżnia dokument i numer strony, więc nie pokazuje tekstu poprzedniej strony podczas nowego odczytu.

Klient jest ładowany przez `next/dynamic` z `ssr:false`. `pdfAsset()` uwzględnia wbudowany prefiks Next `__NEXT_ROUTER_BASEPATH`; worker ma ścieżkę `/pdf/pdf.worker.min.mjs` z tym prefiksem. Osobnego eksportu statycznego z niepustym basePath nie uruchomiono.

## Generowanie i zasoby

- `npm run pdf:assets` / `postinstall`: ustala PDF.js przez resolver zależności edytora, kopiuje zgodny worker, licencje i zapisuje wersję.
- `npm run pdf:demo`: generator TypeScript z `@react-pdf/renderer` **4.9.0** (devDependency), uruchamiany przez `tsx` **4.23.15** (devDependency).
- `npm run pdf:verify`: sprawdza liczbę i rozmiar stron A4, wszystkie bbox względem `getTextContent` z tolerancją 0,1 pt, wspólny margines x=48 pt, zakres 0..1 i brak warstwy tekstowej skanu.
- Generator wymaga lokalnego `pdftoppm` (Poppler), wyłącznie do rasteryzacji skanu. Przeglądarka nie wymaga Popplera.
- Data utworzenia PDF jest stała. Ponowne generowanie dało identyczne SHA-256 wszystkich czterech PDF-ów.
- Wszystkie dane są syntetyczne. Oryginały organizatora pozostają nienaruszone. Odwołanie ma trzy strony, pełnomocnictwo i przelew po jednej, skan jest obrazem pierwszej strony odwołania.
- Bbox są obliczane z rzeczywistych macierzy tekstu oraz metryk fontu, z normalizacją ascent do udziału pełnej wysokości em jak w TextLayer PDF.js. Skan dziedziczy geometrię rasteryzowanej strony.

Rozmiary nieskompresowane:

| Zasób | Bajty |
|---|---:|
| Worker PDF.js | 1 286 284 |
| odwolanie.pdf | 13 815 |
| pelnomocnictwo.pdf | 10 180 |
| przelew.pdf | 10 940 |
| skan-odwolanie.pdf | 62 178 |
| PDF-y razem | 97 113 |
| Osadzany font generatora NotoSans-Regular.ttf | 621 572 |

Licencje: edytor MIT, PDF.js Apache-2.0, pdf-lib MIT, Noto Sans SIL OFL 1.1. Kopie są przy zasobach w `public/pdf` i `public/demo-pdf`. Font ma osadzony copyright „Copyright 2022 The Noto Project Authors”.

## Pliki

- `src/components/organisms/PdfViewer.tsx`, `PdfViewer.stories.tsx`, `PdfViewer.test.tsx`.
- `src/components/organisms/pdf/{PdfViewerClient.tsx,assets.ts,editorDom.ts,text.ts,viewer.css}`.
- `scripts/pdf/{copy-assets.mjs,generate-demo-pdfs.ts,verify-geometry.ts,REPORT.md}`.
- `public/pdf/*` (worker, wersja i licencje), `public/demo-pdf/*` (4 PDF, 4 JSON geometrii, font i licencja).
- `e2e/pdf-viewer.spec.ts`, `src/app/dev-pdf/page.tsx` (wyłącznie demo/e2e, bez linku w menu).
- `package.json`, `package-lock.json` (trzy wymienione wyżej zależności i skrypty).
- `next dev` automatycznie dopisał w `tsconfig.json` dwa wpisy `include` dla `.next-e2e-3108`; równoległy port 3107 zachowano. Pliku nie zmieniano ręcznie.
- Za zgodą koordynatora: `src/components/stories.test.tsx` (mock samego PdfEditor, stub ResizeObserver, oczekiwanie na rzeczywisty pasek przed axe) i `eslint.config.mjs` (pominięcie skopiowanych plików `public/**`). Reguła wywołań API w `src` pozostaje bez zmian.

Historie obejmują pojedynczy dokument, wiele stron, ramki, aktywny dowód, błąd, skan i ciemny wariant. Zbiorczy axe uruchamia historie w obu motywach. Mock zachowuje rzeczywisty pasek PdfViewer, adapter DOM i portale ramek; nie pomija audytu dostępności.

## Ograniczenia

- W `react-web-pdf-editor` 0.1.6 anulowanie `TextLayer.render()` przy szybkim zoomie/przełączeniu pliku może zgłosić w konsoli nieobsłużone `AbortException: TextLayer task cancelled`. Źródło to wewnętrzny efekt renderowania biblioteki, który anuluje TextLayer podczas cleanup bez obsługi odrzucenia jego promise. W zaobserwowanych przebiegach kolejny render i nawigacja działają; raport nie pomija tego komunikatu.
- Podgląd nadal korzysta z natywnych komunikatów postępu biblioteki, częściowo angielskich; własne sterowanie i alert błędu są po polsku.
- Bbox dotyczą widocznej strony PDF (z uwzględnieniem jej orientacji). Integracja backendu powinna dostarczać ten sam układ współrzędnych po rotacji/crop.
- Demo zawiera skróconą syntetyczną treść prawną. Zachowuje wymagane nazwy, BZP i TED z zadania; nie odtwarza całej typografii dokumentu z F08.
- Integracja z właściwym widokiem dokumentu i modelem API należy do koordynatora. Ten spike nie zmienia kontraktu API.

## Wyniki kontroli (ostatnie zakończone przebiegi)

- `npm run pdf:assets`: exit 0, `Lokalny worker PDF.js 5.7.284`.
- `npm run pdf:demo`: exit 0, `Wygenerowano 4 syntetyczne PDF-y i ich geometrię; skan bez tekstu.`
- `npm run pdf:verify`: exit 0; wszystkie cztery pliki: `geometria i liczba stron poprawne`.
- `npm run typecheck`: exit 0, `tsc --noEmit`, bez błędów.
- `npm run lint`: exit 0, `0 errors, 3 warnings` (istniejące: eksporty konfiguracji ESLint/PostCSS oraz Radio/aria-invalid).
- `npm test`: exit 0, **86 files passed / 729 tests passed**, `Duration 97.07s`.
- `npm run build-storybook`: exit 0, `Storybook build completed successfully`.
- `E2E_PORT=3108 npx playwright test e2e/pdf-viewer.spec.ts --output=/tmp/pdf-spike-out --workers=2`: exit 0, **4 passed (45.1s)**. Obejmuje desktop i phone, realny canvas/tekst, bbox obrysu względem tekstu **<2 px** przy 100% i 150%, zmianę strony i szerokości, aktywny dowód, klawiaturę, miniatury, tekst, skan, błąd pliku, blokadę drop/edycji/eksportu, axe w obu motywach, białą stronę w dark i **zero żądań do obcych hostów**.
- `python3 scripts/verify_docs.py` z roota: exit 0, `OK: 440 materiałów, 62 dokumentów, odnośniki lokalne i integralność źródeł.`

Scenariusz e2e ma limit całkowity 90 s: dwa audyty axe i równoległe buildy w współdzielonym IDE przekraczały domyślny limit 30 s. Limity poszczególnych asercji i tolerancja geometrii pozostały rygorystyczne.

Czas od nawigacji do widocznego PDF i poprawnej ramki w ostatnim przebiegu: **desktop 6263 ms, phone 4151 ms**. To pomiar serwera deweloperskiego obejmujący nawigację, hydratację i ewentualną kompilację Next, pod współdzielonym obciążeniem; nie jest pomiarem czystego czasu PDF.js ani produkcyjnego eksportu.

Logi ostatnich przebiegów: `/tmp/pdf-spike-{typecheck-final,lint-final,tests-final,storybook-final,e2e-final,geometry,demo-final,docs}.log`. Zrzuty: `/tmp/pdf-spike-desktop.png`, `/tmp/pdf-spike-phone.png`. Pliki i raport pozostawiono bez commita.
