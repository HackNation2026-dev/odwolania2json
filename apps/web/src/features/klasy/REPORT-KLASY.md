# W-KLASY — ekrany i refaktor

Bez commita. Odczytano `apps/web/AGENTS.md`, raport DS-B, README, wymagania,
pytania otwarte, przepływy klas i §9.1 projektu UI. Obejrzano wszystkie makiety
zakresu: F20, F21, F36, F37, F46, F47, F48, F55 i F59.

## ZROBIONE

### Pliki

- `src/app/klasy/[id]/page.tsx`: cienka strona, asynchroniczne parametry Next.js.
- `src/features/klasy/ClassesView.tsx`, `ClassesView.test.tsx`: istniejąca lista,
  karty biblioteczne, linki do szczegółów, atomowa blokada braku konfiguracji.
- `ClassDetailView.tsx`, `ClassDetailView.test.tsx`, `ClassDetailView.stories.tsx`:
  odczyt pól/YAML, podgląd, test, aktywacja i scenariusze demonstracji.
- `ClassDraftEditor.tsx`, `ClassFormPreview.tsx`, `ClassActivation.tsx`: małe
  elementy szczegółów, składane z biblioteki.
- `ConfigurationGuard.tsx`: wspólny komunikat i hook blokady dla wykonawcy `/dodaj`.
- `src/components/molecules/ConfigurationFieldList.tsx`, odpowiadające `.stories.tsx`
  i `.test.tsx`: wspólny wykaz reguł wymagania i dopuszczalności null; zachowany
  wygląd rozwiniętych pól starej listy. Bez zmian istniejących komponentów biblioteki.
- Dopiski własnych typów i metod do `src/lib/api/{schemas,client,hooks}.ts`;
  import i jedna pozycja w obiekcie `src/lib/api/mock/client.ts`.
- `src/lib/api/mock/klasy.ts`, `klasy.test.ts`: odizolowany mock zestawów klas.
- `e2e/klasy.spec.ts`, `e2e/klasy-scenarios.spec.ts`: własne przepływy Playwright.

Współdzielone pliki API zawierają też równoległe dopiski innych wykonawców;
ten raport przypisuje sobie tylko metody i typy klas. Nie zmieniano tokenów,
globalnego CSS, powłoki, istniejących atomów ani innych obszarów funkcjonalnych.

### Makieta → implementacja

