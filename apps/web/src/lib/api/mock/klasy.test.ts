import { describe, expect, it } from "vitest";
import { createClassMock } from "./klasy";
import {
  classSetVersionSchema,
  classTestSchema,
  classYamlSchema,
} from "../schemas";

const wait = async <T>(value: T) => structuredClone(value);

describe("class configuration mock", () => {
  it("reads contract definitions and validates response schemas", async () => {
    const api = createClassMock(wait);
    for (const id of ["odwolanie", "pelnomocnictwo", "przelew"]) {
      expect((await api.getClassDetail(id))?.id).toBe(id);
      expect(
        classYamlSchema.parse(await api.getClassYaml(id)).active,
      ).toContain(`id: ${id}`);
    }
    expect(await api.getClassDetail("unknown")).toBeNull();
    expect((await api.getClassYaml("unknown")).active).toBe("");
  });

  it("requires a current passing test before atomic activation", async () => {
    const api = createClassMock(wait);
    await expect(api.activateClassSet("v2")).rejects.toThrow(
      "wymagany poprawny test",
    );
    const result = await api.testClassDraft("przelew");
    expect(classTestSchema.parse(result).valid).toBe(true);
    expect(
      classSetVersionSchema.parse(await api.activateClassSet("v2")).active,
    ).toBe(true);
    expect(
      (await api.listClassVersions())
        .filter((version) => version.active)
        .map((version) => version.version),
    ).toEqual(["v2"]);
    expect((await api.getClassDetail("przelew"))?.version).toBe("v2");
    expect((await api.getClassDetail("przelew"))?.fields.at(-1)?.key).toBe(
      "oznaczenie_sprawy",
    );
    expect((await api.getClassYaml("przelew")).active).toContain("wersja: 2");
    expect((await api.getClassYaml("przelew")).draft).toBeNull();
  });

  it("reports line 14 and leaves the previous set active", async () => {
    const api = createClassMock(wait, "invalid");
    expect((await api.testClassDraft("przelew")).issues).toContain(
      "Linia 14: brak normalizatora",
    );
    await expect(api.activateClassSet("v2")).rejects.toThrow();
    expect(
      (await api.listClassVersions()).find((version) => version.active)
        ?.version,
    ).toBe("v1");
  });

  it("preserves v1 after activation failure and allows retry", async () => {
    const api = createClassMock(wait, "activation-error");
    await api.testClassDraft("przelew");
    await expect(api.activateClassSet("v2")).rejects.toThrow(
      "Nie aktywowano. Nadal aktywny v1. Ponów",
    );
    expect(
      (await api.listClassVersions()).find((version) => version.active)
        ?.version,
    ).toBe("v1");
    expect((await api.activateClassSet("v2")).active).toBe(true);
  });

  it("rejects concurrent activation and exposes missing configuration", async () => {
    const api = createClassMock(
      (value) => new Promise((resolve) => setTimeout(() => resolve(value), 10)),
    );
    await api.testClassDraft("przelew");
    const first = api.activateClassSet("v2");
    await expect(api.activateClassSet("v2")).rejects.toThrow("już trwa");
    await first;
    expect(
      await createClassMock(wait, "no-configuration").listClassVersions(),
    ).toEqual([]);
  });
});
