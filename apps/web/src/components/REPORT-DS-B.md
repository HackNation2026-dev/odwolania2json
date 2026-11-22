# System design — molekuły, organizmy i szablony

Zaimplementowano warstwy współdzielonych komponentów w `apps/web/src/components`. Jedyna zmiana konsumenta to wydzielenie `SiteHeader` i `SideNav` z `AppShell`; widoki `src/features` i trasy `src/app` pozostały bez zmian. Nie wykonano commita.

## Pliki i kontrakty

Każdy publiczny komponent w poniższych tabelach ma plik `Nazwa.stories.tsx` i `Nazwa.test.tsx` obok kodu. Dostępne są również trzy pliki `index.ts`: `molecules`, `organisms`, `templates`. Atomy importowane są przez `@/components/atoms`.

### Molekuły

| Komponent | Propsy |
|---|---|
| `FormField` | `label`, `hint?`, `error?`, `required?`, `children(a11y)`; `a11y`: unikatowe `id`, `aria-describedby`, `aria-invalid`, `required` |
| `SearchBox` | natywne propsy `Input`, `label?`, `onClear?`; ustala typ `search` i powiązaną etykietę |
| `ToggleChip`, `FilterChip` | `pressed`, `count?`, pozostałe propsy `Button`; `FilterChip` jest aliasem |
| `Tabs` | `value?`, `defaultValue?`, `onValueChange?`, `children`; bez wartości początkowej wybiera pierwszą aktywną zakładkę |
| `TabList` | atrybuty `div`, `aria-label?`; strzałki lewo/prawo, Home/End, pomijanie wyłączonych zakładek |
| `Tab` | `value` i atrybuty przycisku, w tym `disabled`; `aria-selected`, roving tabindex, powiązanie z panelem |
| `TabPanel` | `value`, `children`, atrybuty `div`; ukrycie nieaktywnego panelu i etykieta zakładki |
| `SegmentedControl` | `label`, `value`, `onChange`, `options[{value,label,disabled?}]`; natywna grupa atomów `Radio` |
| `Banner` | `tone: info/success/warning/error/neutral`, `title?`, `children?`, `actions?`, `role?`; domyślnie błąd jako alert, pozostałe jako status |
| `EmptyState` | `icon?`, `title`, `description?`, `action?` |
| `ErrorState` | `title?`, `description?`, `onRetry?` |
| `LoadingState` | `label?`; spinner, tekst i szkielet |
| `SkeletonBlock` | `lines?`; szkielet ukryty przed czytnikiem |
| `ProgressBar` | `value`, `label`; ograniczenie do 0–100, ARIA progressbar i komunikat polite |
| `Stepper` | `steps[{id,label,status,description?}]`, `label?`; stany pending/running/ok/error, bieżący krok i komunikaty polite |
| `Disclosure` | `title`, `children`, natywne atrybuty `details`; `summary` z ikoną otwarcia |
| `CodeBlock` | `code`, `wrap?`, `copyLabel?`, `copyDisabled?`, `label?`; sukces i błąd schowka ogłaszane jako status |
| `KeyValueList` | `items[{key,label,value}]`; semantyczne `dl`, jawny brak danych |
| `Breadcrumbs` | `items[{label,href?}]`; ostatni element jako bieżąca strona |
| `LoadMore` | `onLoad`, `loading?`, `hasMore?`, `shown`, `total` |
| `StatTile` | `label`, `value`, `hint?` |
| `DocumentTile` | `href`, `fileName`, `className?` (nazwa klasy dokumentu), `status`, `pages`, `date?`, `codes?`, `progress?`, `thumbnail?` |
| `FieldRow` | `label`, `fieldKey`, `value`, `state: ok/missing/computed/corrected`, `active?`, `onSelect?`, `onEdit?`, `children?` |
| `EvidenceQuote` | `quote`, `page`, `source: text/ocr`, `confidence?`, `onSelect?` |
| `NavItem` | `href`, `label`, `icon?`, `active?`; Next Link z `aria-current` |
| `DropZone` | istniejące `onFiles(files,messages)`, `disabled?`; kod zachowany bez zmian, dodano stories i test |
| `ThemeToggle` | brak propsów; kod zachowany bez zmian, dodano stories i test |

`Tab`, `TabList`, `TabPanel` są implementowane wspólnie w `Tabs.tsx`, `SkeletonBlock` w `LoadingState.tsx`, a `FilterChip` w `ToggleChip.tsx`; pliki o ich nazwach przekazują eksporty. Każdy ma osobne stories i test.

### Organizmy

