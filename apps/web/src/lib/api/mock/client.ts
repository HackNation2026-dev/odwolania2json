import { createMockSysMethods } from "./sys";
import { ApiError, type ApiClient } from "../client";
import { documentSchema, type CheckStep, type DocumentQuery, type DocumentRecord, type ExportDecision, type KeyStatus } from "../schemas";
import { classes, seedDocuments, pipelineFor, diagnosisFor } from "./data";
import { buildResult, validateResult, appealReasons } from "../contract";
import type { ResultVersion, Versions } from "../processing";
import { createClassMock } from "./klasy";

const statusOrder = ["error", "ambiguous", "multi", "partial", "running", "foreign", "full"];

export function evaluateExport(doc: DocumentRecord, classesList = classes): ExportDecision {
  const baseName = doc.fileName.replace(/\.pdf$/i, "");
  const blockers: ExportDecision["blockers"] = [];
  if (doc.status === "foreign" && doc.classId === "obcy" && doc.state.outcome === "foreign") return { allowed: true, fileName: `${baseName}.json`, blockers };
  if (doc.status === "running") blockers.push({ code: "RUNNING", message: "Analiza trwa. Poczekaj na wynik." });
  if (doc.status === "error") blockers.push({ code: doc.errorCode ?? "TECHNICAL_ERROR", message: "Błąd techniczny. Brak wyniku ekstrakcji; użyj „Ponów”." });
  if (doc.status === "ambiguous") blockers.push({ code: "AMBIGUOUS", message: "Niejednoznaczna klasa. Wybierz klasę dokumentu." });
  if (doc.status === "multi") blockers.push({ code: "MULTI", message: "Wiele dokumentów w jednym PDF. Rozdziel plik." });
  if (doc.status === "partial" || doc.status === "full") {
    const cls = classesList.find((c) => c.id === doc.classId);
    if (!cls || cls.id === "obcy") blockers.push({ code: "invalid_configuration", message: "Brak właściwej klasy kontraktu." });
    for (const def of cls?.fields ?? []) {
      const field = doc.fields.find((x) => x.key === def.key);
      if (def.required && !def.nullable && (field?.value ?? null) === null) {
        blockers.push({ code: "NULL_NOT_ALLOWED", message: `Pole „${def.label}” jest puste, a null jest niedozwolony.` });
      }
    }
    if (cls) for (const issue of validateResult(cls.id, buildResult(doc))) blockers.push({ code: "result_validation_failed", message: issue });
  }
  if (doc.status === "foreign") blockers.push({ code: "foreign_document", message: "Brak potwierdzenia dokumentu obcego." });
  return { allowed: blockers.length === 0, fileName: blockers.length === 0 ? `${baseName}.json` : null, blockers };
}

export function buildExportJson(doc: DocumentRecord): string {
  const decision = evaluateExport(doc);
  if (!decision.allowed) throw new ApiError("EXPORT_BLOCKED", decision.blockers[0]?.message ?? "Eksport zablokowany.");
  return JSON.stringify(buildResult(doc), null, 2);
}

export type MockOptions = { latencyMs?: number; failKey?: boolean };

