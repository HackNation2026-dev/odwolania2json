import { describe, expect, it } from "vitest";
import { createMockClient } from "./client";
import { documentSchema } from "../schemas";
describe("batch plans and path collisions", () => {
  it("includes three validated results and omits three failures without substitute JSON", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const plan = await api.getBatchExportPlan("B-01");
    expect(plan.included).toHaveLength(3);
    expect(plan.omitted).toHaveLength(3);
    expect(plan.included.map((e) => e.status)).toEqual([
      "full",
      "partial",
      "foreign",
    ]);
    for (const entry of plan.omitted) {
      expect(entry.reasons.length).toBeGreaterThan(0);
      await expect(api.exportJson(entry.documentId)).rejects.toThrow();
    }
    const foreign = await api.exportJson("doc-7");
    expect(foreign.json).toBe("{}");
    expect(plan.included[1]!.outputPath).toMatch(/^output\/sprawa-a\//);
  });
  it("rejects an invalid batch and returns isolated batch reads", async () => {
    const api = createMockClient({ latencyMs: 0 });
    await expect(api.getBatchExportPlan("absent")).rejects.toThrow();
    const batches = await api.listBatches();
    batches[0]!.entries.length = 0;
    expect((await api.listBatches())[0]!.entries).toHaveLength(6);
  });
  it("detects existing paths and duplicate paths inside a selection", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const file = { name: "fresh.pdf", sizeKb: 2, type: "application/pdf" };
    expect(await api.checkPathCollision([file])).toEqual([]);
    expect(
      await api.checkPathCollision([file, { ...file, sizeKb: 4 }]),
    ).toEqual([
      { path: "fresh.pdf", incomingIndex: 1, existingDocumentId: null },
    ]);
    expect(
      (await api.checkPathCollision([{ ...file, name: "odwolanie.pdf" }]))[0]!
        .existingDocumentId,
    ).toBe("doc-1");
  });
  it("preserves originals and names when creating a version or separate package", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const original = await api.getDocument("doc-1");
    const files = [
      { name: original.fileName, sizeKb: 2, type: "application/pdf" },
    ];
    const [version] = await api.addResolvedDocuments({
      files,
      choice: "version",
    });
    expect(documentSchema.parse(version).fileName).toBe(original.fileName);
    expect(version!.resultVersion).toBe(original.resultVersion + 1);
    expect(version!.batchId).toBe(original.batchId);
    expect((await api.getVersions("doc-1")).documents).toHaveLength(2);
    expect((await api.getVersions("doc-1")).results[0]!.version).toBe(1);
    expect((await api.getDocument("doc-1")).fileName).toBe(original.fileName);
    const [separate] = await api.addResolvedDocuments({
      files,
      choice: "package",
    });
    expect(separate!.batchId).not.toBe(original.batchId);
    expect(separate!.fileName).not.toContain("(2)");
    expect((await api.getVersions(version!.id)).results.at(-1)!.version).toBe(
      version!.resultVersion,
    );
  });
});
