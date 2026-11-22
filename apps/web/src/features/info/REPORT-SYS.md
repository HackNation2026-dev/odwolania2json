# W-SYS — ekrany systemowe i powłoka

Bez commita. Zakres: wyłącznie W-SYS, nowe pliki jego komponentów, dopiski API i własne testy. Przeczytano `apps/web/AGENTS.md`, `REPORT-DS-B.md`, README, wymagania, pytania otwarte i sekcje przepływów dotyczące konfiguracji, dostępności oraz administracji. Obejrzano wszystkie przydzielone PNG: F04, F22, F25, F26, F29, F30, F32, F49, F56, F63, F64.

## (a) ZROBIONE

### Poprawka po odbiorze — nawigacja i licznik audytu

Zakres poprawki: `apps/web/e2e/dziennik.spec.ts`, `apps/web/src/features/info/EventsView.tsx`, `apps/web/src/features/info/EventsView.test.tsx` oraz ten raport. Przeszukano cały katalog e2e pod kątem `Główna` i `getByRole("navigation")`: tylko test dziennika i `smoke.spec.ts` używają tej nawigacji. Smoke już otwiera menu, gdy widoczny jest przycisk „Otwórz menu”, i nie wymagał kolejnej zmiany.

Test dziennika miał założenia sprzed F26: sześć wpisów z `listEvents`, brak konfiguracji i rozwijane szczegóły. Nowy widok korzysta z pięciu wpisów `listAuditEvents` w `mock/sys.ts`, w tym jednego zdarzenia aktywacji YAML; szczegóły są bezpośrednio w tabeli/kartach. Test dopasowano do tego zamierzonego zachowania: otwiera Drawer na telefonie, sprawdza zamknięcie po nawigacji, liczby 5 → 1 → 0 → 5, maskowane wartości, faktyczny pusty wynik przez filtr nieistniejącego użytkownika oraz wyczyszczenie obu filtrów. Przebieg wykonuje się w obu motywach na desktopie i telefonie; nie usunięto żadnego kryterium filtrowania lub maskowania.

Dodano dostępny, wizualnie ukryty licznik `role=status` z `aria-label="Liczba zdarzeń"`; jest obecny dopiero po udanym odczycie i nie pokazuje zastępczego zera podczas ładowania/błędu. Stała informacja E3 ma teraz semantykę `note`, a nie komunikatu live. Selektor testu wybiera status po jednoznacznej nazwie, niezależnie od ładowania, eksportu i pustego stanu. Jednostkowy test weryfikuje nazwany licznik dla 5, 1 i 0 wpisów. Brak zmian API, mockowych danych, widocznego układu lub progu wizualnego.

Kontrole poprawki (logi `/tmp/wsys-fix-*.log`, kody wyjścia w odpowiadających `.status`):

```text
npm run typecheck
tsc --noEmit
exit 0

npm run lint
3 problems (0 errors, 3 warnings)
exit 0

npm test -- --maxWorkers=2
Test Files 107 passed (107)
Tests 827 passed (827)
Duration 76.58s
exit 0

npm run build-storybook -- --output-dir /tmp/wsys-fix-storybook
Vite built in 10.76s
Storybook build completed successfully
exit 0

E2E_PORT=3114 npx playwright test e2e/dziennik.spec.ts e2e/smoke.spec.ts e2e/klucz.spec.ts --workers=2 --output=/tmp/wsys-fix-out
84 passed (2.0m)
exit 0
```

Dodatkowe `python3 scripts/verify_docs.py` po poprawce zgłosiło brakujące odnośniki w cudzym `docs/00-organizacja/zadania-gui.md` (m.in. `zadania-dla-agentow.md`, `backlog.md`, `ADR-003-lokalne-ci-cd.md`). Nie edytowano tej dokumentacji; przekazano wynik koordynatorowi. `git diff --check` przechodzi. Port 3114 sprawdzono przed testami i po ich zakończeniu; jest wolny. Usunięto wyłącznie automatycznie dodane przez własny serwer wpisy `.next-e2e-3114` z konfiguracji TypeScript.