export function createMockClient(options: MockOptions = {}): ApiClient {
  const latency = options.latencyMs ?? 120;
  let docs = seedDocuments();
  const histories = new Map<string, Versions>();
  const snapshot = (d: DocumentRecord, version: number, kind: ResultVersion["kind"], restoredFrom: number | null = null): ResultVersion => ({ version, documentVersion: 1, kind, restoredFrom, createdAt: new Date().toISOString(), fields: structuredClone(d.fields), status: d.status, classId: d.classId, json: evaluateExport(d).allowed ? buildExportJson(d) : null });
  for (const d of docs) {
    const results = ["full", "partial", "foreign"].includes(d.status) ? [snapshot(d, 1, "silnik")] : [];
    if (d.id === "doc-1") {
      results[0]!.fields.find(f => f.key === "ZamowieniePubliczne.numer_ted")!.value = "999136-2026";
      results[0]!.json = JSON.stringify(buildResult({ ...d, fields: results[0]!.fields }), null, 2);
      results.push(snapshot(d, 2, "korekta"), snapshot(d, 3, "zatwierdzony"));
    }
    histories.set(d.id, { documents: [{ version: 1, fileName: d.fileName, sha256: "a".repeat(64), createdAt: d.uploadedAt }], results });
  }
  let key: KeyStatus = { configured: false, persisted: false, lastCheck: "never" };
  let seq = 100;
  const wait = <T>(v: T) => new Promise<T>((r) => setTimeout(() => r(structuredClone(v)), latency));
  const find = (id: string) => {
    const d = docs.find((x) => x.id === id);
    if (!d) throw new ApiError("NOT_FOUND", `Nie znaleziono dokumentu ${id}`);
    return d;
  };
  const replace = (d: DocumentRecord) => {
    docs = docs.map((x) => (x.id === d.id ? d : x));
    return d;
  };

  return {
    ...createClassMock(wait),
    getPipeline: async id => wait(pipelineFor(find(id))),
    getDiagnosis: async id => wait(diagnosisFor(find(id))),
    getVersions: async id => { const d = find(id); return wait(histories.get(id) ?? { documents: [{ version: 1, fileName: d.fileName, sha256: "a".repeat(64), createdAt: d.uploadedAt }], results: [snapshot(d, 1, "silnik")] }); },
    async restoreVersion(id, version) {
      const d = find(id);
      const history = histories.get(id);
      const old = history?.results.find(v => v.version === version);
      if (!history || !old || old.json === null) throw new ApiError("NOT_FOUND", "Nie znaleziono zapisanej wersji wyniku.");
      const restored = { ...d, fields: structuredClone(old.fields), reasons: old.status === "partial" ? [...new Set(old.fields.flatMap(f => f.gap ? [f.gap.reason] : []))] : [], status: old.status, classId: old.classId, className: classes.find(c => c.id === old.classId)?.name ?? null, resultVersion: history.results.at(-1)!.version + 1 };
      history.results.push(snapshot(restored, restored.resultVersion, "przywrócenie", version));
      return wait(replace(restored));
    },
    ...createMockInfoMethods(wait),
    ...createMockEventMethods(wait),
    ...createListaMethods({ wait, read: () => docs, write: next => { docs = next; }, evaluate: evaluateExport, histories, snapshot }),
    ...createMockSysMethods(wait, () => createMockInfoMethods(wait).getSystemInfo()),
    getKeyStatus: () => wait(key),
    async saveKey({ value, persist }) {
      if (!value.trim()) throw new ApiError("KEY_EMPTY", "Podaj klucz API.");
      key = { configured: true, persisted: persist, lastCheck: "never" };
      return wait(key);
    },
    async runSelfCheck(onStep) {
      const labels: [CheckStep["id"], string][] = [["connection", "Połączenie"], ["authorization", "Autoryzacja"], ["model", "Model"], ["region", "Region i licencja"], ["ocr", "Gotowość OCR"]];
      let steps: CheckStep[] = labels.map(([id, label]) => ({ id, label, state: "pending", detail: null }));
      for (let i = 0; i < steps.length; i++) {
        steps = steps.map((s, j) => (j === i ? { ...s, state: "running" } : s));
        onStep(structuredClone(steps));
        await new Promise((r) => setTimeout(r, latency));
        const fail = options.failKey && i === 1;
        steps = steps.map((s, j) => (j === i ? { ...s, state: fail ? "error" : "ok", detail: fail ? "401: klucz odrzucony. Bez ponowień; popraw konfigurację." : null } : s));
        onStep(structuredClone(steps));
        if (fail) break;
      }
      key = { ...key, lastCheck: steps.every((s) => s.state === "ok") ? "ok" : "error" };
      return structuredClone(steps);
    },
    async getDashboard() {
      const byStatus: Record<string, number> = {};
      for (const d of docs) byStatus[d.status] = (byStatus[d.status] ?? 0) + 1;
      return wait({ total: docs.length, byStatus, recent: [...docs].sort((a, b) => b.uploadedAt.localeCompare(a.uploadedAt)).slice(0, 5) } as never);
    },
    async listDocuments(q: DocumentQuery = {}) {
      let out = docs.filter((d) => (!q.search || d.fileName.toLowerCase().includes(q.search.toLowerCase())) && (!q.statuses?.length || q.statuses.includes(d.status)) && (!q.classId || d.classId === q.classId));
      const sort = q.sort ?? "newest";
      out = [...out].sort((a, b) => (sort === "name" ? a.fileName.localeCompare(b.fileName, "pl") : sort === "oldest" ? a.uploadedAt.localeCompare(b.uploadedAt) : sort === "status" ? statusOrder.indexOf(a.status) - statusOrder.indexOf(b.status) : b.uploadedAt.localeCompare(a.uploadedAt)));
      return wait(out);
    },
    getDocument: async (id) => wait(find(id)),
    async addDocuments(files) {
      const batchId = `batch-${++seq}`;
      const added = files.map((file) => {
        const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
        if (!isPdf) throw new ApiError("NOT_PDF", `Plik „${file.name}” nie jest PDF i został pominięty.`);
        const id = `doc-${++seq}`;
        return documentSchema.parse({
          id, fileName: file.name, pages: 2, sizeKb: file.sizeKb, status: "running", classId: null, className: null,
          uploadedAt: new Date().toISOString(), batchId, progress: 0, fields: [], evidence: [], reasons: [], errorCode: null, candidates: [], pageText: [], processedPages: [], unprocessedPages: [1, 2], codes: [], state: { progress: "queued", outcome: null, stage: null }, technicalErrors: [], resultVersion: 1, contractRevision: "main-7590db8 / openapi 0.5.0",
        });
      });
      docs = [...added, ...docs];
      // Symulacja postępu: po chwili dokument kończy się jako „Pełny”.
      for (const d of added) {
        setTimeout(() => {
          const done = seedDocuments()[0]!;
          const completed = { ...done, id: d.id, fileName: d.fileName, uploadedAt: d.uploadedAt, batchId: d.batchId, sizeKb: d.sizeKb, resultVersion: 1 };
          replace(completed);
          histories.set(d.id, { documents: [{ version: 1, fileName: d.fileName, sha256: "a".repeat(64), createdAt: d.uploadedAt }], results: [snapshot(completed, 1, "silnik")] });
        }, latency * 12);
      }
      return wait(added);
    },
    async retryDocument(id) {
      const d = find(id);
      const done = seedDocuments()[0]!;
      const history = histories.get(id)!;
      const completed = { ...done, id: d.id, fileName: d.fileName, uploadedAt: d.uploadedAt, batchId: d.batchId, resultVersion: (history.results.at(-1)?.version ?? 0) + 1 };
      history.results.push(snapshot(completed, completed.resultVersion, "silnik"));
      return wait(replace(completed));
    },
    async chooseClass(id, classId) {
      const d = find(id);
      const cls = classes.find((c) => c.id === classId);
      if (!cls) throw new ApiError("NO_CLASS", "Nieznana klasa.");
      const template = seedDocuments().find(x => x.classId === cls.id && x.status === "full");
      if (!template) throw new ApiError("NO_CLASS", "Wybierz klasę kontraktu.");
      const history = histories.get(id)!;
      const completed = { ...template, id: d.id, fileName: d.fileName, batchId: d.batchId, uploadedAt: d.uploadedAt, resultVersion: (history.results.at(-1)?.version ?? 0) + 1 };
      history.results.push(snapshot(completed, completed.resultVersion, "silnik"));
      return wait(replace(completed));
    },
    async updateField(id, fieldKey, value) {
      const d = find(id);
      const old = d.fields.find(f => f.key === fieldKey);
      if (!old) throw new ApiError("NOT_FOUND", "Nie znaleziono pola.");
      const fields = d.fields.map((x) => (x.key === fieldKey ? { ...x, value, gap: null, state: value === null ? ("brak" as const) : ("poprawione" as const) } : x.key === "OdwolanieKIO.czynnosc_opis" && fieldKey === "OdwolanieKIO.czynnosc_powod_id" ? { ...x, value: typeof value === "number" ? appealReasons[value - 1] ?? null : null, state: "poprawione" as const, evidenceIds: [] } : x));
      if (!d.classId || validateResult(d.classId, buildResult({ ...d, fields })).length) throw new ApiError("VALIDATION_ERROR", "Wartość jest niezgodna z kontraktem.");
      const updated = { ...d, fields, reasons: d.status === "partial" ? [...new Set(fields.flatMap(f => f.gap ? [f.gap.reason] : []))] : [], resultVersion: d.resultVersion + 1 };
      histories.get(id)?.results.push(snapshot(updated, updated.resultVersion, "korekta"));
      return wait(replace(updated));
    },
    getExportDecision: async (id) => wait(evaluateExport(find(id))),
    async exportJson(id) {
      const d = find(id);
      const decision = evaluateExport(d);
      if (!decision.allowed || !decision.fileName) throw new ApiError("EXPORT_BLOCKED", decision.blockers[0]?.message ?? "Eksport zablokowany.");
      return wait({ fileName: decision.fileName, json: buildExportJson(d) });
    },
    listClasses: () => wait(classes),
  };
}

