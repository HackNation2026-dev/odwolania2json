import { describe, expect, it } from "vitest";
import appeal from "../../../../public/demo-pdf/odwolanie.json";
import scan from "../../../../public/demo-pdf/skan-odwolanie.json";
import { seedDocuments } from "./data";
import { documentPdfFile } from "./document-pdf";

describe("document PDF fixtures", () => {
  it("chooses a real demo asset for every mock document class", () => {
    const docs = seedDocuments();
    expect(documentPdfFile(docs[0]!)).toBe("/demo-pdf/odwolanie.pdf");
    expect(documentPdfFile(docs[3]!)).toBe("/demo-pdf/skan-odwolanie.pdf");
    expect(documentPdfFile(docs[9]!)).toBe("/demo-pdf/przelew.pdf");
    expect(documentPdfFile(docs[10]!)).toBe("/demo-pdf/pelnomocnictwo.pdf");
    for (const doc of docs)
      expect(documentPdfFile(doc)).toMatch(/^\/demo-pdf\/.+\.pdf$/);
  });
  it("uses verified text geometry and leaves absent values without invented boxes", () => {
    for (const doc of seedDocuments().filter(
      (doc) => doc.classId === "odwolanie",
    )) {
      const geometry = doc.id === "doc-4" ? scan : appeal;
      for (const item of doc.evidence.filter((item) => item.box)) {
        const region = geometry.find((region) => region.label === item.quote);
        expect(region).toBeDefined();
        expect(item.box).toEqual(region!.box);
        expect(item.page).toBe(region!.page);
      }
      const absent = doc.evidence.find(
        (item) => item.fieldKey === "OdwolanieKIO.data",
      );
      if (absent) expect(absent.box).toBeUndefined();
    }
  });
  it("keeps field associations and source metadata intact", () => {
    const doc = seedDocuments()[3]!;
    for (const item of doc.evidence) {
      expect(
        doc.fields.some((field) => field.evidenceIds.includes(item.id)),
      ).toBe(true);
      expect(item.source).toBe("ocr");
      expect(item.confidence).toBe(0.74);
    }
  });
});