| Komponent | Propsy |
|---|---|
| `PageHeader` | `breadcrumbs?`, `title`, `subtitle?`, `actions?` |
| `DataTable<Row>` | `columns`, `rows`, `rowKey`, `cardTitle`, `caption`, `loading?`, `error?`, `onRetry?`, `emptyTitle?`, `sort?`, `onSortChange?`; kolumna: `key,label,render,sortValue?` |
| `FilterBar` | `query`, `onQueryChange`, `children?` (kontrolki filtrów), `onReset?`, `shown?`, `total?`, `searchLabel?` |
| `Dialog` | `open`, `onClose`, `title`, `description?`, `children`, `actions?`, `initialFocusRef?`; maks. 480 px |
| `Drawer` | jak `Dialog`; szerokość 288 px |
| `ToastRegion` | `children`; `useToast()` udostępnia `toast({title,description?,tone?}) -> id` i `dismiss(id)` |
| `PdfPagePreview` | `pages`, `page`, `onPageChange`, `pageText`, `title?`, `evidence?`, `selected?`, `onSelect?` |
| `JsonViewer` | `json: string/null`, `blocked?`, `blockReason?`; brak zastępczego `{}`, blokada schowka przy zablokowanym wyniku |
| `SiteHeader` | brak propsów; nagłówek aplikacji przeniesiony bez zmiany struktury i klas |
| `SideNav` | `pathname`; zachowane grupy i reguły aktywności, wiersze składane z `NavItem` |
| `AppShell` | istniejące `children`; używa nowych `SiteHeader` i `SideNav` |

Wewnętrzny `ModalFrame.tsx` współdzieli obsługę fokusu, Esc, portalu i blokady przewijania; testowany przez publiczne `Dialog` i `Drawer`. Obsługuje również stos otwartych okien oraz przywrócenie poprzedniej wartości `body.style.overflow`. Zapis i jego błędy obsługuje konsument; komponent nie zamyka się po renderowaniu błędu ani po kliknięciu tła. Powiadomienia pozostają do ręcznego zamknięcia.

`DataTable` pokazuje tabelę od 769 px i karty do 768 px; sortuje liczbę albo tekst po polsku przez przyciski nagłówków, a na telefonie przez osobne przyciski sortowania. Renderuje wyłącznie bieżący układ, bez powielania kontrolek, identyfikatorów i efektów.

### Szablony

| Komponent | Propsy |
|---|---|
| `AppPage` | `header`, `children` |
| `TwoPane` | `left`, `right`, `ratio?: 50/50 lub 60/40`, `mobileTabs?: [lewa etykieta,prawa etykieta]`; do 768 px zakładki, od 769 px dwie kolumny |
| `CenteredCard` | `children`, `title?`; karta maks. 480 px |
| `TextPage` | `children`, `title`, `intro?`; kolumna maks. `max-w-3xl` |

Wspólny hook `src/components/useDesktopLayout.ts` obsługuje granicę 768/769 px. SSR i środowiska bez `matchMedia` otrzymują układ desktopowy; po hydratacji odczytywany jest faktyczny rozmiar. Przy przejściu przez breakpoint `TwoPane` przełącza strukturę; stan edycji należy przechowywać u konsumenta, jeżeli musi przetrwać takie przełączenie.

## Źródła wydzielonych wzorców

Ścieżki i linie odnoszą się do zachowanych plików źródłowych. Nowe komponenty są gotowe do późniejszego refaktoru widoków; w tym zadaniu celowo nie zastępowano ich użyć w `features`.

| Źródło | Wspólne komponenty |
|---|---|
| `src/features/dokumenty-lista/FilterBar.tsx:20` | `FilterBar`, `SearchBox`, `ToggleChip/FilterChip`, `Disclosure`, `SegmentedControl` |
| `src/features/dokumenty-lista/DocumentTile.tsx:25` | `DocumentTile`, postęp dokumentu |
| `src/features/dokumenty-lista/DocumentsList.tsx:47` | `DataTable`, wariant tabeli i kart |
| `src/features/dokumenty-lista/DocumentsList.tsx:277` | `LoadingState`, `SkeletonBlock`, `EmptyState`, `ErrorState` |
| `src/features/dokument/DocumentField.tsx:10` | `FieldRow`, `EvidenceQuote`, `FormField` i połączenie etykiet oraz komunikatów |
| `src/features/dokument/DocumentEvidence.tsx:12` | `EvidenceQuote`, semantyczna tabela/karty `DataTable` |
| `src/features/dokument/DocumentPreview.tsx:7` | `PdfPagePreview`: miniatury, nawigacja strzałkami, zoom, tryb tekstu, dowody i ostrzeżenie OCR |
| `src/features/dokument/DocumentJson.tsx:5` | `JsonViewer`, `CodeBlock`: zawijanie, schowek, stan blokady i brak wyniku |
| `src/features/dodawanie/BatchProgress.tsx:18` | `ProgressBar`, `Banner`, `DataTable` |
| `src/features/klucz/SelfCheckView.tsx:35` | `Stepper`, `Banner`, stany kontroli połączenia |
| `src/features/klucz/KeyView.tsx:40` | `CenteredCard`, `FormField`, stany ładowania i błędu |
| `src/features/pulpit/DashboardView.tsx:16` | `PageHeader`, `StatTile`, `AppPage` i stany danych |
| `src/features/info/UsersView.tsx:16`, `src/features/info/EventsView.tsx:21` | `DataTable`, nagłówki, filtry i stany danych |
| `src/features/info/HowItWorksView.tsx:24` | `TextPage` |
| poprzednie `src/components/organisms/AppShell.tsx` | `SiteHeader`, `SideNav`, `NavItem`; rzeczywista integracja w powłoce |

