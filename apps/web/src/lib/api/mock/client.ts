import { ApiError, type ApiClient } from "../client";
import { documentSchema, type CheckStep, type DocumentQuery, type DocumentRecord, type ExportDecision, type KeyStatus } from "../schemas";
import { classes, seedDocuments } from "./data";

const statusOrder = ["error", "ambiguous", "multi", "partial", "running", "foreign", "full"];

export function evaluateExport(doc: DocumentRecord, classesList = classes): ExportDecision {
  const baseName = doc.fileName.replace(/\.pdf$/i, "");
  const blockers: ExportDecision["blockers"] = [];
  if (doc.status === "foreign") return { allowed: true, fileName: `${baseName}.json`, blockers };
  if (doc.status === "running") blockers.push({ code: "RUNNING", message: "Analiza trwa. Poczekaj na wynik." });
  if (doc.status === "error") blockers.push({ code: doc.errorCode ?? "TECHNICAL_ERROR", message: "Błąd techniczny. Brak wyniku ekstrakcji; użyj „Ponów”." });
  if (doc.status === "ambiguous") blockers.push({ code: "AMBIGUOUS", message: "Niejednoznaczna klasa. Wybierz klasę dokumentu." });
  if (doc.status === "multi") blockers.push({ code: "MULTI", message: "Wiele dokumentów w jednym PDF. Rozdziel plik." });
  if (doc.status === "partial" || doc.status === "full") {
    const cls = classesList.find((c) => c.id === doc.classId);
    for (const def of cls?.fields ?? []) {
      const field = doc.fields.find((x) => x.key === def.key);
      if (def.required && !def.nullable && (field?.value ?? null) === null) {
        blockers.push({ code: "NULL_NOT_ALLOWED", message: `Pole „${def.label}” jest puste, a null jest niedozwolony.` });
      }
    }
  }
  return { allowed: blockers.length === 0, fileName: blockers.length === 0 ? `${baseName}.json` : null, blockers };
}

export function buildExportJson(doc: DocumentRecord): string {
  if (doc.status === "foreign") return "{}";
  return JSON.stringify(Object.fromEntries(doc.fields.map((x) => [x.key, x.value])), null, 2);
}

export type MockOptions = { latencyMs?: number; failKey?: boolean };

export function createMockClient(options: MockOptions = {}): ApiClient {
  const latency = options.latencyMs ?? 120;
  let docs = seedDocuments();
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
    ...createMockInfoMethods(wait),
    ...createMockEventMethods(wait),
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
          uploadedAt: new Date().toISOString(), batchId, progress: 0, fields: [], evidence: [], reasons: [], errorCode: null, candidates: [], pageText: [],
        });
      });
      docs = [...added, ...docs];
      // Symulacja postępu: po chwili dokument kończy się jako „Pełny”.
      for (const d of added) {
        setTimeout(() => {
          const done = seedDocuments()[0]!;
          replace({ ...done, id: d.id, fileName: d.fileName, uploadedAt: d.uploadedAt, batchId: d.batchId, sizeKb: d.sizeKb });
        }, latency * 12);
      }
      return wait(added);
    },
    async retryDocument(id) {
      const d = find(id);
      const done = seedDocuments()[0]!;
      return wait(replace({ ...done, id: d.id, fileName: d.fileName, uploadedAt: d.uploadedAt, batchId: d.batchId }));
    },
    async chooseClass(id, classId) {
      const d = find(id);
      const cls = classes.find((c) => c.id === classId);
      if (!cls) throw new ApiError("NO_CLASS", "Nieznana klasa.");
      return wait(replace({ ...d, status: "partial", classId, className: cls.name, candidates: [], fields: cls.fields.map((x) => ({ key: x.key, label: x.label, value: null, evidenceIds: [], state: "missing" as const })) }));
    },
    async updateField(id, fieldKey, value) {
      const d = find(id);
      const fields = d.fields.map((x) => (x.key === fieldKey ? { ...x, value, state: value === null ? ("missing" as const) : ("corrected" as const) } : x));
      const complete = evaluateExport({ ...d, fields }).allowed;
      return wait(replace({ ...d, fields, status: complete && d.status === "partial" ? "full" : d.status }));
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
      versions: { application: "0.1.0", engine: null, classes: "demo-v1", contract: null },
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
