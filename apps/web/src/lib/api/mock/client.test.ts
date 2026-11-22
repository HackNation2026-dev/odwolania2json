import { beforeEach, describe, expect, it } from "vitest";
import type { ApiClient } from "../client";
import { buildExportJson, createMockClient, evaluateExport } from "./client";
import { seedDocuments } from "./data";

let api: ApiClient;
beforeEach(() => {
  api = createMockClient({ latencyMs: 0 });
});

describe("variant A strict export validation", () => {
  const byId = (id: string) => seedDocuments().find((d) => d.id === id)!;

  it("allows complete document with input basename", () => {
    const d = evaluateExport(byId("doc-1"));
    expect(d).toMatchObject({ allowed: true, fileName: "odwolanie.json" });
  });
  it("partial nullable fields remain exportable", () => {
    const d = evaluateExport(byId("doc-3"));
    expect(d.allowed).toBe(true);
    expect(d.blockers).toEqual([]);
  });
  it.each(["doc-5", "doc-6", "doc-8", "doc-9"])("blocks %s without substitute empty JSON", (id) => {
    const d = evaluateExport(byId(id));
    expect(d.allowed).toBe(false);
    expect(d.fileName).toBeNull();
  });
  it("exports exactly an empty object for a foreign document", () => {
    const d = byId("doc-7");
    expect(evaluateExport(d).allowed).toBe(true);
    expect(buildExportJson(d)).toBe("{}");
  });
  it("rejects export for a blocked document", async () => {
    await expect(api.exportJson("doc-6")).rejects.toMatchObject({ code: "EXPORT_BLOCKED" });
  });
});

describe("mock client", () => {
  it("filters and sorts documents", async () => {
    const full = await api.listDocuments({ statuses: ["full"], sort: "name" });
    expect(full.every((d) => d.status === "full")).toBe(true);
    const names = full.map((d) => d.fileName);
    expect(names).toEqual([...names].sort((a, b) => a.localeCompare(b, "pl")));
    expect((await api.listDocuments({ search: "menu" })).map((d) => d.id)).toEqual(["doc-7"]);
  });
  it("reextracts an ambiguous document with the selected class", async () => {
    const d = await api.chooseClass("doc-5", "odwolanie");
    expect(d.classId).toBe("odwolanie");
    expect(d.status).toBe("full");
  });
  it("keeps unprocessed coverage partial after field correction", async () => {
    await api.updateField("doc-3", "OdwolanieKIO.data", "2026-03-20");
    const d = await api.getDocument("doc-3");
    expect(d.status).toBe("partial");
    expect((await api.getExportDecision("doc-3")).allowed).toBe(true);
  });
  it("rejects non-PDF files", async () => {
    await expect(api.addDocuments([{ name: "a.docx", sizeKb: 1, type: "application/msword" }])).rejects.toMatchObject({ code: "NOT_PDF" });
  });
  it("stops self-check on 401 without retries", async () => {
    const bad = createMockClient({ latencyMs: 0, failKey: true });
    const steps = await bad.runSelfCheck(() => {});
    expect(steps.find((s) => s.id === "authorization")?.state).toBe("error");
    expect(steps.find((s) => s.id === "model")?.state).toBe("pending");
  });
});
