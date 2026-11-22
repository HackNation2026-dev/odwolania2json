import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { baseRoutes, routeExists } from "./routes";

class SmokePage {
  constructor(readonly page: Page) {}
  async ready() {
    await expect(this.page.getByRole("main")).toBeVisible();
    // Poczekaj na zakończenie odczytu hooków zamiast badać wyłącznie szkielety.
    await expect(
      this.page
        .getByRole("status")
        .filter({ hasText: /Wczytywanie|Ładowanie/ }),
    ).toHaveCount(0);
  }
}

for (const route of baseRoutes) {
  test.describe(route.path, () => {
    test.beforeEach(() => {
      // Trasy równoległych wykonawców zaczną być sprawdzane po dodaniu ich plików.
      test.fixme(
        !routeExists(route),
        `Brak trasy ${route.path}; ekran W1–W4 oczekuje implementacji.`,
      );
    });

    test("opens from navigation without console errors or 404", async ({
      page,
    }) => {
      const errors: string[] = [];
      // Znane anulowanie TextLayer w react-web-pdf-editor 0.1.6: scripts/pdf/REPORT.md, „Ograniczenia”.
      const knownTextLayerCancellation = (message: string) => /^(?:AbortException: )?TextLayer task cancelled\.?$/.test(message);
      page.on("pageerror", (error) => { if (!knownTextLayerCancellation(error.message)) errors.push(error.message); });
      page.on("console", (message) => { if (message.type() === "error" && !knownTextLayerCancellation(message.text())) errors.push(message.text()); });
      const missing: string[] = [];
      page.on("response", (response) => {
        if (response.status() === 404) missing.push(response.url());
      });
      await page.goto("/klasy");
      const menu = page.getByRole("button", { name: "Otwórz menu" });
      if (await menu.isVisible()) await menu.click();
      const navigation = page.getByRole("navigation", { name: "Główna" });
      await expect(navigation.getByRole("link")).toHaveCount(baseRoutes.length);
      await navigation
        .getByRole("link", { name: route.label, exact: true })
        .click();
      await expect(page).toHaveURL(route.path, { timeout: 15_000 });
      await new SmokePage(page).ready();
      await expect(
        page.getByRole("heading", { name: "Nie znaleziono strony" }),
      ).toHaveCount(0);
      expect(missing).toEqual([]);
      expect(errors).toEqual([]);
    });

    test("has no horizontal document overflow at 320 pixels", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 320, height: 800 });
      await page.goto(route.path);
      await new SmokePage(page).ready();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
    });

    for (const theme of ["light", "dark"] as const) {
      test(`has no serious or critical axe violations in ${theme} theme`, async ({
        page,
      }) => {
        await page.addInitScript(
          (value) => localStorage.setItem("o2j-theme", value),
          theme,
        );
        await page.goto(route.path);
        await new SmokePage(page).ready();
        await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
        // Uwzględnij także rozwijane szczegóły pól klas.
        await page.locator("main details").evaluateAll((items) =>
          items.forEach((item) => {
            (item as HTMLDetailsElement).open = true;
          }),
        );
        const results = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
          .analyze();
        expect(
          results.violations.filter((violation) =>
            ["serious", "critical"].includes(violation.impact ?? ""),
          ),
        ).toEqual([]);
      });
    }
  });
}

test("persists ThemeToggle and applies theme before hydration and first frame", async ({
  page,
}) => {
  await page.goto("/klasy");
  for (const theme of ["dark", "light"] as const) {
    const menu = page.getByRole("button", { name: "Otwórz menu" });
    if (await menu.isVisible()) await menu.click();
    await page
      .getByRole("combobox", { name: "Motyw", exact: true })
      .selectOption(theme);
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    expect(await page.evaluate(() => localStorage.getItem("o2j-theme"))).toBe(
      theme,
    );
    // Zablokuj JS aplikacji: tylko skrypt inline w head może ustawić motyw.
    await page.route(/\/_next\/.*\.js(?:\?.*)?$/, (request) => request.abort());
    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    expect(
      await page.evaluate(
        () =>
          new Promise<string | undefined>((resolve) =>
            requestAnimationFrame(() =>
              resolve(document.documentElement.dataset.theme),
            ),
          ),
      ),
    ).toBe(theme);
    await page.unroute(/\/_next\/.*\.js(?:\?.*)?$/);
    await page.reload();
    if (await menu.isVisible()) await menu.click();
    await expect(
      page.getByRole("combobox", { name: "Motyw", exact: true }),
    ).toHaveValue(theme);
    const close = page.getByRole("button", {
      name: "× Zamknij menu",
      exact: true,
    });
    if (await close.isVisible()) await close.click();
  }
});

