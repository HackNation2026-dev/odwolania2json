import schemas from "./contract.generated.json";
import type { DocumentClass, DocumentRecord, Field } from "./schemas";

type Schema = { $ref?: string; type?: string | string[]; description?: string; properties?: Record<string, Schema>; required?: string[]; items?: Schema; anyOf?: Schema[]; enum?: unknown[]; pattern?: string; minimum?: number; maximum?: number };
const models: Record<string, Schema> = schemas;
export const appealReasons = schemas.OdwolanieKIO.properties.czynnosc_opis.enum.filter((value): value is string => value !== null);
export const classModels = { odwolanie: "Odwolanie", pelnomocnictwo: "Pelnomocnictwo", przelew: "Przelew", obcy: "PustyWynik" } as const;
export const groupLabels: Record<string, string> = { ZamowieniePubliczne: "Zamówienie publiczne", OdwolanieKIO: "Odwołanie", Odwolujacy: "Odwołujący", PelnomocnikOdwolania: "Pełnomocnik odwołującego", Zamawiajacy: "Zamawiający", MocodawcaDane: "Mocodawca", Podpisujacy: "Podpisujący", PelnomocnikPelnomocnictwa: "Pełnomocnicy", PrzelewBankowy: "Przelew" };
const labels: Record<string, string> = { data: "Data odwołania", czynnosc_dzien: "Data zaskarżonej czynności", czynnosc_powod_id: "Zaskarżona czynność (kod)", czynnosc_opis: "Zaskarżona czynność (opis)", miejscowosc: "Miejscowość", krs: "KRS", nazwa: "Nazwa", nip: "NIP", regon: "REGON", "przez-pelnomocnika": "Działa przez pełnomocnika", imie_nazwisko: "Imię i nazwisko", mail: "E-mail", prowadzacy_postepowanie: "Prowadzi postępowanie", numer_bzp: "Numer BZP", numer_ted: "Numer TED", numer_postepowania: "Numer postępowania", tytul: "Tytuł zamówienia", typ: "Rodzaj mocodawcy", pesel: "PESEL", data_operacji: "Data operacji", kwota: "Kwota", na_rachunek: "Na rachunek", z_rachunku: "Z rachunku", numer_transakcji: "Numer transakcji", pelnomocnik: "Pełnomocnik" };
function resolve(s: Schema): Schema { return s.$ref ? models[s.$ref.split("/").at(-1)!]! : s; }
function nullable(s: Schema): boolean { return s.type === "null" || (Array.isArray(s.type) && s.type.includes("null")) || !!s.anyOf?.some(nullable); }
function concrete(s: Schema): Schema { return resolve(s.anyOf?.find(x => x.type !== "null") ?? s); }
function definition(s: Schema, key: string, group: string, required: boolean): DocumentClass["fields"][number] {
  const leaf = key.split(".").at(-1)!;
  const type = s.type ?? (s.anyOf ? "object" : "string");
  return { key, label: group === "PrzelewBankowy" && leaf === "tytul" ? "Tytuł przelewu" : labels[leaf] ?? leaf, group, required, nullable: nullable(s), type: Array.isArray(type) ? type.filter(t => t !== "null").join(" | ") : type, description: s.description ?? concrete(s).description ?? "" };
}
function definitions(model: string, prefix = "", containersOnly = false): DocumentClass["fields"] {
  return Object.entries(models[model]!.properties ?? {}).flatMap(([key, s]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    const c = concrete(s);
    const container = { ...definition(s, path, model, models[model]!.required?.includes(key) ?? false), type: c.type === "array" ? "array" : "object" };
    if (s.$ref || s.anyOf) return [...(containersOnly ? [container] : []), ...definitions((s.$ref ?? s.anyOf?.find(x => x.$ref)?.$ref)!.split("/").at(-1)!, path, containersOnly)];
    if (c.type === "array") return [...(containersOnly ? [container] : []), ...definitions(c.items!.$ref!.split("/").at(-1)!, `${path}.0`, containersOnly)];
    return containersOnly ? [] : [definition(s, path, model, models[model]!.required?.includes(key) ?? false)];
  });
}
export const contractClasses: DocumentClass[] = Object.entries(classModels).map(([id, model]) => ({ id: id as DocumentClass["id"], model, version: "v1", name: ({ odwolanie: "Odwołanie do KIO", pelnomocnictwo: "Pełnomocnictwo", przelew: "Potwierdzenie przelewu", obcy: "Dokument spoza zakresu" })[id]!, description: models[model]!.description!, fields: definitions(model), containers: definitions(model, "", true) }));

