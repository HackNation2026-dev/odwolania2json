import { z } from "zod";

export const documentStatus = z.enum(["full", "partial", "foreign", "error", "running", "ambiguous", "multi"]);
export type DocumentStatus = z.infer<typeof documentStatus>;

export const partialReason = z.enum(["ocr_unavailable", "unreadable_scan", "missing_field", "low_confidence", "page_limit"]);
export type PartialReason = z.infer<typeof partialReason>;

export const evidenceSchema = z.object({
  id: z.string(),
  fieldKey: z.string(),
  page: z.number().int().positive(),
  quote: z.string(),
  /** Prostokąt w ułamkach strony (0..1) do podświetlenia na PDF. */
  box: z.object({ x: z.number(), y: z.number(), w: z.number(), h: z.number() }),
  confidence: z.number().min(0).max(1),
  source: z.enum(["text", "ocr"]),
});
export type Evidence = z.infer<typeof evidenceSchema>;

export const fieldSchema = z.object({
  key: z.string(),
  label: z.string(),
  value: z.union([z.string(), z.number(), z.boolean(), z.null()]),
  evidenceIds: z.array(z.string()),
  state: z.enum(["ok", "missing", "computed", "corrected"]),
});
export type Field = z.infer<typeof fieldSchema>;

export const documentSchema = z.object({
  id: z.string(),
  fileName: z.string(),
  pages: z.number().int().nonnegative(),
  sizeKb: z.number().nonnegative(),
  status: documentStatus,
  classId: z.string().nullable(),
  className: z.string().nullable(),
  uploadedAt: z.string(),
  batchId: z.string(),
  progress: z.number().min(0).max(100).optional(),
  fields: z.array(fieldSchema),
  evidence: z.array(evidenceSchema),
  reasons: z.array(partialReason),
  errorCode: z.string().nullable(),
  /** Nazwy klas kandydujących dla statusu "ambiguous". */
  candidates: z.array(z.string()),
  pageText: z.array(z.string()),
});
export type DocumentRecord = z.infer<typeof documentSchema>;

export const documentClassSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  fields: z.array(z.object({ key: z.string(), label: z.string(), required: z.boolean(), nullable: z.boolean() })),
});
export type DocumentClass = z.infer<typeof documentClassSchema>;

export const checkStepSchema = z.object({
  id: z.enum(["connection", "authorization", "model", "region", "ocr"]),
  label: z.string(),
  state: z.enum(["pending", "running", "ok", "error"]),
  detail: z.string().nullable(),
});
export type CheckStep = z.infer<typeof checkStepSchema>;

export const keyStatusSchema = z.object({
  configured: z.boolean(),
  persisted: z.boolean(),
  lastCheck: z.enum(["never", "ok", "error"]),
});
export type KeyStatus = z.infer<typeof keyStatusSchema>;

export const exportDecisionSchema = z.object({
  allowed: z.boolean(),
  fileName: z.string().nullable(),
  blockers: z.array(z.object({ code: z.string(), message: z.string() })),
});
export type ExportDecision = z.infer<typeof exportDecisionSchema>;

export const dashboardSchema = z.object({
  total: z.number(),
  byStatus: z.record(documentStatus, z.number()),
  recent: z.array(documentSchema),
});
export type Dashboard = z.infer<typeof dashboardSchema>;

export type DocumentQuery = {
  search?: string;
  statuses?: DocumentStatus[];
  classId?: string;
  sort?: "newest" | "oldest" | "name" | "status";
};
