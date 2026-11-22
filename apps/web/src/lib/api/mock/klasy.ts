import { ApiError, type ApiClient } from "../client";
import type { ClassSetVersion, ClassTest } from "../schemas";
import { classes } from "./data";

export type ClassMockScenario =
  | "ready"
  | "invalid"
  | "activation-error"
  | "no-configuration";
type ClassMethods = Pick<
  ApiClient,
  | "getClassDetail"
  | "getClassYaml"
  | "testClassDraft"
  | "activateClassSet"
  | "listClassVersions"
>;

export function createClassMock(
  wait: <T>(value: T) => Promise<T>,
  scenario: ClassMockScenario = configuredScenario(),
): ClassMethods {
  let activeVersion = "v1";
  let revision = 2;
  let tested: ClassTest | null = null;
  let activating = false;
  let activationFailed = false;
  let testedYaml: string | null = null;
  let activatedYaml: string | null = null;
  const definitions = classes.filter((c) => c.id !== "obcy");
  function version(version: string): ClassSetVersion {
    return {
      version,
      active: activeVersion === version,
      changes:
        version === "v2"
          ? [
              "przelew: dodano pole oznaczenie_sprawy (demonstracja)",
              "odwolanie, pelnomocnictwo: bez zmian",
            ]
          : [],
      classes: definitions.map((c) => ({
        id: c.id,
        version: c.id === "przelew" ? version : "v1",
        fields:
          c.fields.length + (c.id === "przelew" && version === "v2" ? 1 : 0),
      })),
    };
  }
  function activeYaml(id: string) {
    const cls = definitions.find((c) => c.id === id);
    if (!cls) throw new ApiError("NOT_FOUND", "Nie znaleziono klasy.");
    return [
      `id: ${cls.id}`,
      `nazwa: ${cls.name}`,
      "wersja: 1",
      "sygnaly_rozpoznania:",
      `  - fraza: ${cls.name}`,
      "pola:",
      ...cls.fields.flatMap((f) => [
        `  - sciezka: ${f.key}`,
        `    etykieta: ${f.label}`,
        `    typ: ${f.type}`,
        `    wymagane: ${f.required}`,
        `    nullable: ${f.nullable}`,
      ]),
    ].join("\n");
  }
  function draftYaml() {
    const lines = activeYaml("przelew")
      .replace("wersja: 1", "wersja: 2")
      .split("\n");
    if (scenario === "invalid")
      lines.splice(13, 0, "    normalizator: nieistniejacy");
    return [
      ...lines,
      "  - sciezka: oznaczenie_sprawy",
      "    etykieta: Oznaczenie sprawy",
      "    typ: tekst",
      "    wymagane: false",
      "    nullable: true",
    ].join("\n");
  }
  return {
    getClassDetail: (id) => {
      const cls = definitions.find((c) => c.id === id);
      if (!cls || scenario === "no-configuration") return wait(null);
      if (id !== "przelew" || activeVersion !== "v2") return wait(cls);
      return wait({
        ...cls,
        version: "v2",
        fields: [
          ...cls.fields,
          {
            key: "oznaczenie_sprawy",
            label: "Oznaczenie sprawy",
            group: "Demonstracja",
            type: "tekst",
            description: "Pole demonstracyjne poza kontraktem konkursowym.",
            required: false,
            nullable: true,
          },
        ],
      });
    },
    getClassYaml: (id) =>
      wait({
        active:
          scenario === "no-configuration"
            ? ""
            : id === "przelew" && activatedYaml
              ? activatedYaml
              : definitions.some((cls) => cls.id === id)
                ? activeYaml(id)
                : "",
        draft:
          id === "przelew" &&
          activeVersion === "v1" &&
          scenario !== "no-configuration"
            ? draftYaml()
            : null,
        revision,
      }),
    async testClassDraft(id, yaml) {
      if (id !== "przelew" || scenario === "no-configuration")
        throw new ApiError("NO_DRAFT", "Brak wersji roboczej.");
      const code = yaml ?? draftYaml();
      testedYaml = code;
      const invalidLine = code
        .split("\n")
        .findIndex(
          (line) =>
            line.includes("normalizator:") &&
            !line.includes("normalizator: null"),
        );
      const issues =
        invalidLine >= 0
          ? [`Linia ${invalidLine + 1}: brak normalizatora`]
          : [];
      if (
        !code.includes("id: przelew") ||
        !code.includes("sciezka: oznaczenie_sprawy")
      )
        issues.push("Niepoprawna demonstracyjna konfiguracja przelewu v2.");
      tested = {
        valid: !issues.length,
        revision: ++revision,
        issues,
        fileName: "przelew-demo.pdf",
        summary:
          "Scenariusz syntetyczny: kwota 200.00; oznaczenie_sprawy DEMO-42. Test mocka, bez ekstrakcji PDF.",
      };
      return wait(tested);
    },
    async activateClassSet(next) {
      if (activating) throw new ApiError("BUSY", "Aktywowanie już trwa.");
      if (next !== "v2" || !tested?.valid || scenario === "no-configuration")
        throw new ApiError(
          "INVALID_CONFIGURATION",
          "Aktywacja zablokowana: wymagany poprawny test wersji roboczej.",
        );
      activating = true;
      try {
        await wait(null);
        if (scenario === "activation-error" && !activationFailed) {
          activationFailed = true;
          throw new ApiError(
            "ACTIVATION_FAILED",
            "Nie aktywowano. Nadal aktywny v1. Ponów",
          );
        }
        activeVersion = "v2";
        activatedYaml = testedYaml;
        return structuredClone(version("v2"));
      } finally {
        activating = false;
      }
    },
    listClassVersions: () =>
      wait(
        scenario === "no-configuration" ? [] : [version("v2"), version("v1")],
      ),
  };
}

function configuredScenario(): ClassMockScenario {
  switch (process.env.NEXT_PUBLIC_MOCK_CLASS_SCENARIO) {
    case "invalid":
      return "invalid";
    case "activation-error":
      return "activation-error";
    case "no-configuration":
      return "no-configuration";
    default:
      return "ready";
  }
}