/** Ścieżki używają rzeczywistych aliasów kontraktu i jawnych indeksów list. */
export function fieldsFromResult(classId: DocumentClass["id"], result: unknown): Field[] {
  const walk = (s: Schema, value: unknown, path: string, group: string, required: boolean): Field[] => {
    const c = concrete(s);
    const model = (s.$ref ?? s.anyOf?.find(x => x.$ref)?.$ref)?.split("/").at(-1) ?? group;
    if (value !== null && c.properties) return Object.entries(c.properties).flatMap(([k, child]) => walk(child, (value as Record<string, unknown>)[k], path ? `${path}.${k}` : k, model, c.required?.includes(k) ?? false));
    if (Array.isArray(value) && value.length) return value.flatMap((v, i) => walk(c.items!, v, `${path}.${i}`, model, true));
    return [{ ...definition(s, path, model, required), value: value as Field["value"], state: value === null ? "brak" : "ok", evidenceIds: [], gap: null }];
  };
  return walk({ $ref: `#/components/schemas/${classModels[classId]}` }, result, "", classModels[classId], true);
}

type Json = null | string | number | boolean | Json[] | { [key: string]: Json };
/** Czysta budowa wyniku; do JSON nie trafiają metadane ani raporty. */
export function buildResult(doc: Pick<DocumentRecord, "status" | "fields" | "classId">): Record<string, Json> {
  if (doc.status === "foreign" && doc.classId === "obcy") return {};
  if (!["full", "partial"].includes(doc.status)) throw new Error("Brak wyniku ekstrakcji.");
  const root: Record<string, Json> = {};
  for (const field of doc.fields) {
    const parts = field.key.split(".");
    let node: Record<string, Json> | Json[] = root;
    parts.forEach((part, i) => {
      if (["__proto__", "prototype", "constructor"].includes(part)) throw new Error("Niedozwolona ścieżka pola.");
      const index = Array.isArray(node) ? Number(part) : part;
      const target = node as Record<string, Json>;
      if (i === parts.length - 1) target[index] = structuredClone(field.value);
      else {
        target[index] ??= /^\d+$/.test(parts[i + 1]!) ? [] : {};
        node = target[index] as Record<string, Json> | Json[];
      }
    });
  }
  return root;
}

/** Pełna kontrola kluczy, kontenerów, typów i ograniczeń z migawki OpenAPI. */
export function validateResult(classId: DocumentClass["id"], result: unknown): string[] {
  const issues: string[] = [];
  const walk = (schema: Schema, value: unknown, path: string) => {
    if (value === null && nullable(schema)) return;
    const s = concrete(schema);
    if (s.properties || s.type === "object") {
      if (!value || typeof value !== "object" || Array.isArray(value)) { issues.push(`${path}: wymagany obiekt, null niedozwolony`); return; }
      const obj = value as Record<string, unknown>;
      for (const key of s.required ?? []) if (!(key in obj)) issues.push(`${path}.${key}: brak wymaganego klucza`);
      for (const [k, v] of Object.entries(obj)) { if (!s.properties?.[k]) issues.push(`${path}.${k}: nieznany klucz`); else walk(s.properties[k]!, v, `${path}.${k}`); }
    } else if (s.type === "array") {
      if (!Array.isArray(value)) issues.push(`${path}: wymagana lista, null niedozwolony`);
      else for (const [i, v] of value.entries()) walk(s.items!, v, `${path}.${i}`);
    } else {
      const types = Array.isArray(s.type) ? s.type : [s.type];
      if (!types.some(t => t === "integer" ? typeof value === "number" && Number.isInteger(value) : t === "null" ? value === null : typeof value === t)) issues.push(`${path}: nieprawidłowy typ`);
      if (s.enum && !s.enum.includes(value)) issues.push(`${path}: wartość spoza słownika`);
      if (typeof value === "number" && (!Number.isFinite(value) || (s.minimum !== undefined && value < s.minimum) || (s.maximum !== undefined && value > s.maximum))) issues.push(`${path}: wartość poza zakresem`);
      if (typeof value === "string" && s.pattern && !new RegExp(s.pattern).test(value)) issues.push(`${path}: nieprawidłowy format`);
    }
  };
  walk(models[classModels[classId]]!, result, classModels[classId]);
  if (classId === "odwolanie" && result && typeof result === "object") {
    const header = (result as Record<string, unknown>).OdwolanieKIO as Record<string, unknown> | null;
    if (header && typeof header.czynnosc_powod_id === "number" && header.czynnosc_opis !== null && header.czynnosc_opis !== appealReasons[header.czynnosc_powod_id - 1]) issues.push("OdwolanieKIO.czynnosc_opis: opis niezgodny z kodem pierwszego zarzutu");
  }
  return issues;
}
