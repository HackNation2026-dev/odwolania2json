import { expect, test } from "@playwright/test";

/**
 * Siatka regresji wizualnej: wszystkie trasy x motyw x (desktop|telefon).
 * Baza zrzutów powstaje z `--update-snapshots` i NIE jest w Git (zależy od systemu/fontów);
 * służy jako bramka przy refaktorze: wygląd po zmianie ma być identyczny.
 */
const routes: [string, string][] = [
  ["pulpit", "/"],
  ["dodaj", "/dodaj"],
  ["dokumenty-galeria", "/dokumenty"],
  ["dokumenty-lista", "/dokumenty?widok=lista"],
  ["doc-full", "/dokumenty/doc-1"],
  ["doc-partial", "/dokumenty/doc-3"],
  ["doc-ocr", "/dokumenty/doc-4"],
  ["doc-ambiguous", "/dokumenty/doc-5"],
  ["doc-error", "/dokumenty/doc-6"],
  ["doc-foreign", "/dokumenty/doc-7"],
  ["doc-multi", "/dokumenty/doc-8"],
  ["klasy", "/klasy"],
  ["jak-to-dziala", "/jak-to-dziala"],
  ["klucz", "/klucz"],
  ["kontrola", "/klucz/kontrola"],
  ["login", "/login"],
  ["ustawienia", "/ustawienia"],
  ["uzytkownicy", "/uzytkownicy"],
  ["dziennik", "/dziennik"],
  ["nie-znaleziono", "/dokumenty/nie-ma-takiego"],
];

for (const theme of ["light", "dark"] as const) {
  for (const [name, path] of routes) {
    test(`visual ${name} ${theme}`, async ({ page }) => {
      await page.addInitScript((t) => {
        try {
          localStorage.setItem("o2j-theme", t);
        } catch {}
      }, theme);
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      await page.addStyleTag({
        content: "nextjs-portal,[data-nextjs-toast],[data-next-badge-root]{display:none!important} *{caret-color:transparent!important}",
      });
      await page.waitForTimeout(400);
      await expect(page).toHaveScreenshot(`${name}-${theme}.png`, { fullPage: true, animations: "disabled", maxDiffPixelRatio: 0.002 });
    });
  }
}
