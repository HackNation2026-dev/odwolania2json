import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { getDocument } from "pdfjs-dist/legacy/build/pdf.mjs";
for (const name of [
  "odwolanie",
  "pelnomocnictwo",
  "przelew",
  "skan-odwolanie",
]) {
  const pdf = await getDocument({
    data: new Uint8Array(await readFile(`public/demo-pdf/${name}.pdf`)),
  }).promise;
  const geometry = JSON.parse(
    await readFile(`public/demo-pdf/${name}.json`, "utf8"),
  ) as {
    page: number;
    label: string;
    box: { x: number; y: number; w: number; h: number };
  }[];
  assert.equal(pdf.numPages, name === "odwolanie" ? 3 : 1);
  for (let page = 1; page <= pdf.numPages; page++) {
    const p = await pdf.getPage(page);
    const viewport = p.getViewport({ scale: 1 });
    assert(
      Math.abs(viewport.width - 595.28) < 0.1 &&
        Math.abs(viewport.height - 841.89) < 0.1,
      "Nieprawidłowy rozmiar strony A4",
    );
    const content = await p.getTextContent();
    if (name === "skan-odwolanie") {
      assert.equal(content.items.length, 0);
      continue;
    }
    const { width, height } = p.getViewport({ scale: 1 });
    for (const fragment of geometry.filter((h) => h.page === page)) {
      const item = content.items.find(
        (i) => "str" in i && i.str === fragment.label,
      );
      assert(item && "str" in item, `Brak tekstu ${fragment.label}`);
      const box = fragment.box;
      const style = content.styles[item.fontName]!;
      const x = item.transform[4],
        top =
          height -
          item.transform[5] -
          (item.height * style.ascent) / (style.ascent - style.descent);
      assert(Math.abs(box.x * width - x) < 0.1);
      assert(Math.abs(box.y * height - top) < 0.1);
      assert(Math.abs(box.w * width - item.width) < 0.1);
      assert(Math.abs(box.h * height - item.height) < 0.1);
      assert(Object.values(box).every((v) => v >= 0 && v <= 1));
      // Niezależny kontrakt generatora: każdy akapit zaczyna się 48 pt od lewej.
      assert(Math.abs(x - 48) < 0.1);
    }
  }
  await pdf.destroy();
  console.log(`${name}: geometria i liczba stron poprawne`);
}
