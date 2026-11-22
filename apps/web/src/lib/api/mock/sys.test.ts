import { describe, expect, it } from "vitest";
import { createMockClient } from "./client";

describe("system mock", () => {
  it("validates retention against the server range and isolates clients", async () => {
    const api = createMockClient({ latencyMs: 0 });
    for (const days of [0, 366, 1.5, NaN, Infinity])
      await expect(api.saveRetention(days)).rejects.toThrow("Podaj liczbę dni");
    expect(await api.saveRetention(1)).toMatchObject({
      days: 1,
      minDays: 1,
      maxDays: 365,
    });
    expect(await api.saveRetention(365)).toMatchObject({ days: 365 });
    expect(
      await createMockClient({ latencyMs: 0 }).getRetentionSettings(),
    ).toMatchObject({ days: 30 });
  });
  it("filters audit events and exports masked values only", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const changes = await api.listAuditEvents({
      type: "correction",
      object: "odwolanie",
      date: "2026-10-14",
    });
    expect(changes).toHaveLength(1);
    expect(changes[0]?.detail).toContain("Było: •••••••• / Jest: ••••••••");
    expect(await api.listAuditEvents({ user: "nie-istnieje" })).toEqual([]);
    const csv = await api.exportAuditCsv({ type: "reveal" });
    expect(csv.fileName).toBe("dziennik-demo.csv");
    expect(csv.csv).toContain("Wartość nie jest zapisana w dzienniku");
    expect(csv.csv).not.toContain("85120133547");
    const events = await api.listAuditEvents();
    events[0]!.detail = "zmiana klienta";
    expect((await api.listAuditEvents())[0]?.detail).not.toBe("zmiana klienta");
  });
  it("returns readiness metadata consistent with system info", async () => {
    const api = createMockClient({ latencyMs: 0 });
    expect(await api.getReadiness()).toEqual(await api.getSystemInfo());
  });
});
