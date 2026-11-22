/** Dane wyłącznie syntetyczne. Poppler jest potrzebny tylko do utworzenia skanu. */
import React from "react";
import {
  Document,
  Page,
  Text,
  Image,
  Font,
  renderToBuffer,
} from "@react-pdf/renderer";
import { readFile, writeFile, mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { getDocument } from "pdfjs-dist/legacy/build/pdf.mjs";
const W = 595.28,
  H = 841.89;
const dir = "public/demo-pdf";
Font.register({ family: "Demo", src: `${dir}/NotoSans-Regular.ttf` });
const date = new Date("2026-01-01T00:00:00Z");
const content: Record<string, string[][]> = {
  odwolanie: [
    [
      "Krajowa Izba Odwoławcza",
      "ul. Postępu 17A, 02-676 Warszawa",
      "ODWOŁANIE",
      "Odwołujący: Belmoria Rozwiązania S.A.",
      "Zamawiający: Aurelink Automatyka S.A.",
      "Numer ogłoszenia BZP: 2026/BZP00999778",
      "Numer ogłoszenia TED: 999137-2026",
      "Przedmiot: dostawa systemu automatyki budynkowej",
      "Wartość zamówienia: 2 450 000,00 PLN",
      "Dokument demonstracyjny. Wszystkie dane są syntetyczne.",
    ],
    [
      "ODWOŁANIE - zarzuty",
      "Zarzut: niezgodne z warunkami odrzucenie oferty.",
      "Podstawa prawna: art. 226 ust. 1 pkt 5 ustawy Pzp.",
      "Żądanie: unieważnienie czynności odrzucenia oferty.",
      "Uzasadnienie: oferta spełnia wymagania zamawiającego.",
      "Dokument demonstracyjny. Wszystkie dane są syntetyczne.",
    ],
    [
      "ODWOŁANIE - załączniki",
      "1. Pełnomocnictwo",
      "2. Potwierdzenie przelewu wpisu",
      "3. Dokumentacja postępowania",
      "Podpis: pełnomocnik odwołującego",
      "Dokument demonstracyjny. Wszystkie dane są syntetyczne.",
    ],
  ],
  pelnomocnictwo: [
    [
      "PEŁNOMOCNICTWO",
      "Belmoria Rozwiązania S.A.",
      "Udziela pełnomocnictwa do wniesienia odwołania.",
      "Pełnomocnik: Anna Przykładowa",
      "Data: 15 listopada 2026 r.",
      "Dokument demonstracyjny. Wszystkie dane są syntetyczne.",
    ],
  ],
  przelew: [
    [
      "POTWIERDZENIE PRZELEWU",
      "Nadawca: Belmoria Rozwiązania S.A.",
      "Odbiorca: Urząd Zamówień Publicznych",
      "Kwota: 15 000,00 PLN",
      "Tytuł: wpis od odwołania, TED 999137-2026",
      "Data operacji: 15 listopada 2026 r.",
      "Dokument demonstracyjny. Wszystkie dane są syntetyczne.",
    ],
  ],
};
function document(pages: React.ReactNode[]) {
  return React.createElement(
    Document,
    {
      title: "Syntetyczny dokument demo",
      author: "Arkadiana",
      creationDate: date,
      modificationDate: date,
    },
    ...pages,
  );
}
function textPage(lines: string[], index: number) {
  return React.createElement(
    Page,
    { size: [W, H], key: index, style: { fontFamily: "Demo" } },
    ...lines.map((line, i) =>
      React.createElement(
        Text,
        {
          key: i,
          style: {
            position: "absolute",
            left: 48,
            top: 48 + i * 38,
            fontSize: i === 2 && index === 0 ? 18 : 11,
            width: 500,
          },
        },
        line,
      ),
    ),
  );
}
export async function geometry(bytes: Uint8Array) {
  const pdf = await getDocument({ data: bytes, useSystemFonts: true }).promise;
  const fragments = [];
  for (let page = 1; page <= pdf.numPages; page++) {
    const p = await pdf.getPage(page);
    const viewport = p.getViewport({ scale: 1 });
    const text = await p.getTextContent();
    for (const item of text.items) {
      if (!("str" in item) || !item.str.trim()) continue;
      // Geometria pochodzi z rzeczywistych metryk osadzonego fontu i macierzy PDF.
      const style = text.styles[item.fontName];
      // Tak jak PDF.js TextLayer: ascent jako udział pełnej wysokości em (ascent + |descent|).
      const ascent = style ? style.ascent / (style.ascent - style.descent) : 1;
      fragments.push({
        id: `p${page}-${fragments.length + 1}`,
        page,
        label: item.str,
        box: {
          x: item.transform[4] / viewport.width,
          y:
            (viewport.height - item.transform[5] - item.height * ascent) /
            viewport.height,
          w: item.width / viewport.width,
          h: item.height / viewport.height,
        },
      });
    }
  }
  await pdf.destroy();
  return fragments;
}
for (const [name, pages] of Object.entries(content)) {
  const bytes = await renderToBuffer(document(pages.map(textPage)));
  await writeFile(`${dir}/${name}.pdf`, bytes);
  await writeFile(
    `${dir}/${name}.json`,
    JSON.stringify(await geometry(new Uint8Array(bytes)), null, 2) + "\n",
  );
}
const temp = await mkdtemp(join(tmpdir(), "pdf-demo-"));
try {
  execFileSync("pdftoppm", [
    "-f",
    "1",
    "-singlefile",
    "-scale-to",
    "1400",
    "-png",
    `${dir}/odwolanie.pdf`,
    join(temp, "scan"),
  ]);
  const bytes = await renderToBuffer(
    document([
      React.createElement(
        Page,
        { size: [W, H], key: "scan" },
        React.createElement(Image, {
          fixed: true,
          src: await readFile(join(temp, "scan.png")),
          style: { position: "absolute", left: 0, top: 0, width: W, height: H },
        }),
      ),
    ]),
  );
  await writeFile(`${dir}/skan-odwolanie.pdf`, bytes);
  const fragments = await geometry(new Uint8Array(bytes));
  if (fragments.length)
    throw new Error("Skan nie może zawierać warstwy tekstowej");
  // Skan zachowuje identyczną geometrię po rasteryzacji całej strony.
  const original = JSON.parse(await readFile(`${dir}/odwolanie.json`, "utf8"));
  await writeFile(
    `${dir}/skan-odwolanie.json`,
    JSON.stringify(
      original.filter((item: { page: number }) => item.page === 1),
      null,
      2,
    ) + "\n",
  );
} finally {
  await rm(temp, { recursive: true, force: true });
}
console.log(
  "Wygenerowano 4 syntetyczne PDF-y i ich geometrię; skan bez tekstu.",
);
