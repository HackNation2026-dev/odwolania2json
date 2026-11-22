import { describe, expect, it } from "vitest";
import { seedDocuments } from "@/lib/api/mock/data";
import {
  emptyFilters,
  filterDocuments,
  parseFilters,
  serializeFilters,
} from "./filters";

describe("document URL filters", () => {
  it("parses dashboard links, repeated and comma-separated statuses", () => {
    expect(parseFilters(new URLSearchParams("status=full")).statuses).toEqual([
      "full",
    ]);
    expect(
      parseFilters(
        new URLSearchParams("status=full,partial&status=full&status=invalid"),
      ).statuses,
    ).toEqual(["full", "partial"]);
  });
  it("roundtrips filters and Polish query strings", () => {
    const f = {
      ...emptyFilters,
      q: "zażółć & plik.pdf",
      statuses: ["full", "error"] as const,
      klasa: "przelew",
      sort: "name" as const,
      widok: "tabela" as const,
      codes: ["information_not_explicit"],
      attention: true,
      source: "ocr",
    };
    const value = { ...f, statuses: [...f.statuses] };
    expect(parseFilters(serializeFilters(value))).toEqual(value);
  });
  it("ignores invalid values and omits defaults", () => {
    expect(
      parseFilters(
        new URLSearchParams("sort=invalid&widok=invalid&source=invalid"),
      ),
    ).toEqual({ ...emptyFilters, widok: undefined });
    expect(serializeFilters(emptyFilters).toString()).toBe("");
  });
  it("combines filters and sorts predictably", () => {
    const docs = seedDocuments();
    expect(
      filterDocuments(docs, {
        ...emptyFilters,
        statuses: ["full"],
        klasa: "przelew",
      }).map((d) => d.id),
    ).toEqual(["doc-10"]);
    expect(
      filterDocuments(docs, { ...emptyFilters, sort: "name" })[0]?.fileName,
    ).toBe("menu-restauracji.pdf");
    expect(
      filterDocuments(docs, { ...emptyFilters, sort: "oldest" })[0]?.id,
    ).toBe("doc-1");
    expect(
      filterDocuments(docs, { ...emptyFilters, sort: "status" })[0]?.status,
    ).toBe("error");
    expect(
      filterDocuments(docs, {
        ...emptyFilters,
        q: "WODOCIAGI",
        statuses: ["full"],
      }),
    ).toHaveLength(1);
    expect(
      filterDocuments(docs, {
        ...emptyFilters,
        codes: ["ocr_unavailable", "scan"],
      }),
    ).toHaveLength(2);
  });
});
