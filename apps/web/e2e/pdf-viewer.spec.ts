import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import geometry from "../public/demo-pdf/odwolanie.json" with { type: "json" };
// Pełny scenariusz obejmuje dwa audyty axe; równoległe buildy w IDE wydłużają przebieg.
test.setTimeout(90_000);
const proof = geometry.find((h) => h.label.startsWith("Odwołujący:"))!;
async function checkGeometry(page: Page) {
  const frame = page.locator(`[data-evidence-id="${proof.id}"]`);
  const text = page
    .locator(".textLayer span")
    .getByText(proof.label, { exact: true });
  await expect(frame).toBeVisible();
  await expect(text).toBeVisible();
  await expect
    .poll(async () => {
      const [a, b] = await Promise.all([
        frame.boundingBox(),
        text.boundingBox(),
      ]);
      return a && b
        ? Math.max(
            Math.abs(a.x - b.x),
            Math.abs(a.y - b.y),
            Math.abs(a.width - b.width),
            Math.abs(a.height - b.height),
          )
        : 1000;
      // Uwzględniamy zaokrąglenie wymiarów canvas i metryki fontu przeglądarki.
    })
    .toBeLessThan(2);
}
test("renders local read-only PDF with precise evidence at every scale", async ({
  page,
}, testInfo) => {
  const external: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      ["http:", "https:"].includes(url.protocol) &&
      !["localhost", "127.0.0.1"].includes(url.hostname)
    )
      external.push(request.url());
  });
  const start = Date.now();
  await page.goto("/dev-pdf");
  await expect(page.locator('[data-page-number="1"] canvas')).toBeVisible();
  await checkGeometry(page);
  console.log(
    `${testInfo.project.name}: podgląd i dowód gotowe po ${Date.now() - start} ms (łącznie z nawigacją/kompilacją dev)`,
  );
  await page.getByRole("button", { name: "Powiększ", exact: true }).click();
  await page.getByRole("button", { name: "Powiększ", exact: true }).click();
  await expect(page.getByLabel("Powiększenie", { exact: true })).toHaveText(
    "150%",
  );
  await checkGeometry(page);
  await page
    .getByRole("button", { name: "Następna strona", exact: true })
    .click();
  await expect(page.getByText("Strona 2 z 3", { exact: true })).toBeVisible();
  await expect(page.locator('[data-page-number="2"] canvas')).toBeVisible();
  await page
    .getByRole("button", { name: "Poprzednia strona", exact: true })
    .click();
  await checkGeometry(page);
  await page.setViewportSize({
    width: testInfo.project.name === "phone" ? 360 : 1000,
    height: 900,
  });
  await page
    .getByRole("button", { name: "Dopasuj do szerokości", exact: true })
    .click();
  await checkGeometry(page);
  await expect(page.locator('[contenteditable="true"]')).toHaveCount(0);
  await expect(
    page.getByRole("button", {
      name: /export|signature|add text|draw|delete page/i,
    }),
  ).toHaveCount(0);
  // Edytor standardowo dodaje obrazy przez drop; capture musi blokować tę ścieżkę.
  const dataTransfer = await page.evaluateHandle(() => {
    const data = new DataTransfer();
    data.items.add(
      new File([new Uint8Array([137, 80, 78, 71])], "test.png", {
        type: "image/png",
      }),
    );
    return data;
  });
  await page
    .locator('[data-page-number="1"]')
    .dispatchEvent("drop", { dataTransfer });
  await expect(page.locator(".rpe-image-frame")).toHaveCount(0);
  await dataTransfer.dispose();
  await expect(page.locator('[contenteditable="true"]')).toHaveCount(0);
  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => {
      document.documentElement.dataset.theme = value;
    }, theme);
    await expect(page.locator('[data-page-number="1"]')).toHaveCSS(
      "background-color",
      "rgb(255, 255, 255)",
    );
    const results = await new AxeBuilder({ page })
      .include(".pdf-viewer")
      .analyze();
    expect(
      results.violations.filter((v) =>
        ["serious", "critical"].includes(v.impact ?? ""),
      ),
    ).toEqual([]);
  }
  await page.getByRole("button", { name: "Miniatury", exact: true }).click();
  await expect(
    page.getByRole("complementary", { name: "Miniatury stron", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Przejdź do strony 2", exact: true })
    .click();
  await expect(page.getByText("Strona 2 z 3", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Miniatury", exact: true }).click();
  await page
    .getByRole("button", { name: "Poprzednia strona", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Wybierz dowód ze strony 2", exact: true })
    .click();
  await expect(page.getByText("Strona 2 z 3", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Poprzednia strona", exact: true })
    .click();
  const stage = page.getByRole("region", { name: "PDF pages", exact: true });
  await stage.focus();
  await stage.press("PageDown");
  await expect(page.getByText("Strona 2 z 3", { exact: true })).toBeVisible();
  await stage.press("ArrowLeft");
  await expect(page.getByText("Strona 1 z 3", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Tekst strony", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Tekst strony", exact: true }),
  ).toContainText("Belmoria");
  await page.screenshot({
    path: `/tmp/pdf-spike-${testInfo.project.name}.png`,
  });
  expect(external).toEqual([]);
});
test("shows a real raster-only scan and reports a missing PDF", async ({
  page,
}) => {
  await page.goto("/dev-pdf");
  await expect(page.locator('[data-page-number="1"] canvas')).toBeVisible();
  await page
    .getByLabel("Dokument demo", { exact: true })
    .selectOption("skan-odwolanie");
  await expect(page.getByText("Strona 1 z 1", { exact: true })).toBeVisible();
  await expect(page.locator('[data-page-number="1"] canvas')).toBeVisible();
  await expect(page.locator(".textLayer span")).toHaveCount(0);
  await page.getByRole("button", { name: "Tekst strony", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Tekst strony", exact: true }),
  ).toContainText("wymaga OCR");
  await page
    .getByLabel("Dokument demo", { exact: true })
    .selectOption("missing");
  await expect(page.locator(".pdf-viewer").getByRole("alert")).toBeVisible();
});
