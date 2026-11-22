# Decyzja DS-A: Storybook jako katalog komponentów

Data: 2026-11-21. Zakres: narzędzia deweloperskie `apps/web`.

Wybrano Storybook 10.6.8 z `@storybook/nextjs-vite`, addonami docs i a11y
oraz integracją Tailwind przez Vite. Zgodność weryfikują lokalne deklaracje
pakietów, typecheck oraz budowanie z zainstalowanymi Next 16.4.6 i React 19.3.1.
Dokumentacja: lokalne README/deklaracje pakietów oraz oficjalne przykłady
Storybook 10.6.5 dostępne przez Context7.

Konsekwencje: dodatkowe zależności wyłącznie deweloperskie i osobny artefakt
`storybook-static`. Storybook nie zmienia sposobu dostarczenia aplikacji jury.
Globalne style i tokeny pozostają wspólne z aplikacją. Historie komponentów
są również wejściem zbiorczego testu axe. Kontrast CSS wymaga przeglądarki;
JSDOM sprawdza pozostałe reguły, a test tokenów oblicza kontrasty palet.
