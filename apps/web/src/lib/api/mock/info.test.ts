import { describe, expect, it } from "vitest";
import { eventRecordSchema, systemInfoSchema, userRecordSchema } from "../schemas";
import { createMockClient } from "./client";

describe("mock system information and users", () => {
  it("returns validated synthetic events with masked corrections and isolated reads", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const events = (await api.listEvents()).map((event) => eventRecordSchema.parse(event));
    expect(events).toHaveLength(6);
    expect(events.find((event) => event.type === "correction")?.detail).toContain("Było: •••; Jest: •••");
    expect(new Set(events.map((event) => event.result))).toEqual(new Set(["success", "blocked", "error"]));
    events[0]!.description = "Zmieniono";
    expect((await api.listEvents())[0]!.description).not.toBe("Zmieniono");
  });
  it("returns validated metadata without inventing confirmations", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const info = systemInfoSchema.parse(await api.getSystemInfo());
    expect(info.demo).toBe(true);
    expect(info.largestModel).toBeNull();
    expect(info.models[0]!.serverCountry).toBeNull();
    expect(info.ocr.mode).toBe("shim");
    info.models[0]!.name = "Zmieniono";
    expect((await api.getSystemInfo()).models[0]!.name).not.toBe("Zmieniono");
  });
  it("returns synthetic users covering every displayed status", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const users = (await api.listUsers()).map((user) => userRecordSchema.parse(user));
    expect(users).toHaveLength(5);
    expect(new Set(users.map((user) => user.status)).size).toBe(3);
    expect(users.every((user) => user.email.endsWith("@example.test"))).toBe(true);
  });
});