### Pliki i zmiany

- Powłoka: `src/components/organisms/{AppShell,SiteHeader,SideNav}.tsx`; nowe `AppShellMobileMenu` oraz `AppShellPreferences`, każde z historią Storybook i testem. Menu wykorzystuje Drawer 288 px, pułapkę fokusu i powrót fokusu; pierwszym fokusem jest „× Zamknij menu”. Link nagłówka prowadzi do `/gotowosc`. Desktop zachowuje wygląd powłoki.
- `src/features/klucz/{KeyView,SelfCheckView,LoginView}.tsx` i `KeyView.test.tsx`: Card/Input, wielowierszowy JSX, zachowane teksty, rozmiary i zachowanie klucza. Logowanie nadal jest wyłącznie ekranem „po MVP”.
- `src/features/ustawienia/{SettingsView,Preferences,ProcessingSettings,RetentionForm}.tsx`, `SettingsView.test.tsx`: preferencje lokalne, ograniczenie animacji, gęstość tabel desktopowych, wyłączenie skrótu `?`, model tylko do odczytu, zakres retencji z API, powiązany błąd pola, dialog potwierdzenia i komunikaty zapisu.
- `src/features/info/{EventsView,UsersView,UserRoleDialog,HowItWorksView,SystemInfoCard,ReadinessView,AccessibilityView}.tsx` i testy: filtry i CSV, podgląd ról/zakresu, legenda pięciu braków i pokrycia, gotowość, dostępność.
- Nowe trasy `src/app/{dostepnosc,gotowosc}/page.tsx`, `src/app/uzytkownicy/brak-dostepu/page.tsx`; `src/app/{error,forbidden}.tsx`. Testy 500/403: `src/features/info/ErrorPages.test.tsx`.
- `src/lib/api/{schemas,client,hooks}.ts`: wyłącznie dopisany kontrakt systemowy; `src/lib/api/mock/sys.ts` i `sys.test.ts`; w `mock/client.ts` import oraz jeden wiersz integracji. Pozostałe równoległe zmiany tych plików należą do innych wykonawców.
- `e2e/smoke.spec.ts`: nawigacja przez menu telefonu, motyw po ponownym otwarciu menu, przepływy retencji/CSV/ról/informacji, oba motywy i axe. Filtr znanego anulowania PDF pozostawiono zgodnie z treścią dostarczoną przez W-DOC.

Użyte elementy biblioteki: Button, Input, Select, Checkbox, Card, Badge, StatusBadge, Banner, FormField, LoadingState, ErrorState, EmptyState, KeyValueList, Drawer, Dialog, DataTable, PageHeader, AppPage i TextPage. Nie zmieniono domyślnych stylów istniejących atomów, tokenów ani globalnego CSS. Dostosowanie Input na starych ekranach zachowuje dotychczasowe wysokości, typografię i przezroczystość.

### Makieta → implementacja

