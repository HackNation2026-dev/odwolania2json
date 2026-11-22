import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function checkAccessibility(page: Page) {
  const result = await new AxeBuilder({ page }).analyze();
  expect(
    result.violations.filter(
      (item) => item.impact === "serious" || item.impact === "critical",
    ),
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
}

for (const theme of ["light", "dark"] as const) {
  test(`class read, draft test and atomic activation ${theme}`, async ({
    page,
  }, testInfo) => {
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/klasy");
    await page
      .getByRole("heading", { name: "Potwierdzenie przelewu", exact: true })
      .waitFor();
    await page
      .getByRole("article")
      .filter({
        has: page.getByRole("heading", { name: "Potwierdzenie przelewu" }),
      })
      .getByRole("link", { name: "Szczegóły", exact: true })
      .click();
    await expect(page).toHaveURL(/\/klasy\/przelew/);
    await page
      .getByRole("heading", { name: "Pola i reguły kontraktu" })
      .waitFor();
    await page.getByRole("tab", { name: "YAML", exact: true }).click();
    await expect(
      page.getByRole("region", { name: "przelew.yaml", exact: true }),
    ).toContainText("kwota");
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("link", { name: "Pobierz przelew.yaml" }).click();
    expect((await downloadPromise).suggestedFilename()).toBe("przelew.yaml");
    await checkAccessibility(page);
    await page.getByRole("tab", { name: "Test", exact: true }).click();
    if (testInfo.project.name === "phone")
      await page.getByRole("tab", { name: "Wynik testu", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "Aktywuj zestaw", exact: true }),
    ).toBeDisabled();
    await page.getByRole("button", { name: "Testuj wersję roboczą" }).click();
    await expect(
      page.getByText("Walidacja: poprawna", { exact: true }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Aktywuj zestaw", exact: true })
      .click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toHaveAccessibleName("Aktywuj zestaw v2?");
    await checkAccessibility(page);
    await dialog
      .getByRole("button", { name: "Aktywuj", exact: true })
      .dblclick();
    await expect(
      page.getByText("Zestaw v2 aktywny", { exact: true }),
    ).toBeVisible();
    await expect(page.getByText("wersja v2 · 7 pól")).toBeVisible();
    await checkAccessibility(page);
    await page.screenshot({
      path: testInfo.outputPath(`klasy-activated-${theme}.png`),
      fullPage: true,
    });
  });

  test(`class stale test and invalid normalizer ${theme}`, async ({
    page,
  }, testInfo) => {
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/klasy/przelew");
    await page.getByRole("tab", { name: "Test", exact: true }).click();
    const editor = page.getByRole("textbox", { name: /edycja demonstracyjna/ });
    const lines = (await editor.inputValue()).split("\n");
    lines.splice(13, 0, "    normalizator: nieistniejacy");
    await editor.fill(lines.join("\n"));
    if (testInfo.project.name === "phone")
      await page.getByRole("tab", { name: "Wynik testu", exact: true }).click();
    await page.getByRole("button", { name: "Testuj wersję roboczą" }).click();
    await expect(page.getByRole("main").getByRole("alert")).toContainText(
      "Linia 14: brak normalizatora",
    );
    await expect(
      page.getByText("Wynik poprzedniego testu jest nieaktualny"),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Aktywuj zestaw", exact: true }),
    ).toBeDisabled();
    await checkAccessibility(page);
    await page.screenshot({
      path: testInfo.outputPath(`klasy-invalid-${theme}.png`),
      fullPage: true,
    });
    await page.setViewportSize({ width: 320, height: 900 });
    await checkAccessibility(page);
  });
}
