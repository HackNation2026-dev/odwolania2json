# W3 — lista dokumentów

Wdrożono `/dokumenty`: galerię, tabelę przechodzącą w karty na telefonie, filtrowanie, sortowanie, rozmiary S/M/L, wczytywanie kolejnych ośmiu rekordów, ponowienie błędnych analiz oraz stany ładowania, pustej sesji, pustego wyniku i błędu API. Kafelki prowadzą do przeglądu dokumentu; miniatury są wektorowymi atrapami. Próg galerii wynosi siedem dokumentów całej sesji, niezależnie od filtrów; URL ma pierwszeństwo przed zapamiętanym widokiem, a dostęp do localStorage jest chroniony try/catch.

## Pliki zadania

- `src/app/dokumenty/page.tsx`
- `src/features/dokumenty-lista/DocumentsList.tsx`
- `src/features/dokumenty-lista/DocumentTile.tsx`
- `src/features/dokumenty-lista/FilterBar.tsx`
- `src/features/dokumenty-lista/filters.ts`
- `src/features/dokumenty-lista/DocumentsList.test.tsx`
- `src/features/dokumenty-lista/filters.test.ts`
- `e2e/dokumenty-lista.spec.ts`
- `src/features/dokumenty-lista/REPORT.md`

Nie zmieniano fundamentu, kontraktu API ani podtrasy `[id]`; bez commita. Zapytania wykonują istniejące hooki `useDocuments`, `useClasses` i `useRetryDocument`. Filtrowanie i sortowanie odbywają się w funkcji czystej na pobranej kolekcji; statusy i kody łączone są przez OR wewnątrz grupy oraz AND między grupami. Parametry wymagane zadaniem: `q`, powtarzany `status` (akceptowany także zapis z przecinkami), `klasa`, `sort`, `widok`; dodatkowe elementy makiet używają `source`, `kod`, `uwaga`.

## Makieta → implementacja

- F06g/F67/F68/F69, „Akta zbiorcze 2026”, 24 dokumenty i konfiguracja klas v1 → „Dodane dokumenty”, liczba z API i „bieżąca sesja”; kontrakt nie udostępnia nazwy sprawy ani wersji konfiguracji.
- Nazwy, klasy, kody i liczby z FigCraft → rzeczywiste dane syntetyczne istniejącego mocka; bez dopisywania rekordów do fundamentu.
- Wyszukiwanie po pliku, NIP i numerze postępowania → wyszukiwanie po nazwie pliku zgodnie z W3 i kontraktem; placeholder nie obiecuje nieobsługiwanych pól.
- F68 dwie osobne pozycje „Wymaga uwagi najpierw” i „Status” → jedna pozycja „Wymaga uwagi najpierw / Status”, domyślna; obie oznaczałyby tę samą kolejność stanów. Pozostałe opcje z makiety są dostępne, w tym nazwa Z–A i liczba braków.
- Dropdown sortowania i klasy → natywne selecty, zachowujące semantykę oraz obsługę telefonu i klawiatury; status ma panel z checkboxami, liczbami, „Wyczyść” i „Zastosuj”.
- F06 pełna nazwa pliku wynikowego → nazwa dla pełnego/obcego dokumentu, dla pozostałych jawny brak zatwierdzonego wyniku; to metadane, bez przycisku pobierania omijającego decyzję eksportu.
- Nagłówek, boczna nawigacja, stopka i statusy → istniejące AppShell i StatusBadge zgodnie z zakazem zmian fundamentu; różnice powłoki są poza W3.
- Desktopowe kontrolki FigCraft → zawijanie na telefonie, cele dotykowe 44 px i brak przewijania poziomego przy 320 px; tabela przechodzi w karty.

## Ograniczenia kontraktu

Nie dodawano metod ani pól API. Źródło tekstu jest wyznaczane z istniejących dowodów; brak dowodów oznacza brak rozpoznanego źródła. Kody pochodzą z `reasons` i `errorCode`, ponieważ kontrakt nie udostępnia osobnego katalogu odstępstw ani audytu. Nazwy plików wynikowych nie są deklaracją dopuszczalności pobierania — ten widok nie pobiera JSON.

## Weryfikacja

Testy własne: 7 testów parsowania/serializacji i integracji z prawdziwym mockiem. E2E obejmuje status, wyszukiwanie, sortowanie, zapis widoku, wejście do `/dokumenty/doc-1`, link pulpitu, pusty wynik i 320 px oraz axe w obu widokach i obu motywach na desktopie i telefonie. Globalne testy obejmują też równoległe zadania.

Końcówki wyników:

```text
npm run typecheck
> tsc --noEmit
kod 0

npm run lint
✖ 2 problems (0 errors, 2 warnings)
kod 0; ostrzeżenia dotyczą istniejących eksportów konfiguracji ESLint/PostCSS

npm test
Test Files  16 passed (16)
Tests       84 passed (84)

npx vitest run src/features/dokumenty-lista
Test Files  2 passed (2)
Tests       7 passed (7)

E2E_PORT=3103 npx playwright test e2e/dokumenty-lista.spec.ts --output=/tmp/w3-e2e-settled
8 passed (38.3s)

python3 scripts/verify_docs.py
OK: 440 materiałów, 60 dokumentów, odnośniki lokalne i integralność źródeł.
```

Pierwsze uruchomienie E2E wymagało instalacji Chromium; kolejne ujawniło i pozwoliło naprawić wyścig aktualizacji URL oraz zawijanie sortowania. Wyniki Playwright zapisano poza współdzielonym `test-results`, ponieważ równoległe zadania usuwały wzajemnie artefakty. Jeden przebieg podczas Fast Refresh przerwał nawigację do dokumentu; po zakończeniu zmian pełny przebieg przeszedł.

Oceniono zrzuty renderu: `/tmp/w3-gallery-final.png` i `/tmp/w3-table.png`. Oryginały FigCraft pozostały bez zmian.