| Makieta | Realizacja i odstępstwa |
| --- | --- |
| F04 | Drawer 288 px, fokus „Zamknij menu”, pełna nawigacja, dostępność i motyw. Zachowany dodatkowy standardowy przycisk „Zamknij” z Drawer. Brak PL/EN, ponieważ EN wyłączono z tej rundy. Na telefonie nagłówek pokazuje menu, nazwę i przycisk „＋”. |
| F22 | Sześć dotychczasowych etapów zachowano; dodano legendę pięciu powodów braku i opis pokrycia/diagnozy. Dłuższa treść objaśniająca wariant A, statusy i kartę modeli pozostaje dostępna poniżej kart. |
| F25 | Zachowana tabela, dodano wyszukiwanie i dostępny dialog ról, zakresu oraz flagi danych osobowych. Edycja to jawny podgląd E3; zapis, dodawanie i blokowanie kont pozostają niedostępne bez backendu i logowania. |
| F26 | Filtry rodzaju, użytkownika, dat od/do i obiektu, pięć syntetycznych wpisów, maskowane Było/Jest, odsłonięcie bez wartości w logu, rzeczywiste pobieranie CSV. Data od/do to dwa jednoznacznie opisane pola. Standardowy DataTable daje bardziej przestronny układ i karty telefonu niż PNG. |
| F29 | Preferencje, dostępność, model do odczytu i retencja. Natywne Select zamiast segmentów; język tylko PL. Zachowano istniejącą sekcję klucza. Błąd nie jest pokazany od razu: pojawia się po próbie zapisu błędnej liczby. Retencja to jawna symulacja bez usuwania plików. |
| F30 | Cel WCAG 2.1 AA, brak audytu, ograniczenia PDF/OCR, jawny brak kontaktu i powrót do analizy. Treść statyczna działa bez API; nie wymyślono kontaktu ani daty audytu. |
| F32 | 500, komunikat, bezpieczny digest jako ID zdarzenia, ponowienie odczytu i nowa analiza; bez treści błędu/stack trace. Gdy runtime nie przekaże digestu, pokazany jest jawny brak identyfikatora i prośba o czas zdarzenia. Obsługiwane aktualne `retry` oraz dotychczasowe `reset`. |
| F49 | Widok 403 bez obiektu, powrót do spraw. Jawna trasa demonstracyjna: `/uzytkownicy/brak-dostepu`; sam `forbidden.tsx` pozostaje gotowym ekranem przerwania autoryzacji. Nie dodawano backendowej kontroli dostępu. |
| F56 | `/gotowosc`, komplet metadanych modeli/OCR, największy model, licencje/wagi, kraje firmy i serwera, rewizja kontraktu. Nie powielono niezweryfikowanych deklaracji gotowości z PNG: nieznane dane są jawne, a kontrola oznaczona jako symulacja. |
| F63/F64 | Wygląd i działanie zachowane; refaktor na Card/Input. Nie dodano nowych wariantów funkcjonalnych. |

### Walidacja

Końcowe logi jednostkowe i kontroli: `/tmp/wsys-{unit,typecheck,lint,storybook}-final.log`. E2E: `/tmp/wsys-smoke-complete.log`, status `/tmp/wsys-smoke-complete.status` = 0. Bramka: `/tmp/wsys-visual-final.log`, artefakty `/tmp/wsys-final-out`. Dokumentacja: `/tmp/wsys-docs.log`.

```text
npm run typecheck
tsc --noEmit
exit 0 (potwierdzone /tmp/wsys-typecheck-final.status)

npm run lint
3 problems (0 errors, 3 warnings)
exit 0

npx vitest run src/features/info src/features/klucz src/features/ustawienia src/components/organisms/AppShellMobileMenu.test.tsx src/components/organisms/AppShellPreferences.test.tsx src/components/organisms/AppShell.test.tsx src/components/organisms/SiteHeader.test.tsx src/components/organisms/SideNav.test.tsx src/lib/api/mock/sys.test.ts --maxWorkers=2
Test Files 15 passed (15)
Tests 33 passed (33)
Duration 55.76s
exit 0

npm run build-storybook -- --output-dir /tmp/wsys-storybook
Output directory: /tmp/wsys-storybook
Storybook build completed successfully
exit 0

E2E_PORT=3114 npx playwright test e2e/smoke.spec.ts -g "W-SYS|/ustawienia|/dziennik|/uzytkownicy|/jak-to-dziala|persists ThemeToggle" --workers=2 --output=/tmp/wsys-smoke-complete-out
42 passed (2.2m)
exit 0

E2E_PORT=3114 npx playwright test e2e/visual.spec.ts -g "klucz|kontrola|login|ustawienia|jak-to-dziala|uzytkownicy|dziennik|nie-znaleziono" --workers=2 --output=/tmp/wsys-final-out
24 failed
8 passed (4.6m)
exit 1 — wyłącznie opisane poniżej celowe różnice

python3 scripts/verify_docs.py
OK: 440 materiałów, 62 dokumentów, odnośniki lokalne i integralność źródeł.
exit 0

git diff --check
exit 0
```

