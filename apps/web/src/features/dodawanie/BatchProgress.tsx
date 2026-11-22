"use client";

import Link from "next/link";
import { ProgressBar } from "@/components/molecules/ProgressBar";
import { PipelineProgress } from "./PipelineProgress";
import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { DocumentTable } from "@/features/dokumenty-lista/DocumentTable";
import type { DocumentRecord } from "@/lib/api/schemas";

export function BatchProgress({
  documents,
  total,
  name,
  refreshError,
  onRefresh,
}: {
  documents: DocumentRecord[];
  total: number;
  name: string;
  refreshError: boolean;
  onRefresh: () => void;
}) {
  const [filter, setFilter] = useState("all");
  const completed = documents.filter((d) => d.status !== "running").length;
  const finished = documents.length === total && completed === total;
  const filters = [
    { id: "all", label: "Wszystkie", count: total },
    {
      id: "ready",
      label: "Pełne / częściowe",
      count: documents.filter((d) => ["full", "partial"].includes(d.status))
        .length,
    },
    {
      id: "foreign",
      label: "Obce",
      count: documents.filter((d) => d.status === "foreign").length,
    },
    {
      id: "error",
      label: "Błędy techniczne",
      count: documents.filter((d) => d.status === "error").length,
    },
    {
      id: "running",
      label: "W toku",
      count: documents.filter((d) => d.status === "running").length,
    },
  ];
  const visible = documents.filter(
    (d) =>
      filter === "all" ||
      (filter === "ready"
        ? ["full", "partial"].includes(d.status)
        : d.status === filter),
  );
  return (
    <section
      className="min-w-0 rounded-md border border-border bg-surface p-5"
      aria-label="Postęp analizy"
    >
      <h2 className="mb-3 text-xl font-semibold">
        {finished ? "Analiza zakończona" : "Analiza w toku"}
      </h2>
      <p className="mb-3 break-words text-sm text-muted">{name}</p>
      <div aria-live="polite" role="status">
        <p className="rounded-md bg-[var(--running-bg)] p-3 text-sm text-[var(--running-fg)]">
          Przetworzono {completed} z {total} dokumentów
        </p>
        <ProgressBar
          label="Postęp analizy"
          value={total ? (completed / total) * 100 : 0}
        />
      </div>
      <div aria-label="Filtr postępu" className="mb-3 flex flex-wrap gap-2">
        {filters.map((item) => (
          <Button
            key={item.id}
            className="min-h-11 px-3 text-xs"
            variant={filter === item.id ? "primary" : "secondary"}
            aria-pressed={filter === item.id}
            onClick={() => setFilter(item.id)}
          >
            {item.label} {item.count}
          </Button>
        ))}
      </div>
      <DocumentTable documents={visible} />
      {visible.length === 0 && (
        <p className="py-3 text-sm text-muted">
          Brak dokumentów o wybranym statusie.
        </p>
      )}
      {documents.map((document) => (
        <PipelineProgress
          key={document.id}
          documentId={document.id}
          fileName={document.fileName}
        />
      ))}
      {refreshError && (
        <p role="alert">
          Nie udało się odświeżyć postępu.{" "}
          <Button className="min-h-11" variant="secondary" onClick={onRefresh}>
            Spróbuj ponownie
          </Button>
        </p>
      )}
      {finished && (
        <Link
          href="/dokumenty"
          className="mt-4 inline-flex min-h-11 items-center rounded-md bg-primary px-4 text-sm text-on-primary"
        >
          Przejdź do dokumentów
        </Link>
      )}
    </section>
  );
}
