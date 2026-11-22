import type { CheckStep, Dashboard, DocumentClass, DocumentQuery, DocumentRecord, ExportDecision, KeyStatus } from "./schemas";

/**
 * Jedyny kontrakt między UI a danymi. Implementacje: mock (domyślnie) i http (po powstaniu backendu).
 * Komponenty nie wołają fetch; używają hooków z ./hooks.
 */
export interface ApiClient {
  getPipeline(id: string): Promise<import("./processing").Pipeline>;
  getDiagnosis(id: string): Promise<import("./processing").Diagnosis>;
  getVersions(id: string): Promise<import("./processing").Versions>;
  restoreVersion(id: string, version: number): Promise<DocumentRecord>;
  getKeyStatus(): Promise<KeyStatus>;
  saveKey(input: { value: string; persist: boolean }): Promise<KeyStatus>;
  runSelfCheck(onStep: (steps: CheckStep[]) => void): Promise<CheckStep[]>;
  getDashboard(): Promise<Dashboard>;
  listDocuments(query?: DocumentQuery): Promise<DocumentRecord[]>;
  getDocument(id: string): Promise<DocumentRecord>;
  addDocuments(files: { name: string; sizeKb: number; type: string }[]): Promise<DocumentRecord[]>;
  retryDocument(id: string): Promise<DocumentRecord>;
  chooseClass(id: string, classId: string): Promise<DocumentRecord>;
  updateField(id: string, key: string, value: import("./schemas").Field["value"]): Promise<DocumentRecord>;
  getExportDecision(id: string): Promise<ExportDecision>;
  exportJson(id: string): Promise<{ fileName: string; json: string }>;
  listClasses(): Promise<DocumentClass[]>;
}

export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface ApiClient {
  getSystemInfo(): Promise<import("./schemas").SystemInfo>;
  listUsers(): Promise<import("./schemas").UserRecord[]>;
}

export interface ApiClient {
  listEvents(): Promise<import("./schemas").EventRecord[]>;
}
