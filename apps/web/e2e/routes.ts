import { existsSync } from "node:fs";
import { resolve } from "node:path";

/** Jedna lista tras bazowych; brakujące ekrany W1–W4 mają jawne fixme. */
export const baseRoutes = [
  { path: "/", label: "Pulpit", source: "src/app/page.tsx" },
  { path: "/dodaj", label: "Nowa analiza", source: "src/app/dodaj/page.tsx" },
  { path: "/dokumenty", label: "Sprawy", source: "src/app/dokumenty/page.tsx" },
  { path: "/klasy", label: "Klasy dokumentów", source: "src/app/klasy/page.tsx" },
  { path: "/jak-to-dziala", label: "Jak to działa", source: "src/app/jak-to-dziala/page.tsx" },
  { path: "/ustawienia", label: "Ustawienia", source: "src/app/ustawienia/page.tsx" },
  { path: "/uzytkownicy", label: "Użytkownicy i role", source: "src/app/uzytkownicy/page.tsx" },
  { path: "/dziennik", label: "Dziennik zdarzeń", source: "src/app/dziennik/page.tsx" },
] as const;

export const routeExists = (route: (typeof baseRoutes)[number]) => existsSync(resolve(process.cwd(), route.source));