## Wyniki kontroli

Końcowe komendy wykonano w `apps/web`, a weryfikację dokumentacji w katalogu repozytorium.

```text
npm run typecheck
tsc --noEmit
exit 0

npm run lint
3 problems (0 errors, 3 warnings)
exit 0

npm test
Test Files 83 passed (83)
Tests 692 passed (692)
Duration 14.71s
exit 0

python3 scripts/verify_docs.py
OK: 440 materiałów, 60 dokumentów, odnośniki lokalne i integralność źródeł.
exit 0

git diff --check
exit 0
```

Pełny log testów: `/tmp/dsb-test-final.log`. Ostrzeżenia lint dotyczą istniejących eksportów konfiguracji (`eslint.config.mjs`, `postcss.config.mjs`) i atomu `Radio` należącego do DS-A; nowe pliki DS-B nie generują ostrzeżeń.

Testy własne obejmują renderowanie stanów stories, nazwy i role, powiązanie etykiety/opisu/błędu, sterowanie zakładkami i pomijanie wyłączonych opcji, tryb kontrolowany, pułapkę fokusu, Esc, powrót fokusu i przewijania, pozostawienie formularza z wartością po błędzie, schowek i odmowę dostępu, blokadę kopiowania JSON, brak zastępczego wyniku, sortowanie tabel/kart, nawigację podglądu strzałkami i powiadomienia. Dialog i Drawer mają dodatkowe testy axe obejmujące cały `document.body`, łącznie z portalem. Zbiorczy test stories DS-A w obu motywach wchodzi w podane 692 testy i przechodzi.

Osobny, tymczasowy test porównał `renderToStaticMarkup` bieżącego `AppShell` z jego wersją z HEAD: 6/6 zaliczonych tras (`/`, `/dokumenty`, `/klasy`, `/klucz`, `/login`, `/ustawienia`), HTML identyczny znak w znak po końcowym wykorzystaniu `NavItem`. Tymczasowy kod bazowy i test usunięto po pomiarze; nie dodano kopii starej powłoki do repozytorium.

Następnie porównano także obrazy w Chromium: te same sześć tras × jasny/ciemny × szerokości 320, 768, 1440 px. Dla każdej pary render starej i nowej powłoki otrzymał ten sam aktualny arkusz CSS aplikacji; porównanie buforów PNG jest ścisłe, bez tolerancji różnicy pikseli. Sprawdzany był sam `AppShell` ze stałą treścią przykładową, bez danych widoków.

```text
E2E_PORT=3198 npx playwright test e2e/dsb-shell-parity.spec.ts --workers=2 --project=desktop
36 passed (30.0s)
exit 0
```

Wynik: 36/36 par obrazów identycznych, 72 pliki PNG w `/tmp/dsb-shell-screenshots/`; log `/tmp/dsb-shell-visual.log`. Tymczasowy test E2E i pliki bazowe usunięto; jego zadaniem była jednorazowa kontrola wydzielenia powłoki z wersji HEAD.

## Odstępstwa i granice weryfikacji

- Zbiorczy axe w jsdom nie mierzy kontrastu CSS; kolory nowych komponentów korzystają z istniejących tokenów. Kontrola PNG obejmuje powłokę, bez ponownej walidacji pełnych ekranów `features`, których nie zmieniano.
- Podgląd PDF pozostaje jawnie syntetyczny, zgodnie z istniejącym `DocumentPreview`; nie dodano renderera PDF ani nowego stosu. Współdzielony podgląd nie zależy od typu rekordu API ani arkusza CSS konkretnego widoku.
- `JsonViewer` udostępnia podgląd i kopiowanie, bez przycisku pobierania. Decyzja eksportu oraz operacje API pozostają u konsumenta; `blocked` blokuje kopiowanie, `json=null` nie jest zamieniane na `{}`.
- Komponenty nie wywołują API, nie zmieniają schematów ani mocków. Brak nowych wymagań kontraktu API, modeli, licencji lub hostingu.
- Stories oraz testy stworzono także dla zachowanych `DropZone` i `ThemeToggle`. Konfiguracja Storybooka, atomy, style globalne i tokeny pozostały poza zakresem DS-B.
