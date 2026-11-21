import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

class AddDocumentsPage {
  constructor(readonly page: Page) {}
  async configureKey() {
    await this.page.getByRole("link", { name: "Skonfiguruj klucz" }).click();
    await this.page.getByLabel("Klucz API", { exact: true }).fill("synthetic-demo-key");
    await this.page.getByRole("button", { name: "Sprawdź i zapisz" }).click();
    await expect(this.page.getByRole("heading", { name: "Klucz API skonfigurowany" })).toBeVisible();
    // Ekran klucza nie ma menu bocznego; powrót do analizy jest w nagłówku.
    await this.page.getByRole("banner").getByRole("link", { name: "Nowa analiza", exact: true }).click();
  }
}

test("uploads PDF through progress into document list", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "+ Dodaj dokumenty", exact: true }).click();
  await expect(page.getByRole("button", { name: "Uruchom analizę" })).toBeDisabled();
  await new AddDocumentsPage(page).configureKey();
  await page.getByLabel("Pliki PDF", { exact: true }).setInputFiles({ name: "e2e-appeal.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4 synthetic") });
  await page.getByRole("button", { name: "Uruchom analizę" }).click();
  await expect(page.getByRole("heading", { name: "Analiza w toku" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Analiza zakończona" })).toBeVisible();
  await page.getByRole("link", { name: "Przejdź do dokumentów" }).click();
  await expect(page).toHaveURL(/\/dokumenty$/);
  await page.getByRole("searchbox", { name: "Szukaj po nazwie pliku" }).fill("e2e-appeal.pdf");
  await expect(page.getByRole("link", { name: /e2e-appeal\.pdf/ })).toBeVisible();
});

for (const theme of ["light", "dark"] as const) {
  test(`selection is accessible in ${theme} theme at 360px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 360, height: 800 });
    await page.emulateMedia({ colorScheme: theme });
    await page.goto("/dodaj");
    await expect(page.getByRole("link", { name: "Skonfiguruj klucz" })).toBeVisible();
    await page.getByLabel("Pliki PDF", { exact: true }).setInputFiles([{ name: "appeal.pdf", mimeType: "application/pdf", buffer: Buffer.from("pdf") }, { name: "notes.docx", mimeType: "application/octet-stream", buffer: Buffer.from("docx") }]);
    await expect(page.getByText(/notes\.docx: to nie jest PDF — pominięto\./)).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath(`phone-${theme}.png`), fullPage: true });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations.filter(v => ["serious", "critical"].includes(v.impact ?? ""))).toEqual([]);
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.screenshot({ path: testInfo.outputPath(`desktop-${theme}.png`), fullPage: true });
    expect((await new AxeBuilder({ page }).analyze()).violations.filter(v => ["serious", "critical"].includes(v.impact ?? ""))).toEqual([]);
  });
}