test("supports keyboard skip link and visible focus", async ({ page }) => {
  await page.goto("/klasy");
  await new SmokePage(page).ready();
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Przejdź do treści" });
  await expect(skip).toBeFocused();
  await expect(skip).toBeVisible();
  expect(
    await skip.evaluate((element) => {
      const style = getComputedStyle(element);
      return (
        style.outlineStyle !== "none" && parseFloat(style.outlineWidth) >= 2
      );
    }),
  ).toBe(true);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  await page.keyboard.press("Tab");
  const focused = page.getByRole("main").locator(":focus");
  await expect(focused).toBeVisible();
  expect(
    await focused.evaluate((element) => getComputedStyle(element).outlineStyle),
  ).not.toBe("none");
});

for (const theme of ["light", "dark"] as const) {
  test(`W-SYS retention, audit, roles and public information in ${theme}`, async ({
    page,
  }) => {
    test.setTimeout(90_000);
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/ustawienia");
    const input = page.getByRole("spinbutton", {
      name: "Usuń sprawy po (liczba dni)",
    });
    await input.fill("0");
    await page.getByRole("button", { name: "Zapisz retencję" }).click();
    await expect(input).toHaveAttribute("aria-invalid", "true");
    await input.fill("60");
    await page.getByRole("button", { name: "Zapisz retencję" }).click();
    await page.getByRole("button", { name: "Zapisz", exact: true }).click();
    await expect(
      page.getByText("Zapisano retencję w demonstracji."),
    ).toBeVisible();
    await page.goto("/dziennik");
    await page
      .getByRole("combobox", { name: "Rodzaj zdarzenia" })
      .selectOption("reveal");
    await expect(
      page.getByText(/Wartość nie jest zapisana w dzienniku/),
    ).toBeVisible();
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Eksportuj CSV" }).click();
    expect((await download).suggestedFilename()).toBe("dziennik-demo.csv");
    await page.goto("/uzytkownicy");
    await page.getByRole("button", { name: "Edytuj: Anna Kowalska" }).click();
    await expect(
      page.getByRole("combobox", { name: "Zakres spraw" }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "Edytuj: Anna Kowalska" }),
    ).toBeFocused();
    for (const path of [
      "/dostepnosc",
      "/gotowosc",
      "/uzytkownicy/brak-dostepu",
    ]) {
      await page.goto(path);
      await new SmokePage(page).ready();
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      expect(
        results.violations.filter((v) =>
          ["serious", "critical"].includes(v.impact ?? ""),
        ),
      ).toEqual([]);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    }
  });
}

for (const theme of ["light", "dark"] as const) {
test(`W-SYS mobile menu focuses close and navigates to accessibility in ${theme}`, async ({
  page,
}) => {
  test.setTimeout(90_000);
  await page.addInitScript(value => localStorage.setItem("o2j-theme", value), theme);
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto("/ustawienia");
  const trigger = page.getByRole("button", { name: "Otwórz menu" });
  await trigger.click();
  const close = page.getByRole("button", {
    name: "× Zamknij menu",
    exact: true,
  });
  await expect(close).toBeFocused();
  await expect(page.getByRole("dialog")).toHaveCSS("width", "288px");
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter(v => ["serious", "critical"].includes(v.impact ?? ""))).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
  await trigger.click();
  await page.getByRole("link", { name: "Deklaracja dostępności" }).click();
  await expect(
    page.getByRole("heading", { name: "Dostępność", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});
}
