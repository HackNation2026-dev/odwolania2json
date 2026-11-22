"use client";
import { DocumentResultsTable } from "@/components/organisms/DocumentResultsTable";
import { useRetryDocument } from "@/lib/api/hooks";
import type { DocumentRecord } from "@/lib/api/schemas";
export function DocumentTable({ documents }: { documents: DocumentRecord[] }) {
  const retry = useRetryDocument();
  return (
    <DocumentResultsTable
      documents={documents}
      onRetry={(id) => retry.mutate(id)}
      retryPending={retry.isPending}
      retryError={retry.isError}
    />
  );
}
