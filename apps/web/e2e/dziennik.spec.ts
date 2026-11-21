import { expect, test } from "@playwright/test";

test("opens event log from navigation and filters synthetic events", async ({ page }) => {
  await page.goto("/klasy");
  await page.getByRole("navigation", { name: "Główna" }).getByRole("link", { name: "Dziennik zdarzeń", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Dziennik zdarzeń", exact: true })).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("Liczba zdarzeń: 6");
  await page.getByRole("combobox", { name: "Rodzaj zdarzenia" }).selectOption("correction");
  await expect(page.getByRole("status")).toHaveText("Liczba zdarzeń: 1");
  await page.getByText("Szczegóły zdarzenia", { exact: true }).click();
  await expect(page.getByText(/Było: •••; Jest: •••/)).toBeVisible();
  await page.getByRole("combobox", { name: "Rodzaj zdarzenia" }).selectOption("configuration");
  await expect(page.getByRole("status")).toHaveText("Brak zdarzeń spełniających kryteria.");
  await page.getByRole("button", { name: "Wyczyść filtry" }).click();
  await expect(page.getByRole("status")).toHaveText("Liczba zdarzeń: 6");
});
