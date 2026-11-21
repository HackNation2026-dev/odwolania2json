import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("filters, searches, sorts, remembers view and opens a document", async ({
  page,
}) => {
  await page.goto("/dokumenty");
  await expect(page.getByTestId("document-gallery")).toBeVisible();
  await page.getByText(/^Status.*▾/).click();
  await page.getByRole("checkbox", { name: /Pełny/ }).check();
  await page.getByRole("button", { name: "Zastosuj (1)" }).click();
  await expect(page).toHaveURL(/status=full/);
  await expect(
    page.getByTestId("document-gallery").getByRole("link"),
  ).toHaveCount(5);
  await page.getByRole("searchbox").fill("odwolanie-001");
  await expect(
    page.getByTestId("document-gallery").getByRole("link"),
  ).toHaveCount(1);
  await expect(page).toHaveURL(/q=odwolanie-001/);
  await page.getByRole("button", { name: "Wyczyść filtry" }).click();
  await page.getByRole("combobox", { name: "Sortowanie" }).selectOption("name");
  await expect(
    page.getByTestId("document-gallery").getByRole("link").first(),
  ).toContainText("decyzja-0412.pdf");
  await page
    .getByRole("combobox", { name: "Sortowanie" })
    .selectOption("oldest");
  await expect(
    page.getByTestId("document-gallery").getByRole("link").first(),
  ).toContainText("odwolanie-005.pdf");
  await page.getByRole("button", { name: /Lista/ }).click();
  await expect(page.getByRole("button", { name: /Lista/ })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.goto("/dokumenty");
  await expect(page.getByRole("button", { name: /Lista/ })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.getByRole("button", { name: /Kafelki/ }).click();
  await page.getByRole("searchbox").fill("odwolanie-001");
  await page.getByRole("link", { name: /odwolanie-001.pdf/ }).click();
  await expect(page).toHaveURL(/\/dokumenty\/doc-1$/);
});

test("dashboard link, empty results and phone width", async ({ page }) => {
  await page.goto("/dokumenty?status=full");
  await expect(
    page.getByTestId("document-gallery").getByRole("link"),
  ).toHaveCount(5);
  await page.getByRole("searchbox").fill("faktura_2027.pdf");
  await expect(
    page.getByRole("heading", {
      name: "Brak dokumentów spełniających kryteria",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Wyczyść filtry" }).last().click();
  await expect(page.getByTestId("document-gallery")).toBeVisible();
  await page.setViewportSize({ width: 320, height: 800 });
  await expect(page.getByRole("searchbox")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: /Lista/ }).click();
  await expect(page.getByRole("table")).toBeHidden();
  await expect(
    page.getByRole("link", { name: /nowe-odwolanie.pdf/ }),
  ).toBeVisible();
});

for (const theme of ["light", "dark"])
  test(`has no serious accessibility violations in ${theme}`, async ({
    page,
  }) => {
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/dokumenty");
    await expect(page.getByTestId("document-gallery")).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    for (const view of ["Kafelki", "Lista"]) {
      await page.getByRole("button", { name: new RegExp(view) }).click();
      const results = await new AxeBuilder({ page }).analyze();
      expect(
        results.violations.filter((v) =>
          ["serious", "critical"].includes(v.impact ?? ""),
        ),
      ).toEqual([]);
    }
  });
