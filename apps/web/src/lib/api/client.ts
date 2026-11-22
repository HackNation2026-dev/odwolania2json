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

export interface ApiClient {
  getClassDetail(id: string): Promise<import("./schemas").ClassDetail | null>;
  getClassYaml(id: string): Promise<import("./schemas").ClassYaml>;
  testClassDraft(id: string, yaml?: string): Promise<import("./schemas").ClassTest>;
  activateClassSet(version: string): Promise<import("./schemas").ClassSetVersion>;
  listClassVersions(): Promise<import("./schemas").ClassSetVersion[]>;
}

export interface ApiClient {
  getRetentionSettings(): Promise<import("./schemas").RetentionSettings>;
  saveRetention(days: number): Promise<import("./schemas").RetentionSettings>;
  listAuditEvents(query?: import("./schemas").AuditQuery): Promise<import("./schemas").AuditEvent[]>;
  exportAuditCsv(query?: import("./schemas").AuditQuery): Promise<{ fileName: string; csv: string }>;
  getReadiness(): Promise<import("./schemas").SystemInfo>;
}


export interface ApiClient {
  listBatches(): Promise<import("./schemas").DocumentBatch[]>;
  getBatchExportPlan(batchId: string): Promise<import("./schemas").BatchExportPlan>;
  checkPathCollision(files: import("./schemas").UploadFile[]): Promise<import("./schemas").PathCollision[]>;
  addResolvedDocuments(input: { files: import("./schemas").UploadFile[]; choice: import("./schemas").CollisionChoice }): Promise<DocumentRecord[]>;
}