Ostrzeżenia lint dotyczą istniejących `eslint.config.mjs`, `postcss.config.mjs` i atomu Radio. Nie dodano nowych ostrzeżeń. Uruchomiono także Storybook dev na 6114; obejrzano historię Drawer (`/tmp/wsys-story-Drawer.png`) oraz przeczytano historie DataTable, FormField i CenteredCard.

Bramka: desktop `klucz`, `kontrola`, `login`, `nie-znaleziono` przechodzi w obu motywach (8/8). Desktop `jak-to-dziala` różni się dodaną legendą; `ustawienia` preferencjami/modelem/retencją; `uzytkownicy` filtrem i aktywnym podglądem; `dziennik` filtrami, nowymi wpisami i CSV (8 celowych różnic). Wszystkie osiem tras telefonu różni się wymaganą zmianą powłoki F04, dodatkowo powyższe cztery mają nową treść (16 celowych różnic). Obejrzano wszystkie 24 końcowe pliki `*-diff.png` przez narzędzie obrazu. Baza i próg 0.002 pozostały bez zmian.

Dodatkowe ścisłe porównanie PNG dla starego desktopu (`/tmp/wsys-parity-result.log`): kontrola i login po 0 pikseli w obu motywach; klucz 14/13, strona nieznaleziona 15/20 pikseli w jasnym/ciemnym, w obszarze nagłówka i drobnych krawędzi tekstu. Bramka referencyjna przechodzi; nie deklaruję pełnej identyczności każdego piksela poza jej tolerancją. Nie wprowadzono zmian w wyglądzie tych starych widoków.


Pierwszy szeroko równoległy przebieg miał przeładowanie HMR i przekroczenia limitów czasu; po ustabilizowaniu kodu testy powtórzono. Nie zmieniono bazy obrazów ani progu. Polecenie globalne `npm test` uruchomiono; przy dużym obciążeniu przerwano je, następnie uruchomiono `npm test -- --maxWorkers=2`. Ten przebieg zgłosił awarie cudzych `ClassDetailView`, `DocumentsList` i `DocumentPageText`. Koordynator polecił pozostawić te pliki ich wykonawcom i rozlicza pełny zestaw po integracji. Własny końcowy zestaw jest niezależny od tych awarii.

### Granice i API

- Trwała retencja, usuwanie spraw, autoryzacja, edycja kont i audyt produkcyjny wymagają backendu. Mock nie wykonuje ekstrakcji ani nie potwierdza dostawcy, regionu lub licencji. Nie dodano kluczy do pamięci przeglądarki ani logów.
- Gęstość zmniejsza odstępy tabel wyłącznie na desktopie; cele dotykowe telefonu pozostają bez zmian. Przełącznik skrótów blokuje istniejący wzorzec `?`; nowe jednoklawiszowe skróty innych modułów powinny respektować `html[data-single-key-shortcuts=off]`.
- Statyczne ekrany dostępności i odmowy dostępu nie mają stanów pustego wyniku/ładowania API. Pozostałe odczyty mają loading/error/empty/success odpowiednio do domeny; błędy zapisu pozostawiają dialog otwarty.
- Brak audytu WCAG pozostaje prawdziwym komunikatem. Automatyczne axe oraz reflow nie zastępują audytu z czytnikiem ekranu i powiększeniem 400%.
- Retencja nie ma jeszcze okna ochrony szkicu przy nawigacji wewnętrznej; zapis wymaga jawnego potwierdzenia.
- Proponowane endpointy: `GET /settings/retention`, `PUT /settings/retention` (zakres i liczba spraw do usunięcia z serwera), `GET /audit-events` (filtry, maskowanie w serwerze), `GET /audit-events/export.csv`, `GET /system/readiness` spójny z `GET /system/info`. Zarządzanie rolami i autoryzacja wymagają osobnego kontraktu E3; nie dodano fikcyjnego zapisu.

