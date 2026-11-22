import { describe, expect, it } from "vitest";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import schemas from "./contract.generated.json";
import { appealReasons, buildResult, contractClasses, fieldsFromResult, validateResult } from "./contract";
import { documentSchema } from "./schemas";
import { seedDocuments, appealResult } from "./mock/data";
import { buildExportJson, evaluateExport } from "./mock/client";

describe("engine contract alignment", () => {
  it("uses the current OpenAPI as source of truth and checks model aliases", () => {
    const root = resolve(process.cwd(), "../..");
    const script = `import ast,json,pathlib,yaml,sys
root=pathlib.Path(sys.argv[1])/"packages/contracts/odwolania2json_contracts"
schemas=yaml.safe_load((root/"openapi.yaml").read_text())["components"]["schemas"]
tree=ast.parse((root/"models.py").read_text())
for cls in (n for n in tree.body if isinstance(n,ast.ClassDef)):
 fields=[]
 for n in cls.body:
  if isinstance(n,ast.AnnAssign):
   aliases=[k.value.value for c in ast.walk(n.annotation) if isinstance(c,ast.Call) for k in c.keywords if k.arg=="alias"]
   fields.append(aliases[0] if aliases else n.target.id)
 assert fields==list(schemas[cls.name].get("properties",{})),cls.name
print(json.dumps(schemas))`;
    expect(JSON.parse(execFileSync("python3", ["-c", script, root], { encoding: "utf8" }))).toEqual(schemas);
    const reasons = JSON.parse(execFileSync("python3", ["-c", "import runpy,json,sys; print(json.dumps(runpy.run_path(sys.argv[1])['APPEAL_REASONS']))", resolve(root, "packages/contracts/odwolania2json_contracts/powody.py")], { encoding: "utf8" }));
    expect(Object.values(reasons)).toEqual(appealReasons);
  });
  it("validates every seed record and every complete JSON using official schemas", () => {
    for (const doc of seedDocuments()) {
      expect(documentSchema.safeParse(doc).success, doc.id).toBe(true);
      if (doc.status === "full") expect(validateResult(doc.classId!, JSON.parse(buildExportJson(doc))), doc.id).toEqual([]);
    }
    expect(contractClasses.map(c => c.id)).toEqual(["odwolanie", "pelnomocnictwo", "przelew", "obcy"]);
  });
  it("preserves nested lists, aliases, nullable objects and identifier strings", () => {
    const doc = seedDocuments()[0]!;
    expect(buildResult(doc)).toEqual(appealResult);
    const result = { ...appealResult, Odwolujacy: [{ ...appealResult.Odwolujacy[0], pelnomocnik: null }] };
    const built = buildResult({ ...doc, fields: fieldsFromResult("odwolanie", result) });
    expect(built).toEqual(result);
    expect(validateResult("odwolanie", built)).toEqual([]);
    expect(JSON.stringify(built)).not.toContain("evidence");
  });
  it("preserves empty arrays and multiple parties without flattening them", () => {
    const doc = seedDocuments()[0]!;
    for (const result of [{ ...appealResult, Odwolujacy: [], Zamawiajacy: [] }, { ...appealResult, Odwolujacy: [...appealResult.Odwolujacy, ...appealResult.Odwolujacy] }]) {
      const built = buildResult({ ...doc, fields: fieldsFromResult("odwolanie", result) });
      expect(built).toEqual(result);
      expect(validateResult("odwolanie", built)).toEqual([]);
    }
  });
  it("exports nullable gaps and blocks null in required containers, invalid types and unknown keys", () => {
    const doc = seedDocuments()[2]!;
    expect(evaluateExport(doc).allowed).toBe(true);
    expect(buildResult(doc)).toHaveProperty("OdwolanieKIO.data", null);
    const invalid = { ...doc, fields: [{ ...doc.fields[0]!, key: "OdwolanieKIO", value: null }] };
    expect(evaluateExport(invalid).allowed).toBe(false);
    expect(() => buildExportJson(invalid)).toThrow();
    expect(validateResult("przelew", { przelew_bankowy: { kwota: "200" }, unexpected: 1 }).length).toBeGreaterThan(0);
  });
  it("exports exactly an empty object only for a confirmed foreign document", () => {
    expect(buildExportJson(seedDocuments()[6]!)).toBe("{}");
    for (const d of seedDocuments().filter(d => ["error", "running", "ambiguous", "multi"].includes(d.status))) expect(() => buildExportJson(d)).toThrow();
  });
});
