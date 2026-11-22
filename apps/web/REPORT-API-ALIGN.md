# API-ALIGN — dopasowanie UI do kontraktu silnika

Zmiany bez commita. Zakres: model UI, mock, obecne widoki i testy; bez nowych tras i zmian w OpenAPI silnika. Bez zmian oryginałów organizatora.

## Implementacja

- `src/lib/api/schemas.ts`: klasy `odwolanie`, `pelnomocnictwo`, `przelew`, `obcy`; pola ze ścieżkami, grupą modelu, typem, opisem, wymagalnością i nullable; cztery stany pola, pięć niezależnych powodów braków, pokrycie stron i błędy techniczne.
- `contract.ts`, `contract.generated.json`, `scripts/generate-ui-contract.py`: migawka rzeczywistego OpenAPI, metadane klas i kontenerów, czysta budowa zagnieżdżonego JSON i walidacja kluczy, list, obiektów, typów, enumów, formatów i zakresów. Alias `przez-pelnomocnika` oraz wielkie litery kluczy organizatora pozostają bez zmian. Puste listy, wiele podmiotów i nullable obiekt pełnomocnika są obsługiwane.
- `processing.ts`, `codes.ts`, `client.ts`, `hooks.ts`: przebieg E/L/T1/T2/T3/T4/T5/Eksport, diagnoza dokumentu/strony/regionu, porównanie i przywracanie wersji. T2/T4 są jawnie pomijane w demonstracji v1.
- `mock/data.ts`: 12 dokumentów syntetycznych; pełne odwołania, pięć powodów braków na pięciu polach doc-3, skan OCR doc-4, konflikt klas doc-5, `LLM_TIMEOUT` doc-6, obcy doc-7, wiele dokumentów doc-8, przetwarzanie doc-9, przelew doc-10, pełnomocnictwo doc-11. Dane Belmoria/Aurelink/BZP/TED/kod 9/200.00/PESEL odpowiadają §9.1 projektu UI; identyfikatory są tekstem.
- `mock/client.ts`: eksport wariantu A kontroluje rzeczywisty schemat; legalny null nie blokuje eksportu. Awaria, nierozstrzygnięta klasa, wiele dokumentów i niezgodność schematu blokują pobranie; potwierdzony obcy daje dokładnie `{}`. Historia doc-1: v1 silnik, v2 korekta TED, v3 zatwierdzony; przywrócenie dopisuje v4, zachowując poprzednie wersje. Korekta kodu czynności aktualizuje zależny opis ze słownika.
- `features/dokument/*`: grupy według nazw modeli, JSON zagnieżdżony, szczegóły braków przy polach, rzeczywista metoda i przesłanki dowodu, osobny raport pokrycia, opcjonalna geometria oraz „Nie oceniono” zamiast fikcyjnej pewności. `DocumentProcessing.tsx` udostępnia przebieg, diagnozę i historię w obecnym widoku.
- `features/dokumenty-lista/*`, `features/dodawanie/*`, `features/klasy/*`: nowe klasy, źródła PDF/OCR, kody, plik wynikowy na kafelku, metadane kontenerów i wersja v1. Pulpit korzysta z tego samego nowego modelu bez zmiany kompozycji.
- Zaktualizowano testy widoków i e2e oraz przykłady Storybook pól i JSON. Dodano testy kontraktu i przebiegu/historii oraz `e2e/api-align.spec.ts`.

## Mapowanie dawnych pól

Nie migrujemy fikcyjnych wartości do pól o innym znaczeniu. Mock został zastąpiony danymi właściwych klas.

| Dawne pole | Ścieżka kontraktu / decyzja |
|---|---|
| `sygnatura` | Brak odpowiednika; numer referencyjny zamówienia to osobne `ZamowieniePubliczne.numer_postepowania`. |
| `data_pisma` | `OdwolanieKIO.data` (nagłówek pierwszej strony). |
| `organ` | Brak odpowiednika „organu rozpatrującego”; `Zamawiajacy.0.nazwa` opisuje zamawiającego, nie organ odwoławczy. |
| `wnioskodawca` | Podmiot odwołujący: `Odwolujacy.0.nazwa`. |
| `kwota` | Wyłącznie `przelew_bankowy.kwota`; usunięta fikcyjna kwota sporu z odwołania. |
| `data_decyzji`, `rozstrzygniecie`, klasa `decyzja` | Usunięte; kontrakt nie zawiera decyzji administracyjnej. Data zaskarżonej czynności ma odrębne znaczenie: `OdwolanieKIO.czynnosc_dzien`. |
| `mocodawca` | `mocodawca.0.data.nazwa` / `.imie_nazwisko`, dane podmiotu i lista podpisujących. |
| `pelnomocnik` | `pelnomocnicy.0.imie_nazwisko` w pełnomocnictwie; `Odwolujacy.0.pelnomocnik.imie_nazwisko` w odwołaniu. |
| `zakres` | Brak odpowiednika w ocenianym JSON; usunięte. |