## (b) DO ZROBIENIA

Poniższe zadania są poza zakończonym etapem. W produkcyjnym kodzie nie pozostawiono eksperymentalnych tras ani fikcyjnych zapisów uprawnień. Ścieżki w raporcie są względem katalogu głównego repozytorium.

### Ścisła deterministyczność pojedynczych pikseli desktopu

**Cel:** ustalić przyczynę 13–20 pikseli różnicy dodatkowego pomiaru, mimo przechodzącej niezmienionej bramki Playwright.
**Makiety:** `apps/web/design/F63-brak-klucza.png`, `apps/web/design/F64-kontrola.png`; referencją regresji są istniejące PNG poza Git w `apps/web/e2e/visual.spec.ts-snapshots`.
**Pliki:** w razie potrzeby nowy `apps/web/e2e/wsys-parity.spec.ts`; analizuj `apps/web/src/components/organisms/SiteHeader.tsx`. Nie edytuj baz ani progu istniejącego testu.
**Kroki:**
1. Odtwórz dokładne warunki `visual.spec.ts` (1440×900, oba motywy, fonty, ukryte narzędzia Next i caret, wyłączone animacje); zapisz dodatkowe PNG do `/tmp`.
2. Porównaj z bazą bez tolerancji. Punkt wyjścia: `/tmp/wsys-parity-result.log`; różnice klucza są w obszarze x1082–1105/y8–46, nieznalezionej strony x311–1106/y8–142.
3. Rozróżnij zmianę układu od krawędzi fontu/natywnego selecta i stanu fokusu; popraw kod tylko po potwierdzeniu rzeczywistej regresji. Nie „naprawiaj” wyniku przez podmianę obrazów lub zwiększenie progu.
**Kryteria:** 8/8 dotychczasowych desktopowych porównań nadal przechodzi; ścisły pomiar daje 0 albo protokół wykazuje odtwarzalną niedeterministyczność samej procedury porównania.
**Weryfikacja:** `E2E_PORT=3114 npx playwright test e2e/visual.spec.ts -g 'klucz|kontrola|login|nie-znaleziono' --project=desktop --workers=2 --output=/tmp/wsys-out`; dodatkowe porównanie RGB bez tolerancji.
**Pułapki/decyzje:** kontrola i login już dają dokładnie 0 w obu motywach. Bramka ma zastany próg 0.002 i nie był on zmieniany. Zmiany mobilne F04 są celowe, nie należą do tej analizy.
**Zależności:** stabilne fonty, Chromium i stan procesu deweloperskiego; brak zależności od backendu.

### Ochrona niezapisanego szkicu retencji

**Cel:** ostrzegać o utracie zmienionej liczby dni przy opuszczaniu ustawień.
**Makiety:** `apps/web/design/F29-ustawienia.png`; opis S11 w `docs/04-architektura/gui/projekt-ui.md`.
**Pliki:** edytuj `apps/web/src/features/ustawienia/RetentionForm.tsx`, `apps/web/src/features/ustawienia/SettingsView.test.tsx`, `apps/web/e2e/smoke.spec.ts`; nowy wspólny wzorzec ochrony nawigacji umieść w `apps/web/src/components/organisms/UnsavedRetentionDialog.tsx` z `.stories.tsx` i `.test.tsx`.
**Kroki:**
1. Wylicz dirty z wartości pola oraz `useRetentionSettings().data.days`; po udanym `useSaveRetention` usuń dirty.
2. Dodaj `beforeunload` tylko dla dirty i przechwyć wewnętrzną nawigację poza formularz; użyj bibliotecznego Dialog, z akcjami „Zostań” i „Odrzuć zmiany”.
3. Przechowaj zamiar nawigacji, wykonaj go dopiero po odrzuceniu; przy anulowaniu przywróć fokus. Nie otwieraj dialogu dla niezmienionej lub zapisanej wartości.
4. Dodaj jednostkowe i e2e dla anulowania, odrzucenia, zapisu i odświeżenia, w obu motywach i na telefonie.
**Kryteria:** edycja 30→60 i kliknięcie „Sprawy” otwiera potwierdzenie; „Zostań” zachowuje 60; zapis usuwa ostrzeżenie. Walidacja 1–365 nadal jest związana z polem i pochodzi z API.
**Weryfikacja:** `cd apps/web && npm run typecheck && npm run lint`; własny Vitest formularza; `E2E_PORT=3114 npx playwright test e2e/smoke.spec.ts -g 'W-SYS' --workers=2 --output=/tmp/wsys-out`; `npm run build-storybook`.
**Pułapki/decyzje:** nie stosuj globalnego nieodwracalnego blokowania historii; Dialog ma przywracać fokus, błąd zapisu nie zamyka potwierdzenia. Nie zmieniaj starego wyglądu Card/Input.
**Zależności:** docelowy wspólny mechanizm ochrony szkiców, jeżeli powstanie dla korekt dokumentów; bez zależności od backendu.

