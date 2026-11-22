"use client";
import Link from "next/link";
import { useState } from "react";
import { Button, Select, StatusBadge } from "@/components/atoms";
import { DataTable } from "@/components/organisms/DataTable";
import { Banner, ErrorState, LoadingState } from "@/components/molecules";
import { useBatches, useRetryDocument } from "@/lib/api/hooks";
import type { DocumentRecord } from "@/lib/api/schemas";
import { documentCodes, type Filters } from "./filters";

export function BatchBrowser({
  filters,
  onChange,
  documents,
}: {
  filters: Filters;
  onChange: (filters: Filters) => void;
  documents: DocumentRecord[];
}) {
  const [expanded, setExpanded] = useState(Boolean(filters.partia));
  const batches = useBatches();
  const retry = useRetryDocument();
  const batch = batches.data?.find((b) => b.id === filters.partia);
  const groups = [...new Set(batch?.entries.map((e) => e.group))].map(
    (group) => ({
      group,
      documents: batch!.entries
        .filter((e) => e.group === group)
        .flatMap((e) => documents.filter((d) => d.id === e.documentId)),
    }),
  );
  return (
    <details
      open={expanded}
      onToggle={(event) => setExpanded(event.currentTarget.open)}
      className="rounded-lg border border-border bg-surface p-4"
    >
      <summary className="flex min-h-11 cursor-pointer items-center font-medium">
        Partie i sprawy · E2
      </summary>
      {expanded &&
        (batches.isPending ? (
          <LoadingState label="Ładowanie partii" />
        ) : batches.isError ? (
          <ErrorState onRetry={() => void batches.refetch()} />
        ) : (
          <div className="space-y-4">
            <label className="block max-w-sm text-sm">
              Partia
              <Select
                value={filters.partia ?? ""}
                onChange={(event) => {
                  const selected = batches.data.find(
                    (b) => b.id === event.target.value,
                  );
                  onChange({
                    ...filters,
                    partia: selected?.id,
                    documentIds: selected?.entries.map((e) => e.documentId),
                  });
                }}
              >
                <option value="">Wszystkie partie</option>
                {batches.data.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </Select>
            </label>
            <Banner tone="info">
              Foldery i archiwum ZIP to E2 — funkcje nie są dostępne. Plan
              eksportu i osobne pliki JSON są dostępne w demonstracji.
            </Banner>
            {batch && (
              <>
                <div className="flex flex-wrap gap-2">
                  <Link
                    className="inline-flex min-h-11 items-center rounded-md bg-primary px-4 text-sm text-on-primary"
                    href={`/dokumenty/eksport?partia=${encodeURIComponent(batch.id)}`}
                  >
                    Pobierz wyniki partii (ZIP) · plan E2
                  </Link>
                  <Button
                    variant="secondary"
                    disabled
                    aria-describedby="batch-e2"
                  >
                    Pobierz dowody partii · E2
                  </Button>
                  <Button
                    variant="secondary"
                    disabled={
                      retry.isPending ||
                      !groups.some((g) =>
                        g.documents.some((d) => d.status === "error"),
                      )
                    }
                    onClick={() => {
                      for (const document of groups
                        .flatMap((g) => g.documents)
                        .filter((d) => d.status === "error"))
                        retry.mutate(document.id);
                    }}
                  >
                    Ponów nieudane
                  </Button>
                </div>
                <p id="batch-e2" className="text-sm text-muted">
                  Dowody partii i zachowanie folderów przy pobieraniu wymagają
                  archiwum E2.
                </p>
                <DataTable
                  rows={groups}
                  rowKey={(g) => g.group}
                  cardTitle={(g) => g.group}
                  caption={`Sprawy partii ${batch.id}`}
                  columns={[
                    { key: "group", label: "Sprawa", render: (g) => g.group },
                    {
                      key: "count",
                      label: "Dokumenty",
                      render: (g) => g.documents.length,
                    },
                    {
                      key: "status",
                      label: "Status",
                      render: (g) => (
                        <div className="flex flex-wrap gap-2">
                          {g.documents.map((d) => (
                            <StatusBadge key={d.id} status={d.status} />
                          ))}
                        </div>
                      ),
                    },
                    {
                      key: "codes",
                      label: "Kod",
                      render: (g) =>
                        [...new Set(g.documents.flatMap(documentCodes))].join(
                          " · ",
                        ) || "Nie zgłoszono odstępstw",
                    },
                  ]}
                />
              </>
            )}
            {filters.partia && !batch && (
              <Banner tone="warning">
                Nie znaleziono wskazanej partii. Wybierz partię z listy.
              </Banner>
            )}
            {retry.isError && (
              <Banner tone="error">Nie udało się ponowić analizy.</Banner>
            )}
          </div>
        ))}
    </details>
  );
}
