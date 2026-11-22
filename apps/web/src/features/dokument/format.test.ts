import { describe, expect, it } from "vitest";
import { seedDocuments } from "@/lib/api/mock/data";
import { formatDocumentJson, parseFieldValue, partialReasons } from "./format";

describe("document presentation formatting", () => {
  it("preserves field keys and types without evidence metadata", () => {
    const result = formatDocumentJson(seedDocuments()[0]!);
    expect(JSON.parse(result!)).toHaveProperty("ZamowieniePubliczne.numer_bzp", "2026/BZP00999778");
    expect(result).toContain("Odwolujacy");
  });
  it("returns exactly an empty object only for foreign documents", () => {
    const docs = seedDocuments();
    expect(formatDocumentJson(docs.find(d => d.status === "foreign")!)).toBe("{}");
    for (const status of ["error", "ambiguous", "multi", "running"]) expect(formatDocumentJson(docs.find(d => d.status === status)!)).toBeNull();
  });
  it("maps all five partial reasons to Polish descriptions", () => {
    expect(Object.keys(partialReasons)).toEqual(["missing", "not_applicable", "unreadable", "conflicting", "unprocessed"]);
    for (const reason of Object.values(partialReasons)) { expect(reason.label.length).toBeGreaterThan(3); expect(reason.description.length).toBeGreaterThan(20); }
  });
  it("validates dates and numbers and keeps null explicit", () => {
    const fields = seedDocuments()[0]!.fields;
    expect(() => parseFieldValue(fields[1]!, "2026-02-30")).toThrow("prawidłową datę");
    expect(() => parseFieldValue(seedDocuments()[9]!.fields.find(f => f.key.endsWith("kwota"))!, "abc")).toThrow("liczbę");
    expect(parseFieldValue(seedDocuments()[9]!.fields.find(f => f.key.endsWith("kwota"))!, "12,50")).toBe(12.5);
    expect(parseFieldValue(fields[1]!, "")).toBeNull();
    expect(parseFieldValue(fields[1]!, "2026-03-20")).toBe("2026-03-20");
  });
});