/** Syntetyczna konfiguracja demonstracji; nie potwierdza zgodności rzeczywistego dostawcy. */
function createMockInfoMethods(wait: <T>(value: T) => Promise<T>): Pick<ApiClient, "getSystemInfo" | "listUsers"> {
  return {
    getSystemInfo: () => wait({
      demo: true,
      models: [{ id: "demo-llm", name: "MiniMax-M3.1-Flash-Preview", version: null, role: "Klasyfikacja i ekstrakcja", state: "configured", parameters: null, license: "MiniMax Community License — niepotwierdzona", weights: "Publiczne wagi: wymagają weryfikacji", localInstallation: "Instrukcja lokalnej instalacji: niepotwierdzona", provider: "api.minimax.io · protokół zgodny z Anthropic", companyCountry: null, serverCountry: null, region: "Europa — wpis demonstracyjny, niepotwierdzony", confirmation: "Brak źródła i daty potwierdzenia licencji oraz lokalizacji. Wywołania rzeczywistego modelu zablokowane." }],
      ocr: { name: "rapidocr", version: null, mode: "shim", execution: "Lokalnie, CPU urządzenia jury — konfiguracja demonstracyjna", license: null, parameters: null, detail: "OCR tymczasowy (shim). Docelowy własny model OCR nie jest podłączony. Mock nie wykonuje OCR ani nie potwierdza gotowości komponentu." },
      largestModel: null,
      versions: { application: "0.1.0", engine: null, classes: "v1", contract: "main-7590db8 / openapi 0.5.0" },
      limits: { fileMb: 20, batch: null, concurrency: null },
      licenses: null,
    }),
    listUsers: () => wait([
      { id: "demo-anna", name: "Anna Kowalska", email: "anna.kowalska@example.test", role: "Administrator", personalData: true, status: "active", lastLogin: "2026-11-21T21:58:00+01:00" },
      { id: "demo-jan", name: "Jan Nowak", email: "jan.nowak@example.test", role: "Operator", personalData: false, status: "active", lastLogin: "2026-11-21T20:41:00+01:00" },
      { id: "demo-ewa", name: "Ewa Wiśniewska", email: "ewa.wisniewska@example.test", role: "Weryfikator", personalData: true, status: "active", lastLogin: "2026-11-21T18:12:00+01:00" },
      { id: "demo-piotr", name: "Piotr Zieliński", email: "piotr.zielinski@example.test", role: "Obserwator", personalData: false, status: "invited", lastLogin: null },
      { id: "demo-marta", name: "Marta Lis", email: "marta.lis@example.test", role: "Konfigurator", personalData: false, status: "blocked", lastLogin: "2026-11-14T09:30:00+01:00" },
    ]),
  };
}

