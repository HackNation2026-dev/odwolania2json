import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";

class DocumentScreen {
  constructor(readonly page: Page) {}
  async open(id: string, tab = "przeglad") {
    await this.page.goto(`/dokumenty/${id}?tab=${tab}`);
    await expect(this.page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(this.page.getByRole("button", { name: "Pobierz JSON", exact: true })).toBeVisible();
  }
  get download() { return this.page.getByRole("button", { name: "Pobierz JSON", exact: true }); }
}

test("edits missing field and downloads validated JSON", async ({ page }) => {
  const screen = new DocumentScreen(page); await screen.open("doc-3");
  await expect(screen.download).toBeDisabled();
  await page.getByRole("button", { name: "Edytuj Data pisma" }).click();
  await page.getByLabel("Nowa wartość: Data pisma").fill("2026-03-20");
  await page.getByRole("button", { name: "Zapisz", exact: true }).click();
  await expect(screen.download).toBeEnabled();
  const downloading = page.waitForEvent("download"); await screen.download.click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("odwolanie-003.json");
  const path = await download.path();
  const json = JSON.parse(await readFile(path!, "utf8"));
  expect(json.data_pisma).toBe("2026-03-20"); expect(json.kwota).toBeNull(); expect(json).not.toHaveProperty("evidence");
});

test("blocks failed document and retries analysis", async ({ page }) => {
  const screen = new DocumentScreen(page); await screen.open("doc-6");
  await expect(screen.download).toBeDisabled();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Nie udało się przetworzyć dokumentu");
  await page.getByRole("button", { name: "Ponów", exact: true }).click();
  await expect(page.locator('[data-status="full"]')).toBeVisible();
  await expect(screen.download).toBeEnabled();
});

test("chooses ambiguous class while keeping incomplete export blocked", async ({ page }) => {
  const screen = new DocumentScreen(page); await screen.open("doc-5");
  await expect(screen.download).toBeDisabled();
  await page.getByRole("button", { name: "Wybierz: Odwołanie od decyzji" }).click();
  await expect(page.locator('[data-status="partial"]')).toBeVisible();
  await expect(page.getByRole("button", { name: "Edytuj Data pisma" })).toBeVisible();
  await expect(screen.download).toBeDisabled();
});

test("downloads exactly an empty object for confirmed foreign document", async ({ page }) => {
  const screen = new DocumentScreen(page); await screen.open("doc-7");
  await expect(screen.download).toBeEnabled();
  const downloading = page.waitForEvent("download"); await screen.download.click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("menu-restauracji.json");
  expect(await readFile((await download.path())!, "utf8")).toBe("{}");
});

test("shows JSON wrapping and mobile document view without overflow", async ({ page }, testInfo) => {
  const screen = new DocumentScreen(page); await screen.open("doc-1", "json");
  await expect(page.getByLabel("Zawijaj linie")).toBeChecked();
  await expect(page.getByLabel("JSON dokumentu")).toContainText('"sygnatura"');
  if (testInfo.project.name === "phone") {
    await page.getByRole("link", { name: "Dokument", exact: true }).click();
    await expect(page.getByRole("region", { name: /Strona PDF/ })).toBeVisible();
    await expect(page.getByRole("link", { name: "Przegląd", exact: true })).toBeInViewport();
    for (const pane of await page.locator(".scroll-pane").all()) expect((await pane.boundingBox())?.height).toBeGreaterThan(0);
    await page.setViewportSize({ width: 320, height: 780 });
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

for (const theme of ["light", "dark"] as const) {
  for (const [id, tab] of [["doc-1", "przeglad"], ["doc-3", "eksport"], ["doc-4", "przeglad"], ["doc-5", "przeglad"], ["doc-6", "przeglad"], ["doc-7", "json"], ["doc-8", "dowody"], ["doc-9", "przeglad"]]) {
    test(`has no serious accessibility violations: ${id}/${tab}/${theme}`, async ({ page }, testInfo) => {
      await page.addInitScript(value => localStorage.setItem("o2j-theme", value), theme);
      await page.emulateMedia({ colorScheme: theme });
      const screen = new DocumentScreen(page); await screen.open(id!, tab!);
      await expect(page.getByRole("heading", { name: /Eksport (dozwolony|zablokowany)/ })).toBeVisible();
      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations.filter(v => v.impact === "serious" || v.impact === "critical")).toEqual([]);
      if (id === "doc-1") await page.screenshot({ path: testInfo.outputPath(`document-${theme}.png`), fullPage: true });
    });
  }
}

for (const viewport of [{ width: 1440, height: 900 }, { width: 1280, height: 720 }, { width: 360, height: 800 }]) {
  for (const id of ["doc-1", "doc-3", "doc-4", "doc-10", "doc-11"]) {
    test(`keeps review fields reachable at ${viewport.width}x${viewport.height}: ${id}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      const screen = new DocumentScreen(page); await screen.open(id);
      const panel = page.getByRole("region", { name: "Zawartość widoku dokumentu" });
      const firstField = panel.locator('article[id^="field-"]').first();
      if (viewport.width < 768) await firstField.scrollIntoViewIfNeeded();
      await expect(firstField).toBeInViewport();
      const dimensions = await panel.evaluate(el => ({ height: el.clientHeight, scrollHeight: el.scrollHeight }));
      expect(dimensions.height).toBeGreaterThan(180);
      const panes = page.locator(".scroll-pane");
      await expect(panes).not.toHaveCount(0);
      for (const pane of await panes.all()) expect((await pane.boundingBox())?.height).toBeGreaterThan(0);
      const targetField = panel.locator('article[id^="field-"]').filter({ hasText: id === "doc-10" ? "Data decyzji" : id === "doc-11" ? "Pełnomocnik" : "Data pisma" });
      await targetField.scrollIntoViewIfNeeded();
      await expect(targetField).toBeInViewport();
      expect((await targetField.boundingBox())?.height).toBeGreaterThan(0);
      const lastField = panel.locator('article[id^="field-"]').last();
      await lastField.scrollIntoViewIfNeeded();
      await expect(lastField).toBeInViewport();
      await expect(screen.download).toBeInViewport();
    });
  }
}

for (const theme of ["light", "dark"] as const) {
  for (let number = 1; number <= 12; number++) {
    test(`visual review ${theme} doc-${number} all tabs`, async ({ page }, testInfo) => {
      await page.addInitScript(value => localStorage.setItem("o2j-theme", value), theme);
      const screen = new DocumentScreen(page);
      const tabs = testInfo.project.name === "phone" ? ["dokument", "przeglad", "json", "dowody", "eksport"] : ["przeglad", "json", "dowody", "eksport"];
      for (const tab of tabs) {
        await screen.open(`doc-${number}`, tab);
        await expect(page.getByRole("heading", { name: /Eksport (dozwolony|zablokowany)/ })).toBeVisible();
        const panel = page.getByRole("region", { name: tab === "dokument" ? "Podgląd dokumentu" : "Zawartość widoku dokumentu" });
        expect((await panel.boundingBox())?.height).toBeGreaterThan(0);
        await page.screenshot({ path: testInfo.outputPath(`${theme}-doc-${number}-${tab}.png`), fullPage: false });
      }
    });
  }
}