Ścieżki UI używają jawnych indeksów list. Przykładowe małe litery `zamowienie_publiczne` z treści zadania nie są aliasami kontraktu i nie trafiają do eksportu.

## Rozbieżności źródeł i kody

`powody.py` definiuje 12 przyczyn odwołania, nie pięć powodów braków. Test porównuje jego słownik z enumem OpenAPI. Pięć powodów braków pochodzi z architektury §4.6: `missing`, `not_applicable`, `unreadable`, `conflicting`, `unprocessed`; kody są niezależne od powodu.

Stan silnika rozdziela postęp `queued/running/done` i rezultat `complete/partial/foreign/ambiguous/technical_error`. Dotychczasowe identyfikatory prezentacyjne statusów `full/error/multi` zachowano dla istniejących atomów; dokument ma równolegle jawny `state`. `multi` odpowiada `ambiguous` z kodem `wiele_dokumentow` i blokadą zleconą w zadaniu. Nowsza architektura §4.4/§6 opisuje segmentację wyłącznie jako ostrzeżenie; tej sprzeczności nie ukryto ani nie zmieniono źródłowego kontraktu.

Mapowanie katalogu na proponowane kody API jest zapisane w `codes.ts`: `ocr_unavailable`, `ocr_error`, `pdf_corrupted`, `pdf_encrypted`, `llm_unavailable`, `llm_authorization`, `llm_rate_limit`, `llm_invalid_response`, `invalid_configuration`, `time_limit`, `context_limit`, `write_failed`, `result_validation_failed`, `class_ambiguous`, `scan`, `mixed_page`, `mixed_document`, `low_quality`, `invalid_ocr_layer`, `clipped_text`, `foreign_document`, `information_not_explicit`, `data_after_page_3`, `class_lookalike`, `multiple_documents`. Zachowano `dokument_obcy`, `wiele_dokumentow`, `zla_warstwa_ocr` z projektu UI oraz `LLM_TIMEOUT` z F14. To nie jest deklaracja ich obecności w obecnym OpenAPI. Architektura wymienia także proponowane `evidence_unanchored`, bez rozszerzania katalogu organizatora.

## Brakujące API — propozycje do osobnego kontraktu

Obecne OpenAPI ma wyłącznie `GET /healthz` i schematy wyników. Wszystkie poniższe ścieżki są propozycjami; nie zostały dopisane do `openapi.yaml`:

| Metody mocka / potrzeba UI | Proponowana ścieżka |
|---|---|
| system, modele, OCR, limity | `GET /api/v1/system` |
| lista dokumentów i dashboard | `GET /api/v1/documents`, `GET /api/v1/dashboard` |
| upload / wsad | `POST /api/v1/batches` |
| dokument i ponowienie | `GET /api/v1/documents/{id}`, `POST /api/v1/documents/{id}/runs` |
| przebieg / diagnoza | `GET /api/v1/documents/{id}/pipeline`, `GET /api/v1/documents/{id}/diagnosis` |
| wynik, dowody, raport, decyzja eksportu | `GET /api/v1/documents/{id}/{result,evidence,report,export-decision}` |
| odczyt konfiguracji klas v1 | `GET /api/v1/classes` |
| kody | `GET /api/v1/codes` |
| wersje i przywracanie (po v1 silnika) | `GET /api/v1/documents/{id}/versions`, `POST /api/v1/documents/{id}/versions` z `restoreFrom` |
| korekta i rozstrzygnięcie klasy (po v1 silnika) | `PATCH /api/v1/documents/{id}/fields`, `POST /api/v1/documents/{id}/classification` |

Endpointy użytkowników, audytu i konfiguracji klucza pozostają osobnymi potrzebami UI; klucze muszą pozostać po stronie serwera. Mock nie wykonuje połączeń z silnikiem, OCR ani modelem. Metadane dostawcy nadal mają status niepotwierdzony.

## Zmiany wizualne i ograniczenia

- Przegląd dokumentu: więcej rzeczywistych pól, osobne grupy modeli i indeksy list, pięć powodów braków, metadane wersji; sekcje przebiegu/diagnozy/historii pod formularzem, aby pierwsze pole pozostawało widoczne także przy 720 px wysokości. Pełny panel diagnozy F23 i historia F24 są tutaj rozwinięciami wewnątrz obecnej trasy, bez osobnej szuflady lub trasy.
- JSON i eksport: zagnieżdżone obiekty i listy, inne nazwy plików, legalny null nie blokuje eksportu.
- Dowody: więcej wierszy, metoda i przesłanki wyliczenia, jawne pokrycie stron oraz nieoceniona pewność.
- Klasy, lista/galeria, dodawanie i pulpit: trzy właściwe klasy i karta obcego, nowe nazwy dokumentów, kody i liczniki; kafelki mają nazwę wyniku.
- Baza `e2e/visual.spec.ts-snapshots` wymaga osobnej aktualizacji po przeglądzie; nie była aktualizowana. Zrzuty z testów funkcjonalnych są tylko artefaktami w `/tmp`.
- Schematy wyników nie definiują polskich etykiet, metadanych przebiegu, diagnoz, użytkowych wersji ani dowodów; modele pomocnicze UI opierają się na dokumentacji architektury, nie na fikcyjnych endpointach. Test źródła prawdy wymaga Python 3 i PyYAML; nie wymaga Pydantic. Sprawdza klucze/aliasy `models.py` względem OpenAPI, a każdy pełny wynik waliduje rekurencyjnie względem tego samego schematu.