| Makieta | Implementacja i odstępstwa |
| --- | --- |
| F20 | Trzy oficjalne klasy z kontraktu: 22/8/6 pól, osobna karta dokumentu obcego, aktywna wersja zestawu i nowe linki „Szczegóły”. Zachowano rozwijane reguły i istniejący rozbudowany opis oraz storyboard, żeby refaktor zachował wygląd. API nie dostarcza liczby pól wyliczanych: brak zgadywanych liczników. |
| F21 | `/klasy/[id]`: Pola / YAML / Podgląd formularza / Test; YAML tylko do odczytu, Kopiuj, Pobierz `<id>.yaml`, układ biblioteczny 60/40. YAML pokazuje wszystkie pola kontraktu zamiast skrótu z makiety. CodeBlock nie numeruje wierszy. Do 768 px panele korzystają z zakładek TwoPane zamiast pionowego stosu. |
| F36 | Szkic v2 dla przelewu, edycja w Textarea oraz kopia w CodeBlock. Nieznany normalizator daje „Linia 14: brak normalizatora”; wynik v1 jest nieaktualny, zapis i aktywacja zablokowane. Błąd jest banerem w panelu testu, bez dekorowania konkretnej linii edytora. Zapis i aktywacja są jedną potwierdzaną operacją „Zapisz i aktywuj wersję 2”, bez osobnego zapisu na serwerze. |
| F37 | Dialog „Aktywuj zestaw v2?”, lista zmian, trzy klasy i jawny wynik syntetycznego testu. Edycja/test są wyraźnie oznaczoną demonstracją E2; brak deklaracji rzeczywistej analizy PDF. |
| F47 | „Aktywowanie…”, status aria-live, blokada ponownego żądania, wyłączone akcje Anuluj i Aktywuj, odrzucenie Esc/zamknięcia. Biblioteczny przycisk X pozostaje widoczny, ale zamknięcie podczas operacji jest blokowane przez onClose. |
| F48 | „Nie aktywowano. Nadal aktywny v1. Ponów”; błąd pozostaje wewnątrz otwartego dialogu i można ponowić. Makieta pokazuje błąd na stronie wersji; zastosowano zasadę biblioteki, według której błąd nie zamyka dialogu. |
| F55 | „Zestaw v2 aktywny”, klasy i ich wersje: odwolanie v1, pelnomocnictwo v1, przelew v2 (7 pól). Informacja o przypięciu historycznych zadań do v1 jest tekstem, bez fikcyjnej historii zadań. Aktywny YAML i podgląd są odświeżane po potwierdzeniu. |
| F46 | Wspólny dokładny komunikat „Błąd konfiguracji. Brak poprawnego zestawu klas. Analiza zablokowana.”, role=alert, bez karty obcego i bez zastępczego `{}`. Brak szczegółowego błędu silnika, którego API demonstracji nie dostarcza. Hook `useClassConfiguration` i komponent `ConfigurationError` są gotowe do wpięcia przez obszar listy. |
| F59 | Zachowano pięć kroków instrukcji YAML poza GUI. Osobna „Nota testowa” zamiast modyfikowania oficjalnego kontraktu odwołania; krok końcowy przypomina przywrócenie oficjalnego zestawu. Storyboard pozostaje instrukcją, nie dowodem rozbudowy działającego ekstraktora. |

### Mock i API

Komponenty korzystają wyłącznie z hooków `@/lib/api/hooks`. Nowe metody:
`getClassDetail(id)`, `getClassYaml(id)`, `testClassDraft(id, yaml?)`,
`activateClassSet(version)`, `listClassVersions()`. Metody odczytu zwracają
typowane definicje, YAML i wersje; test ma rewizję, listę błędów i opis pliku.
Aktywacja ma opóźnienie, zachowuje v1 po błędzie i odrzuca równoległe żądanie.
UI dodatkowo unieważnia test po zmianie treści i blokuje podwójne kliknięcie.
Aktywowany szkic staje się odczytywanym YAML-em; szczegóły i podgląd dostają
siódme, jawnie demonstracyjne pole. Oficjalne kontrakty konkursowe nie są zmieniane.

Scenariusze wyłącznie w mocku i Storybooku:
`ready`, `invalid`, `activation-error`, `no-configuration`. Dla E2E można ustawić
`NEXT_PUBLIC_MOCK_CLASS_SCENARIO`; w interfejsie nie ma przełącznika scenariuszy.
Błąd aktywacji występuje przy pierwszej próbie; ponowienie potwierdza v2.
Mock testuje demonstracyjne reguły, a nie pełną składnię YAML ani ekstrakcję PDF.

Propozycje przyszłych endpointów:

- `GET /api/classes/{id}` i `GET /api/classes/{id}/yaml`.
- `POST /api/classes/{id}/draft/test` z YAML-em i oczekiwaną rewizją.
- `POST /api/class-sets/{version}/activation` z oczekiwaną aktywną wersją,
  rewizją przetestowanego szkicu i kluczem idempotencji.
- `GET /api/class-sets` z klasami, wersjami, zmianami i aktywnym zestawem.
- Osobny zapis szkicu i rzeczywiste wyniki testów PDF wymagają endpointów backendu;
  nie są pozorowane jako działający silnik.

Nie dodano dostawcy modelu, zewnętrznego API ani potwierdzeń licencji/lokalizacji.

### Kontrole

Wszystkie komendy dotyczą `apps/web`, poza weryfikacją dokumentacji.

