import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

class KeyFlow {
  constructor(private page: Page) {}
  async configure() {
    await this.page.goto("/klucz");
    await this.page.getByLabel("Klucz API", { exact: true }).fill("synthetic-e2e-key");
    await this.page.getByRole("button", { name: "Sprawdź i zapisz" }).click();
    await expect(this.page.getByRole("heading", { name: "Klucz API skonfigurowany" })).toBeVisible();
  }
  async check() {
    await this.page.getByRole("link", { name: "Sprawdź połączenie" }).click();
    await this.page.getByRole("button", { name: "Sprawdź ponownie" }).click();
    await expect(this.page.getByRole("heading", { name: "Klucz przyjęty" })).toBeVisible({ timeout: 15_000 });
    await expect(this.page.getByRole("link", { name: "Przejdź do pulpitu" })).toBeVisible();
  }
}

for (const colorScheme of ["light", "dark"] as const) {
  test(`key to successful check and accessibility in ${colorScheme} theme`, async ({ page }, testInfo) => {
    test.setTimeout(90_000);
    await page.emulateMedia({ colorScheme });
    if (testInfo.project.name === "phone") await page.setViewportSize({ width: 320, height: 800 });
    const flow = new KeyFlow(page);
    await page.goto("/klucz");
    await expect(page.getByRole("button", { name: "Sprawdź i zapisz" })).toBeVisible();
    for (const route of ["/klucz", "/login", "/ustawienia"]) {
      await page.goto(route);
      await expect(page.locator("h1")).toBeVisible();
      const { violations } = await new AxeBuilder({ page }).analyze();
      expect(violations.filter((item) => ["serious", "critical"].includes(item.impact ?? ""))).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await page.screenshot({ path: testInfo.outputPath(`${route.slice(1)}-${colorScheme}.png`), fullPage: true });
    }
    await flow.configure();
    await expect(page.locator("body")).not.toContainText("synthetic-e2e-key");
    expect(await page.evaluate(() => JSON.stringify(localStorage))).not.toContain("synthetic-e2e-key");
    await flow.check();
    await page.screenshot({ path: testInfo.outputPath(`kontrola-${colorScheme}.png`), fullPage: true });
    const { violations } = await new AxeBuilder({ page }).analyze();
    expect(violations.filter((item) => ["serious", "critical"].includes(item.impact ?? ""))).toEqual([]);
    await page.getByRole("link", { name: "Przejdź do pulpitu" }).click();
    await expect(page).toHaveURL("/");
  });
}
