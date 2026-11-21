import { beforeEach, describe, expect, it } from "vitest";
import type { ApiClient } from "../client";
import { buildExportJson, createMockClient, evaluateExport } from "./client";
import { seedDocuments } from "./data";

let api: ApiClient;
beforeEach(() => {
  api = createMockClient({ latencyMs: 0 });
});

describe("eksport według wariantu A (ścisła walidacja)", () => {
  const byId = (id: string) => seedDocuments().find((d) => d.id === id)!;

  it("pełny dokument: dozwolony, nazwa z nazwy bazowej", () => {
    const d = evaluateExport(byId("doc-1"));
    expect(d).toMatchObject({ allowed: true, fileName: "odwolanie-001.json" });
  });
  it("częściowy z pustym polem wymaganym: zablokowany", () => {
    const d = evaluateExport(byId("doc-3"));
    expect(d.allowed).toBe(false);
    expect(d.blockers.some((b) => b.code === "NULL_NOT_ALLOWED")).toBe(true);
  });
  it.each(["doc-5", "doc-6", "doc-8", "doc-9"])("%s: zablokowany, bez zastępczego {}", (id) => {
    const d = evaluateExport(byId(id));
    expect(d.allowed).toBe(false);
    expect(d.fileName).toBeNull();
  });
  it("obcy: dokładnie {}", () => {
    const d = byId("doc-7");
    expect(evaluateExport(d).allowed).toBe(true);
    expect(buildExportJson(d)).toBe("{}");
  });
  it("exportJson odrzuca zablokowany dokument", async () => {
    await expect(api.exportJson("doc-6")).rejects.toMatchObject({ code: "EXPORT_BLOCKED" });
  });
});

describe("mock klient", () => {
  it("filtruje i sortuje", async () => {
    const full = await api.listDocuments({ statuses: ["full"], sort: "name" });
    expect(full.every((d) => d.status === "full")).toBe(true);
    const names = full.map((d) => d.fileName);
    expect(names).toEqual([...names].sort((a, b) => a.localeCompare(b, "pl")));
    expect((await api.listDocuments({ search: "menu" })).map((d) => d.id)).toEqual(["doc-7"]);
  });
  it("wybór klasy dla niejednoznacznego dokumentu", async () => {
    const d = await api.chooseClass("doc-5", "odwolanie");
    expect(d.classId).toBe("odwolanie");
    expect(d.status).toBe("partial");
  });
  it("poprawka pola uzupełnia dokument do pełnego", async () => {
    await api.updateField("doc-3", "data_pisma", "2026-03-20");
    const d = await api.getDocument("doc-3");
    expect(d.status).toBe("full");
    expect((await api.getExportDecision("doc-3")).allowed).toBe(true);
  });
  it("nie-PDF jest odrzucony", async () => {
    await expect(api.addDocuments([{ name: "a.docx", sizeKb: 1, type: "application/msword" }])).rejects.toMatchObject({ code: "NOT_PDF" });
  });
  it("self-check zatrzymuje się na 401 bez ponowień", async () => {
    const bad = createMockClient({ latencyMs: 0, failKey: true });
    const steps = await bad.runSelfCheck(() => {});
    expect(steps.find((s) => s.id === "authorization")?.state).toBe("error");
    expect(steps.find((s) => s.id === "model")?.state).toBe("pending");
  });
});
