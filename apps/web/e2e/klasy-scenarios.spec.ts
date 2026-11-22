import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const theme of ["light", "dark"]) {
  test(`activation failure keeps v1 and retries ${theme}`, async ({
    page,
  }, info) => {
    test.skip(
      process.env.NEXT_PUBLIC_MOCK_CLASS_SCENARIO !== "activation-error",
      "Wymaga osobnego serwera demonstracyjnego z NEXT_PUBLIC_MOCK_CLASS_SCENARIO=activation-error; polecenie w REPORT-KLASY.md.",
    );
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/klasy/przelew");
    await page.getByRole("tab", { name: "Test", exact: true }).click();
    if (info.project.name === "phone")
      await page.getByRole("tab", { name: "Wynik testu", exact: true }).click();
    await page.getByRole("button", { name: "Testuj wersję roboczą" }).click();
    await expect(
      page.getByText("Walidacja: poprawna", { exact: true }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Aktywuj zestaw", exact: true })
      .click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("button", { name: "Aktywuj", exact: true }).click();
    await expect(dialog.getByRole("alert")).toContainText(
      "Nie aktywowano. Nadal aktywny v1. Ponów",
    );
    const audit = await new AxeBuilder({ page }).analyze();
    expect(
      audit.violations.filter(
        (item) => item.impact === "serious" || item.impact === "critical",
      ),
    ).toEqual([]);
    await page.screenshot({
      path: info.outputPath(`activation-error-${theme}.png`),
      fullPage: true,
    });
    await dialog.getByRole("button", { name: "Ponów" }).click();
    await expect(
      page.getByText("Zestaw v2 aktywny", { exact: true }),
    ).toBeVisible();
  });

  test(`missing configuration blocks analysis without empty JSON ${theme}`, async ({
    page,
  }, info) => {
    test.skip(
      process.env.NEXT_PUBLIC_MOCK_CLASS_SCENARIO !== "no-configuration",
      "Wymaga osobnego serwera demonstracyjnego z NEXT_PUBLIC_MOCK_CLASS_SCENARIO=no-configuration; polecenie w REPORT-KLASY.md.",
    );
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/klasy");
    await expect(page.getByRole("main").getByRole("alert")).toContainText(
      "Błąd konfiguracji. Brak poprawnego zestawu klas. Analiza zablokowana.",
    );
    await expect(page.getByRole("main")).not.toContainText("{}");
    await expect(
      page.getByRole("link", { name: "Szczegóły", exact: true }),
    ).toHaveCount(0);
    const audit = await new AxeBuilder({ page }).analyze();
    expect(
      audit.violations.filter(
        (item) => item.impact === "serious" || item.impact === "critical",
      ),
    ).toEqual([]);
    await page.screenshot({
      path: info.outputPath(`configuration-error-${theme}.png`),
      fullPage: true,
    });
  });
}
