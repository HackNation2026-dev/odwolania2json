import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("dashboard tiles link to status filters", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Pulpit" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Skonfiguruj klucz" })).toHaveAttribute("href", "/klucz");
  await page.getByRole("region", { name: "Liczniki dokumentów" }).getByRole("link", { name: /Pełny/ }).click();
  await expect(page).toHaveURL(/\/dokumenty\?status=full/);
});

for (const theme of ["light", "dark"] as const) {
  test(`dashboard is accessible in ${theme} theme at 360px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 360, height: 800 });
    await page.emulateMedia({ colorScheme: theme });
    await page.goto("/");
    await expect(page.getByRole("region", { name: "Liczniki dokumentów" })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath(`phone-${theme}.png`), fullPage: true });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations.filter(v => ["serious", "critical"].includes(v.impact ?? ""))).toEqual([]);
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.screenshot({ path: testInfo.outputPath(`desktop-${theme}.png`), fullPage: true });
    expect((await new AxeBuilder({ page }).analyze()).violations.filter(v => ["serious", "critical"].includes(v.impact ?? ""))).toEqual([]);
  });
}
