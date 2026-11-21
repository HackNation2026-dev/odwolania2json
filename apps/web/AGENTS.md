# apps/web: zasady dla wykonawców

Frontend Odwołania2JSON: Next.js 16 (App Router), React 19.3, TypeScript strict, Tailwind 4, TanStack Query. **Bez backendu**: dane z mocka w `src/lib/api/mock`. Pisz po polsku (teksty UI i komentarze), nazwy testów po angielsku.

## Twarde reguły

1. **Jedno miejsce wywołań API**: `src/lib/api`. Komponenty używają wyłącznie hooków z `@/lib/api/hooks`. Zakaz `fetch` poza `src/lib/api` (reguła ESLint). Brakuje metody? Dopisz do `ApiClient` + mocka + testu i opisz w raporcie.
2. **Atomic design**: `src/components/{atoms,molecules,organisms,templates}`. Atom nie zna API ani routingu. Strony w `src/app/**/page.tsx` są cienkie i składają widok z `src/features/<funkcja>/`.
3. **Tokeny, nie kolory**: tylko klasy Tailwind z tokenów (`bg-surface`, `text-muted`, `border-control`, `bg-primary`) lub `var(--...)` z `src/styles/tokens.css`. Zakaz literałów hex w komponentach. Każdy widok musi działać w motywie jasnym i ciemnym (`<html data-theme>`).
4. **Dostępność (WCAG 2.1 AA)**: widoczny fokus, etykiety kontrolek, statusy jako ikona + tekst (`StatusBadge`), `aria-live="polite"` dla postępu, `role="alert"` dla błędów krytycznych, cele dotykowe ≥ 44 px na telefonie, brak poziomego scrolla przy 320 px.
5. **Wariant A eksportu**: JSON nie jest pobieralny, gdy `getExportDecision().allowed === false`; powód pokazany po polsku; nigdy zastępczy `{}` przy awarii (wyjątek: potwierdzony dokument obcy daje dokładnie `{}`). Dowody i raport są osobno, poza oceniany JSON.
6. **Klucz API**: pole klucza nie wyświetla ani nie zapisuje wartości w `localStorage`/logach; po zapisie pokazuj tylko stan „skonfigurowany”.
7. Każdy ekran ma stany: ładowanie (szkielet), pusty, błąd, sukces.

## Referencje

- Makiety (PNG, połowa skali): `design/*.png`. Wzoruj układ i hierarchię na nich; odstępstwa opisz w raporcie.
- Przepływy i stany: `../../docs/04-architektura/gui/user-flow.md`; specyfikacja: `../../docs/04-architektura/gui/projekt-ui.md`.
- Wzorce: `src/components/atoms/Button.tsx` (+ test), `StatusBadge.tsx`, `src/lib/api/hooks.ts`.

## Zakres pliku, który wolno edytować

Tylko pliki własne zadania (katalog funkcji, własne trasy, nowe komponenty współdzielone o unikalnych nazwach, własne testy). **Nie edytuj**: `tokens.css`, `globals.css`, `AppShell.tsx`, `layout.tsx`, istniejących atomów, `schemas.ts` (zgłoś potrzebę w raporcie). Nie commituj; commit robi koordynator.

## Testy (wymagane dla zadania)

- Jednostkowe/integracyjne: Vitest + Testing Library, obok kodu (`*.test.tsx`). Integracyjne = widok z prawdziwym mockiem (`setApiForTests(createMockClient({latencyMs:0}))`, `QueryClientProvider`).
- E2E: Playwright w `e2e/<funkcja>.spec.ts`, projekty `desktop` i `phone`; sprawdź klikalną ścieżkę i `@axe-core/playwright` bez naruszeń poważnych/krytycznych w obu motywach (`page.emulateMedia({colorScheme})` lub `localStorage o2j-theme`).
- Uruchamiaj na własnym porcie: `E2E_PORT=<przydzielony> npx playwright test e2e/<funkcja>.spec.ts`. Dev: `NEXT_DIST_DIR=.next-<port> npm run dev -- --port <port>`.
- Przed raportem: `npm run typecheck && npm run lint && npm test` muszą przejść.

## Raport końcowy

Lista plików, wynik komend (wklej końcówki), odstępstwa od makiet, brakujące elementy kontraktu API, znane luki. Bez wymyślania wyników.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
