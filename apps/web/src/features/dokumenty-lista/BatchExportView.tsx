"use client";
import Link from "next/link";
import { Button, Card, StatusBadge } from "@/components/atoms";
import {
  Banner,
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/molecules";
import { AppPage } from "@/components/templates";
import { PageHeader } from "@/components/organisms/PageHeader";
import { useBatchExportPlan, useExportBatchResults } from "@/lib/api/hooks";
import type { BatchExportEntry } from "@/lib/api/schemas";

function download(fileName: string, contents: string) {
  const url = URL.createObjectURL(
    new Blob([contents], { type: "application/json" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function ExportEntries({
  title,
  entries,
}: {
  title: string;
  entries: BatchExportEntry[];
}) {
  return (
    <Card as="section" className="space-y-3">
      <h2 className="text-lg font-semibold">
        {title} ({entries.length})
      </h2>
      {entries.length === 0 ? (
        <p className="text-sm text-muted">Brak pozycji.</p>
      ) : (
        <ul className="space-y-3">
          {entries.map((entry) => (
            <li
              key={entry.documentId}
              className="space-y-2 rounded-md bg-subtle p-3 text-sm"
            >
              <p className="break-all">
                {entry.inputPath} →{" "}
                {title === "Uwzględnione"
                  ? entry.outputPath
                  : "brak pliku wynikowego"}
              </p>
              <StatusBadge status={entry.status} />
              {entry.status === "foreign" && (
                <p>Potwierdzony dokument obcy: dokładnie {"{}"}.</p>
              )}
              {entry.reasons.map((reason) => (
                <p key={reason} className="break-words">
                  {reason}
                </p>
              ))}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
export function BatchExportView({ batchId }: { batchId: string }) {
  const plan = useBatchExportPlan(batchId);
  const exported = useExportBatchResults();
  return (
    <AppPage
      header={
        <PageHeader
          title="Eksport częściowy"
          subtitle={`Partia ${batchId} · Wariant A: ścisła walidacja`}
        />
      }
    >
      {plan.isPending ? (
        <LoadingState label="Przygotowywanie planu eksportu" />
      ) : plan.isError ? (
        <ErrorState
          description="Nie udało się przygotować planu partii."
          onRetry={() => void plan.refetch()}
        />
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-muted">
            Scenariusz syntetyczny · {plan.data.included.length} uwzględnione,{" "}
            {plan.data.omitted.length} pominięte
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <ExportEntries title="Uwzględnione" entries={plan.data.included} />
            <ExportEntries title="Pominięte" entries={plan.data.omitted} />
          </div>
          <Banner tone="info">
            Wariant A: wyniki z null niedozwolonym nie są uwzględniane,
            zastępczy {"{}"} dla awarii nie powstaje. Raport pominięć to osobny
            plik, poza output/. ZIP i odtwarzanie folderów są E2; wyniki
            pobierane są jako osobne pliki JSON.
          </Banner>
          {plan.data.included.length === 0 && (
            <EmptyState title="Brak wyników do pobrania" />
          )}
          <div className="flex flex-wrap gap-2">
            <Button
              disabled={exported.isPending || plan.data.included.length === 0}
              onClick={() =>
                exported.mutate(batchId, {
                  onSuccess: (files) =>
                    files.forEach((file) => download(file.fileName, file.json)),
                })
              }
            >
              Pobierz {plan.data.included.length} wyniki
            </Button>
            <Button
              variant="secondary"
              onClick={() =>
                download(
                  `raport-pominiec-${batchId}.json`,
                  JSON.stringify(
                    { batchId, omitted: plan.data.omitted },
                    null,
                    2,
                  ),
                )
              }
            >
              Pobierz raport pominięć
            </Button>
            <Link
              href={`/dokumenty?partia=${encodeURIComponent(batchId)}`}
              className="inline-flex min-h-11 items-center px-4 underline"
            >
              Wróć
            </Link>
          </div>
          {exported.isSuccess && (
            <Banner tone="success">
              Przygotowano {exported.data.length} osobne pliki JSON.
              Przeglądarka może wymagać zgody na pobranie wielu plików.
            </Banner>
          )}
          {exported.isError && (
            <Banner tone="error">
              Eksport nie powiódł się. Odśwież plan i sprawdź decyzje
              eksportowe.
            </Banner>
          )}
        </div>
      )}
    </AppPage>
  );
}