```text
E2E_PORT=3112 npx playwright test e2e/klasy.spec.ts --workers=2 --output=/tmp/wklasy-flow-out
8 passed (2.5m)
Końcowe powtórzenie: --output=/tmp/wklasy-final-flow-out
8 passed (1.4m)

NEXT_PUBLIC_MOCK_CLASS_SCENARIO=activation-error E2E_PORT=3112 npx playwright test e2e/klasy-scenarios.spec.ts -g 'activation failure' --workers=2 --output=/tmp/wklasy-activation-out
4 passed (1.2m)

NEXT_PUBLIC_MOCK_CLASS_SCENARIO=no-configuration E2E_PORT=3112 npx playwright test e2e/klasy-scenarios.spec.ts -g 'missing configuration' --workers=2 --output=/tmp/wklasy-configuration-out
4 passed (52.6s)

npm run build-storybook
Storybook build completed successfully

python3 scripts/verify_docs.py
OK: 440 materiałów, 65 dokumentów, odnośniki lokalne i integralność źródeł.

npm run typecheck && npm run lint && npm test -- --maxWorkers=2 --testTimeout=20000
tsc --noEmit
3 problems (0 errors, 3 warnings)
Test Files 107 passed (107)
Tests 827 passed (827)
Duration 195.10s
exit 0
```

E2E: desktop i phone, oba motywy, axe bez serious/critical; w przepływie błędu
YAML dodatkowo szerokość 320 px bez poziomego przewijania. Test jednostkowy
z wstrzymaną odpowiedzią potwierdza blokadę podwójnej aktywacji i zamknięcia.
Zrzuty błędu YAML na telefonie, błędu aktywacji i zakończenia obejrzano.
Logi: `/tmp/wklasy-flow.log`, `/tmp/wklasy-activation.log`,
`/tmp/wklasy-configuration.log`, `/tmp/wklasy-storybook-final.log`.

Własny zakres po końcowych zmianach:

```text
npx vitest run src/features/klasy src/lib/api/mock/klasy.test.ts src/components/molecules/ConfigurationFieldList.test.tsx --maxWorkers=2 --testTimeout=20000
Test Files 4 passed (4)
Tests 19 passed (19)
Duration 29.10s
Końcowe powtórzenie po doprecyzowaniu etykiet kontraktu v1:
Test Files 4 passed (4)
Tests 19 passed (19)
Duration 6.76s
```

Limit czasu testu zwiększono wyłącznie w poleceniu ze względu na obciążenie
maszyny równoległymi pracami; asercje i progi wizualne pozostały niezmienione.
Wcześniej domyślne 5 s było przekraczane zarówno przez testy własne, jak i
testy dokumentów/listy. Log końcowego zakresu: `/tmp/wklasy-unit-closed.log`;
log pełnego zielonego przebiegu: `/tmp/wklasy-check-clean.log`.
Ostrzeżenia lint dotyczą istniejących konfiguracji eksportów i atomu Radio,
bez błędów w nowym kodzie. `npx next typegen` odświeżyło generowane typy tras.
Przejściowy przebieg lint przerwało usunięcie tymczasowej kopii porównania;
po usunięciu plików eksperymentalnych cały łańcuch wykonano ponownie i przeszedł.

### Bramka wizualna

Uruchomiono wymaganą trasę `-g klasy` na porcie 3112, bez zmiany baz lub progu.
Pełna bramka: **4 failed**, oba motywy × desktop/phone. Nowy link „Szczegóły” dodaje wiersz do kart i przesuwa
niższe sekcje. Na telefonie dodatkowo widoczne są równoległe zmiany powłoki spoza
zakresu W-KLASY. Obejrzano cztery obrazy różnic: oba motywy × desktop/phone.
To odstępstwa nowych elementów A i wspólnej powłoki; nie przypisano ich refaktorowi B.