### Pełne zarządzanie rolami E3

**Cel:** zastąpić jawny podgląd rzeczywistą administracją dopiero po dostarczeniu autoryzacji.
**Makiety:** `apps/web/design/F25-ekran.png`, `apps/web/design/F49-403.png`.
**Pliki:** `apps/web/src/features/info/{UsersView,UserRoleDialog}.tsx`, `UsersView.test.tsx`, dopiski w `apps/web/src/lib/api/{schemas,client,hooks}.ts`, `apps/web/src/lib/api/mock/sys.ts`, `sys.test.ts`, `apps/web/e2e/smoke.spec.ts`; kontrakt serwerowy w `packages/contracts` musi być uzgodniony przed implementacją.
**Kroki:**
1. Uzgodnij serwerowy kontrakt tworzenia konta, ról, zakresu spraw i uprawnienia danych osobowych; dodaj hooki zapisu, zaproszenia i blokady wyłącznie przez warstwę API.
2. Rozbuduj Dialog o FormField/Input/Checkbox/Select i walidację; obsłuż loading, błąd pozostawiający formularz, zapis i ponowny odczyt listy.
3. Zaimplementuj ochronę ostatniego administratora oraz kontrolę uprawnień na backendzie; odmowa 403 nie może ujawniać istnienia obiektu ani jego treści.
4. Dodaj maskowany audyt zmian ról oraz testy izolacji zakresów. Dopiero wtedy aktywuj obecne wyłączone akcje.
**Kryteria:** zmiana roli przeżywa ponowne wczytanie; odebranie ostatniego administratora jest odrzucone; anulowanie nie zmienia danych; 403 nie ujawnia dokumentu; axe bez serious/critical.
**Weryfikacja:** Vitest obu widoków i `sys.test.ts`; `npm run typecheck && npm run lint && npm run build-storybook`; własne smoke desktop/phone w obu motywach.
**Pułapki/decyzje:** obecny przycisk „Zapisz (po MVP)” jest celowo wyłączony. Nie zastępuj autoryzacji lokalnym stanem ani localStorage. Logowanie pozostało poza tą rundą.
**Zależności:** backend kont, sesji, uprawnień i audytu; decyzje E3. To nie jest zadanie do wykonania wyłącznie przez zmianę mocka.

### Retencja i audyt na rzeczywistym serwerze

