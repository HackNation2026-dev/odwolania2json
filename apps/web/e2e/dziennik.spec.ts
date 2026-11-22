import { expect, test } from "@playwright/test";

for (const theme of ["light", "dark"] as const) {
  test(`opens event log from navigation and filters synthetic events in ${theme}`, async ({ page }) => {
    await page.addInitScript(value => localStorage.setItem("o2j-theme", value), theme);
    await page.goto("/klasy");
    const menu = page.getByRole("button", { name: "Otwórz menu" });
    if (await menu.isVisible()) await menu.click();
    await page.getByRole("navigation", { name: "Główna" })
      .getByRole("link", { name: "Dziennik zdarzeń", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Dziennik zdarzeń", exact: true })).toBeVisible();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    const count = page.getByRole("status", { name: "Liczba zdarzeń", exact: true });
    await expect(count).toHaveText("Liczba zdarzeń: 5");
    const type = page.getByRole("combobox", { name: "Rodzaj zdarzenia" });
    await type.selectOption("correction");
    await expect(count).toHaveText("Liczba zdarzeń: 1");
    await expect(page.getByText(/Było: •••••••• \/ Jest: ••••••••/)).toBeVisible();
    await type.selectOption("configuration");
    await expect(count).toHaveText("Liczba zdarzeń: 1");
    await page.getByRole("textbox", { name: "Użytkownik", exact: true }).fill("Nieistniejący użytkownik");
    await expect(count).toHaveText("Liczba zdarzeń: 0");
    await expect(page.getByText("Brak zdarzeń spełniających kryteria.", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Wyczyść filtry" }).click();
    await expect(type).toHaveValue("");
    await expect(page.getByRole("textbox", { name: "Użytkownik", exact: true })).toHaveValue("");
    await expect(count).toHaveText("Liczba zdarzeń: 5");
  });
}