Osobno wykonano kontrolę izolującą B: kopia starego ClassesView z HEAD przeciwko
nowemu widokowi w tej samej aktualnej powłoce, przy ukrytych wyłącznie nowych
linkach. Porównanie buforów PNG jest ścisłe, bez tolerancji:

```text
E2E_PORT=3112 npx playwright test e2e/klasy-parity.spec.ts --project=desktop --workers=2 --output=/tmp/wklasy-parity-final-out
6 passed (1.0m)
```

320/768/1440 px × jasny/ciemny: 6/6 testów; w każdym porównano widok zwinięty
i rozwinięty, czyli **12/12 identycznych par obrazów**, także po wydzieleniu
ConfigurationFieldList. Tymczasowe kopie kodu,
trasa i test zostały usunięte; nie dodano baz do Git. Obrazy i log pozostały w
`/tmp/wklasy-parity-final-out` i `/tmp/wklasy-parity-final.log`.
Końcowy log pełnej bramki: `/tmp/wklasy-visual-final.log`; obejrzano również
końcowe cztery obrazy różnic w `/tmp/wklasy-out`.

| Trasa / motyw / projekt | Wynik pełnej bramki |
| --- | --- |
| `/klasy`, jasny, desktop | 81 546 różnych pikseli; wysokość 1331 → 1387 px |
| `/klasy`, ciemny, desktop | 164 684 różnych pikseli; wysokość 1331 → 1387 px |
| `/klasy`, jasny, phone | 117 178 różnych pikseli; wysokość 3280 → 3243 px |
| `/klasy`, ciemny, phone | 134 205 różnych pikseli; wysokość 3280 → 3243 px |

Desktop: dodany wiersz linku z odstępem zwiększa wysokość o 56 px. Telefon:
trzy takie wiersze zwiększają treść o 168 px, a niezależna zmiana nagłówka i
nawigacji mobilnej w powłoce zmniejsza ją o 205 px; łącznie -37 px.

### Granice

- Wpięcie wspólnej blokady w `/dodaj` należy do wykonawcy obszaru listy;
  import: `@/features/klasy/ConfigurationGuard`.
- Demo nie uruchamia silnika YAML ani modelu; nie dowodzi ekstrakcji nowych pól.
- Nie ma trwałego zapisu po przeładowaniu przeglądarki ani rzeczywistej historii zadań.
- `listClasses` zachowuje oficjalne pola kontraktu; demonstracyjna zmiana jest
  prezentowana przez szczegóły klasy i listę wersji zestawu. Po aktywacji lista
  jawnie rozróżnia „Aktywny zestaw: v2 · demonstracja” od kart „v1 · kontrakt”,
  więc nie przedstawia sześciu bazowych pól jako pełnej konfiguracji v2.
- Kontrole globalne uruchamiano podczas równoległych zmian innych wykonawców;
  przejściowe błędy typów/testów poza zakresem są opisane w wynikach, bez ich poprawiania.

## DO ZROBIENIA

Poniższe instrukcje dotyczą dalszych etapów. Obecne GUI pozostaje jawnie oznaczoną
demonstracją; żaden z tych punktów nie jest dodatkową, częściowo podpiętą trasą.

### 1. Wpięcie blokady konfiguracji w Nową analizę