**Cel:** zastąpić stan pamięci mocka kontrolowanym usuwaniem i trwałym dziennikiem.
**Makiety:** `apps/web/design/F29-ustawienia.png`, `apps/web/design/F26-audyt.png`.
**Pliki:** `apps/web/src/lib/api/{schemas,client,hooks}.ts`, `apps/web/src/lib/api/mock/{sys,sys.test}.ts`, `apps/web/src/features/ustawienia/RetentionForm.tsx`, `apps/web/src/features/info/EventsView.tsx` i testy; docelowa implementacja HTTP musi pozostać w `apps/web/src/lib/api/`.
**Kroki:**
1. Uzgodnij endpointy z części API raportu oraz kontrakt podglądu liczby spraw do usunięcia dla wybranej liczby dni.
2. Pobieraj min/max i podgląd z serwera; zapis wymaga Dialog. Serwer ma sprawdzać rolę, zakres i zasadność wartości.
3. Izoluj sesje i usuń pliki/artefakty w cyklu retencji; zapisuj zdarzenie bez wrażliwych wartości. Lista i CSV mają korzystać z tego samego zakresu/maskowania.
4. Sprawdź walidację po stronie serwera, anulowanie, błąd, ponowienie, eksport CSV i odporność na wstrzyknięcie formuł dla przyszłych niesyntetycznych tekstów.
**Kryteria:** ustawienie przeżywa restart; zmiana obejmuje istniejące sprawy według zatwierdzonej polityki; użytkownik spoza zakresu nie dostaje wpisów/CSV; Było/Jest i odsłonięcia nie ujawniają danych w dzienniku.
**Weryfikacja:** testy kontraktu i backendu; własny Vitest + smoke W-SYS desktop/phone/oba motywy; typecheck, lint, Storybook i bramka bez zmiany baz.
**Pułapki/decyzje:** aktualny mock jest jawnie syntetyczny, ma 1–365 dni i `affectedCases=0`; nie przedstawiaj tego jako działającego usuwania. CSV nie jest ocenianym JSON-em i nie zmienia wariantu A.
**Zależności:** backend magazynu dokumentów, polityka retencji i autoryzacja E3.

### Kontakt, audyt dostępności i identyfikatory incydentów

**Cel:** uzupełnić dane operacyjne wyłącznie zweryfikowaną konfiguracją i wykonać brakujące ręczne kontrole.
**Makiety:** `apps/web/design/F30-dostepnosc.png`, `apps/web/design/F32-500.png`, `apps/web/design/F56-gotowosc.png`.
**Pliki:** `apps/web/src/features/info/{AccessibilityView,ReadinessView,SystemInfoCard}.tsx`, `apps/web/src/app/error.tsx`, ich testy i `apps/web/e2e/smoke.spec.ts`; nowe metadane dopisuj w `apps/web/src/lib/api/{schemas,client,hooks}.ts`.
**Kroki:**
1. Uzgodnij niesekretny kontakt oraz publikowaną datę/zakres audytu; strona dostępności musi zachować statyczną treść przy awarii API.
2. Zweryfikuj model, licencję, wagi oraz kraje firmy i serwera w źródłach; dopiero wtedy zmień status niepotwierdzony. HTTP 200 nie wystarcza.
3. Backend ma przekazywać bezpieczny identyfikator incydentu. Dodaj izolowany test e2e prawdziwej granicy 500 z retry/reset; nie dodawaj publicznej trasy wyrzucającej błąd ani stack trace.
4. Wykonaj kontrolę czytnikiem ekranu, tekstem 200%, powiększeniem 400% i klawiaturą ekranową. Wynik audytu publikuj dopiero po jego wykonaniu.
**Kryteria:** brak fikcyjnego kontaktu i deklaracji zgodności; bezpieczne ID łączy zgłoszenie z incydentem; test granicy 500 ponawia tylko odczyt, nie analizę; modele/OCR zachowują pełne metadane i flagę shim.
**Weryfikacja:** testy `AccessibilityView`, `ReadinessView`, `ErrorPages`; izolowany e2e 500; smoke W-SYS z axe; ręczny protokół reflow/klawiatury; typecheck i lint.
**Pułapki/decyzje:** aktualnie poprawnie wyświetlane są „Kontakt nie został skonfigurowany”, „Nie przeprowadzono audytu” i jawny brak digestu, gdy runtime go nie dostarczy. Nie zastępuj nieznanych danych arbitralnymi wartościami.
**Zależności:** zespół kontaktowy/audytujący, backend incydentów i zatwierdzona konfiguracja modeli; frontend może pozostać statyczny przy ich braku.
