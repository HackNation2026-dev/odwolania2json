import { ApiError } from "../client";
import type {
  BatchExportPlan,
  DocumentBatch,
  DocumentRecord,
  ExportDecision,
  UploadFile,
} from "../schemas";
import type { ApiClient } from "../client";
import type { ResultVersion, Versions } from "../processing";

type Dependencies = {
  wait: <T>(value: T) => Promise<T>;
  read: () => DocumentRecord[];
  write: (documents: DocumentRecord[]) => void;
  histories: Map<string, Versions>;
  snapshot: (
    document: DocumentRecord,
    version: number,
    kind: ResultVersion["kind"],
  ) => ResultVersion;
  evaluate: (document: DocumentRecord) => ExportDecision;
};

export function createListaMethods({
  wait,
  read,
  write,
  histories,
  snapshot,
  evaluate,
}: Dependencies): Pick<
  ApiClient,
  | "listBatches"
  | "getBatchExportPlan"
  | "checkPathCollision"
  | "addResolvedDocuments"
> {
  let sequence = 0;
  function batches(): DocumentBatch[] {
    const demoIds = ["doc-1", "doc-4", "doc-7", "doc-6", "doc-5", "doc-8"];
    const groups = ["", "sprawa-a/", "", "sprawa-a/", "sprawa-b/", "sprawa-b/"];
    const demo: DocumentBatch = {
      id: "B-01",
      name: "B-01 · Scenariusz syntetyczny",
      entries: demoIds.flatMap((id, index) => {
        const document = read().find((d) => d.id === id);
        if (!document) return [];
        const relative = `${groups[index]}${document.fileName}`;
        return [
          {
            documentId: id,
            inputPath: `input/${relative}`,
            outputPath: `output/${relative.replace(/\.pdf$/i, ".json")}`,
            group: groups[index]?.replace(/\/$/, "") || "Katalog główny",
          },
        ];
      }),
    };
    const other = new Map<string, DocumentBatch>();
    for (const document of read()) {
      if (!other.has(document.batchId))
        other.set(document.batchId, {
          id: document.batchId,
          name: document.batchId,
          entries: [],
        });
      other.get(document.batchId)!.entries.push({
        documentId: document.id,
        inputPath: `input/${document.fileName}`,
        outputPath: `output/${document.fileName.replace(/\.pdf$/i, ".json")}`,
        group: "Katalog główny",
      });
    }
    return [demo, ...other.values()];
  }
  function collisions(files: UploadFile[]) {
    return files.flatMap((file, incomingIndex) => {
      const existing = read().find((d) => d.fileName === file.name);
      return existing ||
        files.slice(0, incomingIndex).some((f) => f.name === file.name)
        ? [
            {
              path: file.name,
              incomingIndex,
              existingDocumentId: existing?.id ?? null,
            },
          ]
        : [];
    });
  }
  return {
    listBatches: () => wait(batches()),
    async getBatchExportPlan(batchId) {
      const batch = batches().find((b) => b.id === batchId);
      if (!batch) throw new ApiError("NOT_FOUND", "Nie znaleziono partii.");
      const plan: BatchExportPlan = { batchId, included: [], omitted: [] };
      for (const entry of batch.entries) {
        const document = read().find((d) => d.id === entry.documentId)!;
        const decision = evaluate(document);
        const item = {
          ...entry,
          status: document.status,
          reasons: decision.blockers.map((b) => `${b.code}: ${b.message}`),
        };
        (decision.allowed ? plan.included : plan.omitted).push(item);
      }
      return wait(plan);
    },
    checkPathCollision: (files) => wait(collisions(files)),
    async addResolvedDocuments({ files, choice }) {
      if (
        !files.length ||
        files.some((f) => !f.name.toLowerCase().endsWith(".pdf"))
      )
        throw new ApiError("NOT_PDF", "Wybierz pliki PDF.");
      if (
        choice === "version" &&
        new Set(files.map((f) => f.name)).size !== files.length
      )
        throw new ApiError(
          "PATH_COLLISION",
          "Dwie nowe wersje tej samej ścieżki wymagają osobnych paczek.",
        );
      const template = read().find((d) => d.status === "full");
      if (!template)
        throw new ApiError("NO_TEMPLATE", "Brak danych demonstracyjnych.");
      const packageId = `paczka-${++sequence}`;
      const added = files.map((file, index) => {
        const previous = read().find((d) => d.fileName === file.name);
        // Poprzedni dokument i wyniki pozostają w historii wersji.
        return {
          ...structuredClone(template),
          id:
            choice === "version" && previous
              ? previous.id
              : `resolved-${++sequence}`,
          fileName: file.name,
          sizeKb: file.sizeKb,
          batchId:
            choice === "version" && previous
              ? previous.batchId
              : files.slice(0, index).some((f) => f.name === file.name)
                ? `${packageId}-${index}`
                : packageId,
          uploadedAt: new Date().toISOString(),
          resultVersion:
            choice === "version" ? (previous?.resultVersion ?? 0) + 1 : 1,
        };
      });
      for (const document of added) {
        const history = histories.get(document.id);
        const documentVersion = (history?.documents.at(-1)?.version ?? 0) + 1;
        const result = {
          ...snapshot(document, document.resultVersion, "silnik"),
          documentVersion,
        };
        const original = {
          version: documentVersion,
          fileName: document.fileName,
          sha256: "a".repeat(64),
          createdAt: document.uploadedAt,
        };
        histories.set(document.id, {
          documents: [...(history?.documents ?? []), original],
          results: [...(history?.results ?? []), result],
        });
      }
      const ids = new Set(added.map((d) => d.id));
      write([...added, ...read().filter((d) => !ids.has(d.id))]);
      return wait(added);
    },
  };
}
