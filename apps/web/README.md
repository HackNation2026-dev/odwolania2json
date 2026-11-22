# Frontend Odwołania2JSON

Wymagane Node.js ≥ 22. Instalacja: `npm ci` w `apps/web`.

- Aplikacja: `npm run dev -- --port 3100`.
- Katalog komponentów: `npm run storybook` → http://localhost:6006.
- Statyczny katalog: `npm run build-storybook` → `storybook-static/`.
- Kontrole: `npm run typecheck`, `npm run lint`, `npm test`.
- E2E: `E2E_PORT=3100 npm run e2e` (zainstalowane przeglądarki Playwright).

Storybook używa globalnego CSS aplikacji. Toolbar wybiera motyw jasny/ciemny
(`html[data-theme]`) oraz szerokości 320, 360, 768, 1024 i 1440 px.
Foundations opisują tokeny, kontrasty obu palet, typografię, odstępy i ikony.

Nowy komponent umieść w `src/components/{atoms,molecules,organisms,templates}`.
Dodaj eksport w indeksie warstwy, `Nazwa.stories.tsx` z wariantami i stanami oraz
`Nazwa.test.tsx` z zachowaniem i nazwami dostępności. Używaj tokenów i widocznego
fokusu. Historia formularza musi mieć etykiety kontrolek. Zbiorczy
`src/components/stories.test.tsx` automatycznie wykrywa historie i sprawdza axe
w obu motywach. JSDOM nie oblicza kontrastu CSS: test pomija regułę color-contrast;
palety sprawdza `src/lib/theme/contrast.test.ts`, a przeglądarkowy addon a11y
sprawdza renderowane style. Test axe nie zastępuje kontroli klawiatury i telefonu.
