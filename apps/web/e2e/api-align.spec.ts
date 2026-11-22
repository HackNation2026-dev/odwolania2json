import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";

test("shows real pipeline states and OCR region diagnosis", async ({ page }) => {
  await page.goto("/dokumenty/doc-9");
  const pipeline = page.locator("details").filter({ has: page.locator("summary", { hasText: /^Przebieg przetwarzania$/ }) });
  await pipeline.locator("summary").click();
  await expect(pipeline).toContainText("w toku");
  await expect(pipeline).toContainText("oczekuje");
  await page.goto("/dokumenty/doc-4");
  await page.getByRole("button", { name: "Diagnoza dokumentu, stron i regionów" }).click();
  const diagnosis = page.getByRole("dialog", { name: "Diagnoza", exact: true });
  await expect(diagnosis).toBeVisible();
  await diagnosis.getByRole("tab", { name: "Strona", exact: true }).click();
  await diagnosis.getByRole("combobox", { name: "Strona", exact: true }).selectOption("2");
  const pageDiagnosis = diagnosis.getByRole("tabpanel", { name: "Strona", exact: true });
  await expect(pageDiagnosis.getByText("OCR", { exact: true })).toBeVisible();
  await diagnosis.getByRole("tab", { name: "Region", exact: true }).click();
  await diagnosis.getByRole("combobox", { name: "Strona regionu" }).selectOption("2");
  await diagnosis.getByRole("combobox", { name: "Region", exact: true }).selectOption("R3");
  const region = diagnosis.getByRole("tabpanel", { name: "Region", exact: true });
  await expect(region.getByText("OCR", { exact: true })).toBeVisible();
  await expect(region.getByText("zla_warstwa_ocr", { exact: true })).toBeVisible();
  await expect(region).toContainText("tekst warstwy niezgodny z obrazem");
});

test("compares and restores immutable result versions", async ({ page }) => {
  await page.goto("/dokumenty/doc-1");
  await page.getByText("Historia i porównanie wersji", { exact: true }).click();
  await page.getByLabel("Wersja po").selectOption("2");
  await expect(page.getByText(/Było: 999136-2026/)).toContainText("Jest: 999137-2026");
  await page.getByRole("button", { name: "Przywróć v1 jako nową wersję" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Utworzono nową wersję wyniku" })).toBeVisible();
  await expect(page.getByText(/Wynik v4/)).toBeVisible();
  const downloading = page.waitForEvent("download");
  await page.getByRole("button", { name: "Pobierz JSON", exact: true }).click();
  const download = await downloading;
  const json = JSON.parse(await readFile((await download.path())!, "utf8"));
  expect(json.ZamowieniePubliczne.numer_ted).toBe("999136-2026");
  expect(json.Odwolujacy[0]["przez-pelnomocnika"]).toBe(1);
  expect(json).not.toHaveProperty("evidence");
});
