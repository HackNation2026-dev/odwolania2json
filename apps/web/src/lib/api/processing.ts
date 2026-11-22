import type { DocumentRecord, Field } from "./schemas";

export type Signal = { code: string; value: string | number | boolean | null; description: string };
export type DiagnosisPart = {
  text_source: "pdf" | "ocr" | "mixed" | "none" | "unknown";
  coverage: number | null; rotation_degrees: number | null; confidence: number | null;
  method: string; requires_ocr: boolean | null; signals: Signal[]; codes: string[];
};
export type RegionDiagnosis = DiagnosisPart & { id: string; bbox: [number, number, number, number] };
export type PageDiagnosis = DiagnosisPart & { number: number; regions?: RegionDiagnosis[] };
export type Diagnosis = DiagnosisPart & { schema_version: 1; pages: PageDiagnosis[] };
export type PipelineStage = {
  id: "E" | "L" | "T1" | "T2" | "T3" | "T4" | "T5" | "export";
  name: string; state: "oczekuje" | "w toku" | "zakończony" | "pominięty" | "błąd";
  durationMs: number | null; errorCode: string | null;
  counts: { pages?: number; ocrPages?: number; className?: string; routerSignals?: string[]; filled?: number; empty?: number; evidence?: number } | null;
};
export type Pipeline = { documentId: string; stages: PipelineStage[] };
export type ResultVersion = { version: number; documentVersion: number; kind: "silnik" | "korekta" | "zatwierdzony" | "przywrócenie"; createdAt: string; restoredFrom: number | null; fields: Field[]; status: DocumentRecord["status"]; classId: DocumentRecord["classId"]; json: string | null };
export type Versions = { documents: { version: number; fileName: string; sha256: string; createdAt: string }[]; results: ResultVersion[] };

export function compareVersions(a: ResultVersion, b: ResultVersion) {
  const keys = new Set([...a.fields, ...b.fields].map(f => f.key));
  return [...keys].flatMap(key => {
    const before = a.fields.find(f => f.key === key)?.value;
    const after = b.fields.find(f => f.key === key)?.value;
    return JSON.stringify(before) === JSON.stringify(after) ? [] : [{ key, before, after }];
  });
}