**Cel:** ten sam brak poprawnego zestawu blokuje `/klasy` i start `/dodaj`.
**Makiety:** `apps/web/design/F46-brak-konfiguracji.png`.
**Pliki:** `apps/web/src/features/dodawanie/AddDocumentsView.tsx`, `apps/web/src/features/dodawanie/useAddDocumentsState.ts`, `apps/web/src/features/klasy/ConfigurationGuard.tsx`.
**Kroki:**
1. Importuj istniejący `useClassConfiguration` i `ConfigurationError` z obszaru klas; nie kopiuj komunikatu.
2. Podczas odczytu pokazuj LoadingState; przy `blocked` wyłącz start i zablokuj obsługę submit także programowo.
3. Odróżnij błąd odczytu (ErrorState z ponowieniem) od potwierdzonego braku aktywnego zestawu (ConfigurationError). Nie uruchamiaj addDocuments/addResolvedDocuments w żadnym z tych stanów.
4. Dodaj test z `listClassVersions: async () => []` i z odrzuconym odczytem; asercja ma sprawdzać brak mutacji API, a nie tylko disabled.
**Kryteria:** `/dodaj` pokazuje dokładny komunikat F46; brak żądania analizy i brak zastępczego JSON; stany ładowania/błędu/ponowienia działają.
**Weryfikacja:** `npm run typecheck`, `npm run lint`, `npm test -- --maxWorkers=2 --testTimeout=20000`; Playwright obszaru dodawania na przydzielonym porcie, oba projekty/motywy i axe.
**Pułapki i decyzje:** `blocked` jest prawdziwe także podczas ładowania i awarii; sam `useClasses().data.length` nie wystarcza. Wariant A eksportu pozostaje obowiązujący.
**Zależności:** właściciel W-LISTA; bez zmian we wspólnej powłoce.

### 2. Rzeczywista walidacja i ekstrakcja po zmianie YAML

**Cel:** zastąpić jawny mock działającym backendem; nie deklarować tego w obecnej demonstracji.
**Makiety:** `apps/web/design/F36-test-walidacja.png`, `apps/web/design/F59-ekran.png`.
**Pliki:** `apps/web/src/lib/api/client.ts`, `apps/web/src/lib/api/hooks.ts`, `apps/web/src/lib/api/index.ts`, nowy `apps/web/src/lib/api/http/klasy.ts`.
**Kroki:**
1. Uzgodnij backendowe odpowiedzi dla pięciu metod klas opisanych wyżej; uwzględnij rewizję szkicu i wersję aktywnego zestawu.
2. W centralnym kliencie HTTP dodaj parser odpowiedzi i obsługę błędu/timeout; komponenty nadal używają wyłącznie istniejących hooków API.
3. Backend musi rzeczywiście parsować kompletny YAML, sprawdzać rejestr normalizatorów, uruchomić syntetyczny PDF i zwrócić pola/dowody/wynik testu. Dopiero wtedy zastąp tekst „Test mocka” faktycznym statusem.
4. Aktywuj atomowo z oczekiwaną rewizją, kluczem idempotencji i zachowaniem poprzedniego zestawu po błędzie. Historyczne zadania muszą zachować przypięte wersje.
**Kryteria:** dodanie `numer_noty`, potem `oznaczenie_sprawy` daje rzeczywistą ekstrakcję obu pól z PDF i osobne dowody; błędny YAML pozostawia v1; nie ma zastępczego `{}`.
**Weryfikacja:** kontraktowe testy HTTP i backendu, własne testy klas, scenariusze Playwright F36/F47/F48/F55/F59 oraz `npm run build-storybook`.
**Pułapki i decyzje:** obecny mock sprawdza wyłącznie demonstracyjne reguły; sam formularz lub jego JSON nie jest dowodem ekstrakcji. Oryginały organizatora pozostają niezmienione. Licencję i region nowego API/modelu trzeba potwierdzić osobno.
**Zależności:** gotowy backend YAML/ekstrakcji; ten etap wykracza poza obecne zadanie frontendowe.

### 3. Osobny zapis szkicu przed aktywacją