## Weryfikacja

Pierwsze pełne uruchomienie wykryło cudze błędy w równoległym zadaniu PDF (`public/pdf/pdf.worker.min.mjs`, stories `PdfViewer`, brak `ResizeObserver`); zostały zgłoszone koordynatorowi i poprawione przez właściciela PDF. Powtórzone pełne `npm test`: 86 plików, 729 testów przeszło; lint po cudzej poprawce: 0 błędów, 3 istniejące ostrzeżenia. Pierwsze e2e wykryło własny problem widoczności pierwszego pola i niejednoznaczny selektor nowej nazwy pliku; oba poprawione, ponadto Fast Refresh podczas równoległej pracy przerwał scenariusze klucza/uploadu.

## Lista plików zadania

```text
REPORT-API-ALIGN.md
scripts/generate-ui-contract.py
e2e/api-align.spec.ts
e2e/dokument.spec.ts
e2e/dokumenty-lista.spec.ts
src/lib/api/schemas.ts
src/lib/api/client.ts
src/lib/api/hooks.ts
src/lib/api/contract.ts
src/lib/api/contract.generated.json
src/lib/api/contract.test.ts
src/lib/api/processing.ts
src/lib/api/codes.ts
src/lib/api/mock/data.ts
src/lib/api/mock/client.ts
src/lib/api/mock/client.test.ts
src/lib/api/mock/processing.test.ts
src/features/dokument/DocumentView.tsx
src/features/dokument/DocumentView.test.tsx
src/features/dokument/DocumentField.tsx
src/features/dokument/DocumentPreview.tsx
src/features/dokument/DocumentEvidence.tsx
src/features/dokument/DocumentException.tsx
src/features/dokument/DocumentProcessing.tsx
src/features/dokument/format.ts
src/features/dokument/format.test.ts
src/features/dokumenty-lista/DocumentTile.tsx
src/features/dokumenty-lista/DocumentsList.tsx
src/features/dokumenty-lista/DocumentsList.test.tsx
src/features/dokumenty-lista/FilterBar.tsx
src/features/dokumenty-lista/filters.ts
src/features/dokumenty-lista/filters.test.ts
src/features/klasy/ClassesView.tsx
src/features/klasy/ClassesView.test.tsx
src/features/dodawanie/AddDocumentsView.tsx
src/features/dodawanie/BatchProgress.tsx
src/components/molecules/CodeBlock.stories.tsx
src/components/molecules/FieldRow.stories.tsx
src/components/organisms/JsonViewer.stories.tsx
```

Ścieżki są względem `apps/web`. Pozostałe równoległe zmiany w drzewie, w tym pakiety i nowy podgląd PDF, nie należą do API-ALIGN.

## Końcowe wyniki komend

```text
python3 scripts/verify_docs.py
OK: 440 materiałów, 62 dokumentów, odnośniki lokalne i integralność źródeł.

npm run typecheck
> tsc --noEmit
(kod wyjścia 0)

npm run lint
3 problems (0 errors, 3 warnings)
(kod wyjścia 0; istniejące ostrzeżenia: eslint.config.mjs, postcss.config.mjs, Radio.tsx)

npm test
Test Files 86 passed (86)
Tests 729 passed (729)

E2E_PORT=3107 npx playwright test e2e/api-align.spec.ts e2e/dziennik.spec.ts e2e/dokument.spec.ts e2e/dodawanie.spec.ts e2e/pulpit.spec.ts e2e/dokumenty-lista.spec.ts e2e/smoke.spec.ts e2e/klucz.spec.ts e2e/pdf-viewer.spec.ts --output=/tmp/api-align-out --workers=4
222 passed (6.4m)

git diff --check
(kod wyjścia 0)
```

Logi: `/tmp/api-align-typecheck-final.log`, `/tmp/api-align-lint-final.log`, `/tmp/api-align-test-final.log`, `/tmp/api-align-e2e-final.log`. Ostatnia lokalna korekta komunikatu obcego została dodatkowo sprawdzona testami przeglądu: 29/29. Kontrole obejmują równoległy kod PDF po poprawkach jego właściciela; cudze pliki nie są przypisane do API-ALIGN.

Po przeglądzie zrzutów ograniczono obrys w syntetycznym PDF do aktywnego dowodu oraz treść do obszaru kartki; pełny tekst jest dostępny osobno. Źródło tekstu strony pochodzi z diagnozy, także na stronach bez dowodów; strona nieprzetworzona nie otrzymuje etykiety tekstu PDF.
