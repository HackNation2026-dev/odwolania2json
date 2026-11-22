import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const theme of ["light", "dark"] as const) {
  test(`synchronizes real PDF evidence, page text and diagnosis in ${theme}`, async ({
    page,
  }, info) => {
    test.setTimeout(90_000);
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/dokumenty/doc-1");
    await expect(
      page.getByRole("heading", { name: "odwolanie.pdf", exact: true }),
    ).toBeVisible();
    if (info.project.name === "phone") {
      await page.getByRole("link", { name: "Dokument", exact: true }).click();
    }
    const pdf = page.getByRole("region", { name: /Strona PDF/ });
    await expect(pdf.locator('[data-page-number="1"] canvas')).toBeVisible({
      timeout: 30_000,
    });
    // Znajdź rzeczywisty obrys numeru BZP niezależnie od kolejności pozostałych pól kontraktu.
    const target = pdf.getByRole("button", {
      name: /Dowód.*ZamowieniePubliczne.numer_bzp/,
    });
    await expect(target).toBeVisible();
    await expect(pdf.locator('[data-page-number="1"]')).toHaveCSS(
      "background-color",
      "rgb(255, 255, 255)",
    );
    const contrast = await target.evaluate((element) => {
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = 1;
      const context = canvas.getContext("2d")!;
      context.fillStyle = getComputedStyle(element).borderColor;
      context.fillRect(0, 0, 1, 1);
      const channels = [...context.getImageData(0, 0, 1, 1).data]
        .slice(0, 3)
        .map((channel) => {
          const value = channel / 255;
          return value <= 0.04045
            ? value / 12.92
            : ((value + 0.055) / 1.055) ** 2.4;
        });
      const luminance =
        channels[0]! * 0.2126 + channels[1]! * 0.7152 + channels[2]! * 0.0722;
      return 1.05 / (luminance + 0.05);
    });
    expect(contrast).toBeGreaterThanOrEqual(3);
    await target.click();
    await expect(target).toHaveAttribute("aria-pressed", "true");
    await expect(
      page.getByRole("link", { name: /Wróć do pola Numer BZP/ }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Tekst strony", exact: true })
      .click();
    const text = page.getByRole("region", {
      name: "Tekst odczytany ze strony",
    });
    await expect(text).toContainText("Numer ogłoszenia BZP: 2026/BZP00999778");
    if (info.project.name === "phone")
      await page.getByRole("link", { name: /Wróć do pola Numer BZP/ }).click();
    await page
      .getByRole("button", { name: "Diagnoza dokumentu, stron i regionów" })
      .click();
    await expect(
      page.getByRole("dialog", { name: "Diagnoza", exact: true }),
    ).toBeVisible();
    await page.getByRole("tab", { name: "Strona", exact: true }).click();
    await expect(
      page
        .getByRole("tabpanel", { name: "Strona", exact: true })
        .getByText("OCR niewymagany"),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await page.setViewportSize({ width: 320, height: 800 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter((item) =>
        ["serious", "critical"].includes(item.impact ?? ""),
      ),
    ).toEqual([]);
  });

  test(`keeps OCR and export limitations explicit in ${theme}`, async ({
    page,
  }, info) => {
    test.setTimeout(90_000);
    await page.addInitScript(
      (value) => localStorage.setItem("o2j-theme", value),
      theme,
    );
    await page.goto("/dokumenty/doc-4");
    if (info.project.name === "phone")
      await page.getByRole("link", { name: "Dokument", exact: true }).click();
    await page
      .getByRole("button", { name: "Tekst strony", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Strona 1 · Skan — tekst z OCR" }),
    ).toBeVisible();
    await expect(
      page.getByText(
        "Niska jakość odczytu OCR na tej stronie. Porównaj fragment z dokumentem.",
      ),
    ).toBeVisible();
    await page.goto("/dokumenty/doc-6?tab=json");
    await expect(
      page.getByRole("button", { name: "Pobierz JSON", exact: true }),
    ).toBeDisabled();
    await expect(page.getByText("Brak ocenianego JSON")).toBeVisible();
    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter((item) =>
        ["serious", "critical"].includes(item.impact ?? ""),
      ),
    ).toEqual([]);
  });
}