**Cel:** rozdzielić aktualne „Zapisz i aktywuj wersję 2” na zapis szkicu i świadomą aktywację kompletnego zestawu.
**Makiety:** `apps/web/design/F36-test-walidacja.png`, `apps/web/design/F37-aktywacja-gotowa.png`.
**Pliki:** `apps/web/src/features/klasy/ClassDraftEditor.tsx`, `apps/web/src/features/klasy/ClassDetailView.tsx`, `apps/web/src/lib/api/{client,hooks,schemas}.ts`, `apps/web/src/lib/api/mock/klasy.ts`.
**Kroki:**
1. Dopisz `saveClassDraft(id, yaml, expectedRevision)` do centralnego API i hook mutacji; zachowaj regułę dopisywania na końcu współdzielonych plików.
2. Przycisk zapisu w ClassDraftEditor ma zapisywać dopiero poprawny, aktualnie przetestowany szkic. Dodaj ładowanie, sukces i błąd zapisu bez zamykania szkicu.
3. Aktywacja ma odnosić się do potwierdzonej zapisanej rewizji, nie do lokalnego tekstu. Zmiana tekstu unieważnia test oraz uprawnienie do aktywacji.
**Kryteria:** zapis nie aktywuje v2; błąd zapisu nie tworzy wersji; aktywacja działa wyłącznie dla zgodnej rewizji; testy obejmują zmiany podczas żądania i konflikt rewizji.
**Weryfikacja:** testy ClassDetailView i mocka, `E2E_PORT=3112 npx playwright test e2e/klasy.spec.ts --workers=2 --output=/tmp/wklasy-next-out`, typecheck/lint/Storybook.
**Pułapki i decyzje:** w aktualnym etapie operacja jest celowo połączona i uczciwie nazwana; nie zmieniaj podpisu na „Zapisz” bez rzeczywistej implementacji zapisu.
**Zależności:** punkt 2 albo kompletny, odrębnie oznaczony mock zapisu szkicu.

### 4. Numerowane wiersze i błąd przy konkretnej linii YAML

**Cel:** domknąć wizualną zgodność kodu i błędu z F21/F36.
**Makiety:** `apps/web/design/F21-yaml-odczyt.png`, `apps/web/design/F36-test-walidacja.png`.
**Pliki:** nowy `apps/web/src/components/molecules/ConfigurationCodeBlock.tsx` wraz ze stories/testem, `apps/web/src/features/klasy/ClassDraftEditor.tsx`, `apps/web/src/features/klasy/ClassDetailView.tsx`.
**Kroki:**
1. Dodaj wspólny komponent numerowanego kodu z kopiowaniem, zawijaniem i opcjonalną linią błędu; użyj Button i tokenów, bez zmiany domyślnego CodeBlock.
2. Rozdziel wizualną numerację od kopiowanej treści. Czytnik ekranu ma odczytywać kod i pojedynczy komunikat, bez powtarzania numerów.
3. Przy błędzie walidacji wyróżnij właściwą linię i powiąż komunikat z edytorem przez aria-describedby/aria-invalid.
**Kryteria:** linia 14 odpowiada faktycznej pozycji w kodzie; schowek/pobrany YAML nie zawierają numerów; działa przy 320 px i w obu motywach; brak serious/critical axe.
**Weryfikacja:** testy/stories komponentu, test ClassDetailView, E2E klas, build-storybook; nie aktualizuj istniejących baz wizualnych.
**Pułapki i decyzje:** obecny błąd jest poprawnym banerem w panelu testu; nie pokazuj dwóch identycznych alertów dla czytnika ekranu.
**Zależności:** stabilne numery linii z walidatora; w mocku istnieje deterministyczna linia 14.

### 5. Układ S07 na tablecie

