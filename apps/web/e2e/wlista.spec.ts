import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const theme of ["light", "dark"] as const) {
  test(`batch export and card results in ${theme}`, async ({ page }, info) => {
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/dokumenty?partia=B-01&widok=tabela");
    await expect(
      page.getByText("Katalog główny", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Pobierz dowody partii · E2" }),
    ).toBeDisabled();
    await page
      .getByRole("link", { name: "Pobierz wyniki partii (ZIP) · plan E2" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Uwzględnione (3)" }),
    ).toBeVisible({ timeout: 15000 });
    await expect(
      page.getByRole("heading", { name: "Pominięte (3)" }),
    ).toBeVisible();
    const report = page.waitForEvent("download");
    await page.getByRole("button", { name: "Pobierz raport pominięć" }).click();
    expect((await report).suggestedFilename()).toBe(
      "raport-pominiec-B-01.json",
    );
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Pobierz 3 wyniki" }).click();
    expect((await download).suggestedFilename()).toMatch(/\.json$/);
    await expect(
      page.getByText(/Przygotowano 3 osobne pliki JSON/),
    ).toBeVisible();
    await page.screenshot({
      path: info.outputPath(`export-${theme}.png`),
      fullPage: true,
    });
    expect(
      (await new AxeBuilder({ page }).analyze()).violations.filter((v) =>
        ["serious", "critical"].includes(v.impact ?? ""),
      ),
    ).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  });

  test(`collision resolution and pipeline in ${theme}`, async ({
    page,
  }, info) => {
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/dodaj");
    await expect(page.getByText(/OCR tymczasowy \(shim\):/)).toBeVisible();
    await page.getByRole("link", { name: "Skonfiguruj klucz" }).click();
    await page
      .getByLabel("Klucz API", { exact: true })
      .fill("synthetic-demo-key");
    await page.getByRole("button", { name: "Sprawdź i zapisz" }).click();
    await expect(
      page.getByRole("heading", { name: "Klucz API skonfigurowany" }),
    ).toBeVisible();
    await page
      .getByRole("banner")
      .getByRole("link", { name: /Nowa analiza/ })
      .click();
    await page.getByLabel("Pliki PDF", { exact: true }).setInputFiles({
      name: "odwolanie.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("synthetic pdf"),
    });
    await page.getByRole("button", { name: "Uruchom analizę" }).click();
    const dialog = page.getByRole("dialog", { name: "Kolizja ścieżki" });
    await expect(dialog).toBeVisible();
    await expect(
      dialog.getByText(/Bez automatycznego \(2\) i bez nadpisania/),
    ).toBeVisible();
    expect(
      (await new AxeBuilder({ page }).analyze()).violations.filter((v) =>
        ["serious", "critical"].includes(v.impact ?? ""),
      ),
    ).toEqual([]);
    await dialog.getByRole("button", { name: "Anuluj" }).click();
    await expect(
      page.getByRole("heading", { name: "Wybrane pliki (1)" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Uruchom analizę" }).click();
    await page.getByRole("button", { name: "Nowa wersja dokumentu" }).click();
    await expect(
      page.getByRole("heading", { name: "Analiza zakończona" }),
    ).toBeVisible();
    await page.getByText("Etapy potoku: odwolanie.pdf").click();
    await expect(page.getByText(/T5 · Normalizacja i walidacja/)).toBeVisible();
    await expect(page.getByText(/Strony: 3 · OCR: 0/)).toBeVisible();
    await page.screenshot({
      path: info.outputPath(`pipeline-${theme}.png`),
      fullPage: true,
    });
    expect(
      (await new AxeBuilder({ page }).analyze()).violations.filter((v) =>
        ["serious", "critical"].includes(v.impact ?? ""),
      ),
    ).toEqual([]);
    await page.setViewportSize({ width: 320, height: 800 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  });
}
