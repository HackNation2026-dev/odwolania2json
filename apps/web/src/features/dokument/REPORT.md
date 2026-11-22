# W4 — poprawka po odbiorze

## Przyczyna i poprawki

Test przed poprawką odtworzył błąd doc-3 przy 1440×900 i 1280×720: pierwsze pole miało przecięcie z viewportem równe 0. Rozbudowana stopka eksportu zabierała miejsce panelowi, a wysokie banery i opis rozpoznania wypychały pola poza jego widoczną część.

- Panel ma jawne `flex: 1 1 0%`, `min-height: 0`, `overflow: auto`, stabilne miejsce paska przewijania i klasę `.scroll-pane`; pasek zakładek i stopka nie kurczą się.
- Stopka zawiera krótki stan eksportu i odsyłacz do powodów, dwa przyciski i informację o osobnych dowodach. Pełna lista blokad jest w zakładce Eksport. Na telefonie stopka jest przypięta do okna, a treść ma zapas pod nią.
- Baner wyniku częściowego zachowuje wszystkie powody po polsku; rozwijany opis nie zajmuje stale miejsca nad polami. Rozpoznanie i „Dlaczego?” są w zwartym wierszu.
- Przywrócone nagłówki grupy zgodne z realną klasą mocka, liczniki wszystkich filtrów, etykieta i klucz mono w jednym wierszu, wartość, strona/cytat/źródło/metoda i znacznik stanu. Dodana jawna akcja „Pokaż dowód”; na telefonie otwiera zakładkę Dokument.
- Dowody na komputerze są zwartą tabelą jak F60, a na telefonie kartami. Pokrycie stron i osobny raport mieszczą się po tabeli. Liczba stron z tekstem nie uwzględnia wpisów wychodzących poza fizyczną liczbę stron PDF.
- Na telefonie skrócono nagłówek zgodnie z F18 i przeniesiono zakładki nad podgląd PDF, aby powrót do danych nie wymagał przewijania.
- Powiązanie zaznaczenia z polem korzysta z `evidenceIds`; poprawia doc-10/doc-11, których mock ma odziedziczone klucze w dowodach. Dwa testy integracyjne utrwalają tę sytuację.

AppShell, tokeny, API, mock i hooki pozostawione koordynatorowi; brak commita.

## Pliki tej poprawki

- `src/features/dokument/DocumentView.tsx`
- `src/features/dokument/DocumentField.tsx`
- `src/features/dokument/DocumentException.tsx`
- `src/features/dokument/DocumentEvidence.tsx` — nowy
- `src/features/dokument/dokument.module.css`
- `src/features/dokument/DocumentView.test.tsx`
- `e2e/dokument.spec.ts`
- `src/features/dokument/REPORT.md`

## Testy i przegląd wizualny

Regresja sprawdza doc-1, doc-3, doc-4, doc-10, doc-11 przy 1440×900, 1280×720 i 360×800: pierwsze pole na komputerze widoczne od razu, Data pisma/Data decyzji/Pełnomocnik i ostatnie pole osiągalne przez przewijanie, wysokość panelu >180 px, każda `.scroll-pane` >0 px, przycisk pobrania w viewportcie. Ten zestaw działa w obu projektach Playwright.

Macierz wizualna obejmuje doc-1…doc-12 × jasny/ciemny × wszystkie cztery zakładki desktopu i pięć telefonu (w tym Dokument): 216 zrzutów. Porównano wszystkie 18 plansz obejmujących 216 zrzutów i reprezentatywne pełne obrazy z F08, F10, F60, F61, F13, F14, F40, F41, F51, F52 i F18. Po ostatniej korekcie ponownie sprawdzono mobilny Dokument. Galeria: /tmp/w4-review-gallery/index.html; plansze: /tmp/w4-review-gallery/*.png; oryginały desktopu: /tmp/w4-fix-review/, telefonu: /tmp/w4-fix-phone-final/. Galeria zawiera dokładnie 216 odnośników do oryginałów.

Końcowe kontrole: typecheck exit 0; lint 0 błędów, 2 istniejące ostrzeżenia konfiguracji; npm test 18 plików / 92 testy; verify_docs OK (440 materiałów, 59 dokumentów). Pełny pierwszy przebieg został przerwany sygnałem 143 przy konkurencyjnych globalnych E2E; koordynator zatrzymał je, a własny zawieszony serwer 3104 zrestartowano. Raport końcowy podaje wyniki powtórek, nie uznaje przerwanego przebiegu za sukces.

## Ograniczenia danych a makiety

Makiety zawierają dane KIO, grupy zagnieżdżone, wersję silnika/kontraktu i metody ekstrakcji; mock daje płaskie pola innych trzech klas bez tych metadanych. Dlatego grupa jest nazwana rzeczywistą klasą, a brak metody jest jawny; nie utworzono fikcyjnych reguł, rewizji, segmentów ani cytatów. Podgląd PDF pozostaje jawnie syntetyczny według zadania. Doc-4 pokazuje niedostępny OCR; tekst OCR i ostrzeżenie jakości są renderowane, gdy dowód ma `source=ocr` (test integracyjny), zamiast przypisywać OCR zwykłemu tekstowi z seed. Doc-6 ma zero stron i pokazuje brak podglądu zamiast fikcyjnego skanu. Wariant B z F61 jest opisowy i niedostępny; obowiązuje wariant A. Zmiany powłoki pozostają poza tym zadaniem.


## Końcówki poleceń

E2E dotyczą wyłącznie e2e/dokument.spec.ts, E2E_PORT=3104, --workers=3. Pokryto 120 unikalnych przypadków macierzy w obu projektach; po ostatnich korektach ponowiono telefon i regresję 360 px. To rzeczywiste wyniki osobnych uruchomień.

```text
--grep-invert 'visual review' --output=/tmp/w4-fix-checked
72 passed (1.2m)

--grep 'visual review' --output=/tmp/w4-fix-review
48 passed (1.1m)

--project=phone --output=/tmp/w4-fix-phone-final
60 passed (54.6s)

--grep 'keeps review fields reachable at 360|shows JSON wrapping'
--output=/tmp/w4-fix-last-regression
12 passed (8.9s)

npm run typecheck
exit 0

npm run lint
2 warnings (0 errors)

npm test
Test Files 18 passed (18)
Tests 92 passed (92)

python3 ../../scripts/verify_docs.py
OK: 440 materiałów, 59 dokumentów, odnośniki lokalne i integralność źródeł.
```
Logi: /tmp/w4-fix-checked.log, /tmp/w4-fix-review.log, /tmp/w4-fix-phone-final.log, /tmp/w4-fix-last-regression.log, /tmp/w4-fix-unit-final.log.
Brak pozostałych awarii w swoim zakresie; powłoka i wynikające z niej różnice wysokości nagłówka pozostają zakresem koordynatora.