**Cel:** pionowe panele na tablecie przy zachowaniu 60/40 na desktopie i dostępnej nawigacji na telefonie.
**Makiety:** `apps/web/design/F21-yaml-odczyt.png`, `apps/web/design/F36-test-walidacja.png`; dodatkowo projekt-ui.md §9.1.
**Pliki:** `apps/web/src/components/templates/TwoPane.tsx` i odpowiadające stories/test, `apps/web/src/features/klasy/ClassDetailView.tsx`.
**Kroki:**
1. Dodaj opcjonalny wariant tabletowego stosu do TwoPane; domyślny tryb wszystkich istniejących konsumentów ma zostać bez zmian.
2. Włącz wariant wyłącznie w S07; trzymaj kod szkicu i wynik testu w rodzicu, żeby przełączenie breakpointu ich nie usuwało.
3. Sprawdź układy 320/360/768/1024/1440 px oraz kolejność fokusu.
**Kryteria:** tablet pokazuje kod nad podglądem; desktop ma proporcję 60/40; zmiana rozmiaru nie gubi edycji ani wyniku testu; stary TwoPane przechodzi swoje testy i bazowe zrzuty.
**Weryfikacja:** testy TwoPane i ClassDetailView, E2E klas, build-storybook, bramka pozostałych konsumentów po zmianie biblioteki.
**Pułapki i decyzje:** obecne TwoPane przełącza na zakładki przy ≤768 px; nie zmieniaj tej granicy globalnie bez wariantu opt-in.
**Zależności:** zgoda właściciela biblioteki na zmianę istniejącego szablonu.

### 6. Fizyczne wyłączenie przycisku X podczas aktywacji

**Cel:** także wizualnie i semantycznie wyłączyć X, a nie tylko blokować jego callback.
**Makiety:** `apps/web/design/F47-aktywowanie.png`.
**Pliki:** `apps/web/src/components/organisms/ModalFrame.tsx`, `apps/web/src/components/organisms/Dialog.tsx`, `apps/web/src/features/klasy/ClassActivation.tsx` i ich testy/stories.
**Kroki:**
1. Dodaj opcjonalny prop `closeDisabled`, domyślnie false, do bibliotecznego kontraktu modalu.
2. Zablokuj X i Esc podczas oczekiwania, zachowaj pułapkę fokusu i przywrócenie fokusu po rzeczywistym zamknięciu.
3. ClassActivation przekazuje pending; istniejący lock żądania pozostaje.
**Kryteria:** w F47 wszystkie akcje zamknięcia są wyłączone, po błędzie znów działają; jedno żądanie aktywacji po podwójnym kliknięciu; testy innych dialogów bez regresji.
**Weryfikacja:** test ModalFrame/Dialog/ClassDetailView, E2E aktywacji, build-storybook i axe w obu motywach.
**Pułapki i decyzje:** obecnie zamknięcie już jest skutecznie blokowane przez onClose; nie usuwaj tego zabezpieczenia przed wdrożeniem nowego propa.
**Zależności:** właściciel biblioteki; poza pierwotnym zakresem edycji istniejących organizmów W-KLASY.

### 7. Strona wersji po nieudanej aktywacji

**Cel:** po zamknięciu dialogu pokazać błąd i nieaktywną wersję v2 wraz z aktywną v1.
**Makiety:** `apps/web/design/F48-blad-aktywacji.png`.
**Pliki:** `apps/web/src/features/klasy/ClassActivation.tsx`, `apps/web/src/features/klasy/ClassDetailView.tsx`, `apps/web/src/lib/api/schemas.ts`.
**Kroki:**
1. Zachowaj bieżący błąd w dialogu; po świadomym zamknięciu pokaż Banner oraz listę wersji z useClassVersions w panelu Test.
2. Składaj wersje z Card/Badge lub DataTable; „Ponów” uruchamia tę samą wersję, bez zmiany historycznych wyników.
3. Rozszerz odpowiedź API tylko o rzeczywiście przekazany powód nieaktywności; nie przypisuj awarii sieci błędnemu normalizatorowi.
**Kryteria:** po błędzie v1 nadal aktywna, v2 nieaktywna; zamknięcie dialogu nie ukrywa wyniku operacji; ponowienie kończy się potwierdzeniem albo kolejnym błędem.
**Weryfikacja:** własne testy klas i E2E z `NEXT_PUBLIC_MOCK_CLASS_SCENARIO=activation-error`; oba motywy/projekty i axe.
**Pułapki i decyzje:** automatyczne zamknięcie dialogu po błędzie jest zabronione; obecna implementacja słusznie pozostawia go otwartego.
**Zależności:** brak backendowego szczegółu nieaktywnej wersji; teksty muszą odpowiadać faktycznej odpowiedzi.

