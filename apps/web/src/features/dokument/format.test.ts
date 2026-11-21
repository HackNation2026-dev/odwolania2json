import { describe, expect, it } from "vitest";
import { seedDocuments } from "@/lib/api/mock/data";
import { formatDocumentJson, parseFieldValue, partialReasons } from "./format";

describe("document presentation formatting", () => {
  it("preserves field keys and types without evidence metadata", () => {
    const result = formatDocumentJson(seedDocuments()[0]!);
    expect(JSON.parse(result!)).toEqual({ sygnatura: "SKO-2026/114", data_pisma: "2026-03-20", organ: "Samorządowe Kolegium Odwoławcze", wnioskodawca: "Anna Kowalska", kwota: 4200 });
    expect(result).toContain('\n  "sygnatura"');
  });
  it("returns exactly an empty object only for foreign documents", () => {
    const docs = seedDocuments();
    expect(formatDocumentJson(docs.find(d => d.status === "foreign")!)).toBe("{}");
    for (const status of ["error", "ambiguous", "multi", "running"]) expect(formatDocumentJson(docs.find(d => d.status === status)!)).toBeNull();
  });
  it("maps all five partial reasons to Polish descriptions", () => {
    expect(Object.keys(partialReasons)).toEqual(["ocr_unavailable", "unreadable_scan", "missing_field", "low_confidence", "page_limit"]);
    for (const reason of Object.values(partialReasons)) { expect(reason.label.length).toBeGreaterThan(5); expect(reason.description.length).toBeGreaterThan(20); }
  });
  it("validates dates and numbers and keeps null explicit", () => {
    const fields = seedDocuments()[0]!.fields;
    expect(() => parseFieldValue(fields[1]!, "2026-02-30")).toThrow("prawidłową datę");
    expect(() => parseFieldValue(fields[4]!, "abc")).toThrow("liczbę");
    expect(parseFieldValue(fields[4]!, "12,50")).toBe(12.5);
    expect(parseFieldValue(fields[1]!, "")).toBeNull();
    expect(parseFieldValue(fields[1]!, "2026-03-20")).toBe("2026-03-20");
  });
});