function createMockEventMethods(wait: <T>(value: T) => Promise<T>): Pick<ApiClient, "listEvents"> {
  return { listEvents: () => wait([
    { id: "evt-6", occurredAt: "2026-11-21T14:12:00+01:00", type: "export", description: "Eksport JSON", documentName: "nota-testowa.pdf", result: "success", detail: "Zapisano nota-testowa.json po walidacji. Dowody zapisano osobno." },
    { id: "evt-5", occurredAt: "2026-11-21T14:11:00+01:00", type: "correction", description: "Korekta pola", documentName: "nota-testowa.pdf", result: "success", detail: "Pole numer_noty. Było: •••; Jest: •••. Wartości zamaskowane." },
    { id: "evt-4", occurredAt: "2026-11-21T14:10:00+01:00", type: "export", description: "Próba eksportu JSON", documentName: "skan-testowy.pdf", result: "blocked", detail: "Niedozwolony null w wymaganym polu. Wariant A blokuje eksport." },
    { id: "evt-3", occurredAt: "2026-11-21T14:09:00+01:00", type: "error", description: "Błąd OCR", documentName: "skan-testowy.pdf", result: "error", detail: "OCR niedostępny. Nie zapisano pliku wynikowego ani zastępczego {}." },
    { id: "evt-2", occurredAt: "2026-11-21T14:08:00+01:00", type: "analysis", description: "Zakończono analizę", documentName: "nota-testowa.pdf", result: "success", detail: "Wynik zgodny z kontraktem demonstracyjnym." },
    { id: "evt-1", occurredAt: "2026-11-21T14:07:00+01:00", type: "upload", description: "Wgranie PDF", documentName: "nota-testowa.pdf", result: "success", detail: "Przyjęto syntetyczny dokument do analizy." },
  ]) };
}

import { createListaMethods } from "./lista";
