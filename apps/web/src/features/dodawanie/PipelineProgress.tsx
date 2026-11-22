"use client";
import { usePipeline } from "@/lib/api/hooks";
import { ErrorState, LoadingState, Stepper } from "@/components/molecules";
import type { PipelineStage } from "@/lib/api/processing";
function counts(stage: PipelineStage) {
  if (!stage.counts || stage.state !== "zakończony") return undefined;
  const c = stage.counts;
  return [
    c.pages !== undefined && `Strony: ${c.pages}`,
    c.ocrPages !== undefined && `OCR: ${c.ocrPages}`,
    c.className,
    c.filled !== undefined && `Wypełnione: ${c.filled}`,
    c.empty !== undefined && `Puste: ${c.empty}`,
    c.evidence !== undefined && `Dowody: ${c.evidence}`,
  ]
    .filter(Boolean)
    .join(" · ");
}
export function PipelineProgress({
  documentId,
  fileName,
}: {
  documentId: string;
  fileName: string;
}) {
  const pipeline = usePipeline(documentId);
  return (
    <details className="my-3 rounded-md border border-border p-3">
      <summary className="min-h-11 cursor-pointer break-all text-sm">
        Etapy potoku: {fileName}
      </summary>
      {pipeline.isPending ? (
        <LoadingState label="Ładowanie potoku" />
      ) : pipeline.isError ? (
        <ErrorState onRetry={() => void pipeline.refetch()} />
      ) : (
        <Stepper
          label={`Potok ${fileName}`}
          steps={pipeline.data.stages.map((stage) => ({
            id: stage.id,
            label: `${stage.id === "export" ? "Eksport" : stage.id} · ${stage.name} · ${stage.state}`,
            status:
              stage.state === "błąd"
                ? "error"
                : stage.state === "w toku"
                  ? "running"
                  : stage.state === "zakończony" || stage.state === "pominięty"
                    ? "ok"
                    : "pending",
            description: [
              counts(stage),
              stage.errorCode,
              stage.durationMs !== null && `${stage.durationMs} ms`,
            ]
              .filter(Boolean)
              .join(" · "),
          }))}
        />
      )}
    </details>
  );
}