### 8. Rzeczywiste przypięcia zadań w podsumowaniu aktywacji

**Cel:** druga karta „Zadania i wyniki” z faktycznymi przypiętymi wersjami, zamiast obecnego objaśnienia zasad.
**Makiety:** `apps/web/design/F55-aktywacja-zakonczona.png`.
**Pliki:** `apps/web/src/features/klasy/ClassActivation.tsx`, `apps/web/src/lib/api/{schemas,client,hooks}.ts`, `apps/web/src/lib/api/mock/klasy.ts`.
**Kroki:**
1. Dodaj centralne API/hook odczytujące identyfikator zadania, przypięty zestaw i wersję zapisanego wyniku; UI nie może tego wywnioskować z daty.
2. W podsumowaniu użyj dwóch Card w responsywnym układzie: klasy oraz rzeczywiste zadania/wyniki; brak danych pokaż jako EmptyState, awarię jako ErrorState.
3. Testem obejmij zadanie uruchomione na v1 przed aktywacją i nowe zadanie na v2.
**Kryteria:** stary wynik nadal wskazuje v1 i nie jest przeliczany; nowe zadanie wskazuje v2; żadna wymyślona historia nie pojawia się w produkcyjnym UI.
**Weryfikacja:** test kontraktu API i ClassActivation, E2E F55, typecheck/lint/Storybook/axe.
**Pułapki i decyzje:** obecny Banner opisuje regułę, nie potwierdza wykonania rzeczywistych zadań; nie zmieniaj go w fikcyjne rekordy.
**Zależności:** punkt 2 i wersjonowanie zadań po stronie backendu/W-DOKUMENT.

### 9. Aktywne definicje na liście po demonstracyjnej zmianie

**Cel:** lista klas ma pokazywać także demonstracyjne siódme pole przelewu po aktywacji v2, przy zachowaniu niezmienionych oficjalnych kontraktów.
**Makiety:** `apps/web/design/F20-ekran.png`, `apps/web/design/F55-aktywacja-zakonczona.png`.
**Pliki:** `apps/web/src/features/klasy/ClassesView.tsx`, `apps/web/src/lib/api/{client,hooks,schemas}.ts`, `apps/web/src/lib/api/mock/klasy.ts`.
**Kroki:**
1. Rozdziel listę bazowych kontraktów (`DocumentClass`, v1) od listy aktywnej konfiguracji (`ClassDetail`, dowolna wersja). Dodaj `listActiveClassDefinitions` i hook albo rozdziel kartę do komponentu czytającego istniejący useClassDetail.
2. Po aktywacji unieważnij listę aktywnych definicji i pokaż rzeczywistą liczbę pól oraz reguły tej samej wersji; użyj ConfigurationFieldList i Card.
3. Zachowaj identyczny DOM/styl dla domyślnej v1. Testuj aktywację → powrót na listę → rozwinięcie pól → pole oznaczenie_sprawy.
**Kryteria:** przelew v2 ma 7 pól zarówno na liście, jak i w szczegółach; odwolanie/pelnomocnictwo zachowują swoje wersje; domyślna lista v1 ma 0 różnic po wyłączeniu celowych nowych linków.
**Weryfikacja:** ClassesView.test.tsx, test mocka, E2E klas, pełna bramka `-g klasy` z opisem nowych elementów, typecheck/lint/Storybook.
**Pułapki i decyzje:** nie rozszerzaj oficjalnego ocenianego JSON o pole demonstracyjne; istniejący documentClassSchema ma literal v1, a ClassDetail celowo rozszerza wersję osobno.
**Zależności:** właściciel API klas; bez zmian w kontraktach organizatora.
