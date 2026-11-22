import { describe, expect, it } from "vitest";
import { createMockClient } from "./client";
import { compareVersions } from "../processing";

describe("processing, diagnosis and immutable result versions", () => {
  it("returns finished counts, waiting steps and the actual failed stage", async () => {
    const api = createMockClient({ latencyMs: 0 });
    expect((await api.getPipeline("doc-1")).stages.find(s => s.id === "T1")?.counts).toMatchObject({ className: "Odwołanie do KIO" });
    expect((await api.getPipeline("doc-9")).stages[0]?.state).toBe("w toku");
    expect((await api.getPipeline("doc-9")).stages[1]?.counts).toBeNull();
    expect((await api.getPipeline("doc-6")).stages.find(s => s.state === "błąd")).toMatchObject({ id: "T3", errorCode: "LLM_TIMEOUT" });
    await expect(api.getPipeline("missing")).rejects.toMatchObject({ code: "NOT_FOUND" });
  });
  it("exposes OCR regions and preserves unprocessed coverage", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const diagnosis = await api.getDiagnosis("doc-4");
    expect(diagnosis.pages[1]?.regions?.[0]).toMatchObject({ id: "R3", rotation_degrees: 90, codes: ["zla_warstwa_ocr"] });
    expect((await api.getDiagnosis("doc-3")).pages[1]).toMatchObject({ text_source: "none", coverage: 0 });
  });
  it("compares versions and restores by appending without altering history", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const before = await api.getVersions("doc-1");
    expect(before.results.map(v => v.kind)).toEqual(["silnik", "korekta", "zatwierdzony"]);
    expect(compareVersions(before.results[0]!, before.results[1]!)).toEqual([{ key: "ZamowieniePubliczne.numer_ted", before: "999136-2026", after: "999137-2026" }]);
    const restored = await api.restoreVersion("doc-1", 1);
    expect(restored.resultVersion).toBe(4);
    const after = await api.getVersions("doc-1");
    expect(after.results.slice(0, 3)).toEqual(before.results);
    expect(after.results[3]).toMatchObject({ restoredFrom: 1, kind: "przywrócenie" });
    expect(JSON.parse((await api.exportJson("doc-1")).json).ZamowieniePubliczne.numer_ted).toBe("999136-2026");
    await expect(api.restoreVersion("doc-1", 99)).rejects.toMatchObject({ code: "NOT_FOUND" });
  });
});
