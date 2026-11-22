"use client";
import { Button } from "@/components/atoms/Button";
import { useRetryDocument } from "@/lib/api/hooks";
import type { DocumentRecord } from "@/lib/api/schemas";
import type { Filters } from "./filters";
export function QuickStatusFilters({
  all,
  filters,
  change,
}: {
  all: DocumentRecord[];
  filters: Filters;
  change: (filters: Filters) => void;
}) {
  const retry = useRetryDocument();
  return (
    <>
      {all.length > 0 && (
        <>
          {all.some((d) => d.status === "error") && (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[var(--error-fg)] bg-[var(--error-bg)] p-4 text-sm text-[var(--error-fg)]">
              <p>
                Analiza zakończona z błędem.{" "}
                {all.filter((d) => d.status === "error").length} dokumentów nie
                zostało przetworzonych z powodu błędu technicznego — wynik
                ekstrakcji nie został zapisany. Pozostałe dokumenty są dostępne.
              </p>
              <Button
                variant="secondary"
                className="min-h-11"
                disabled={retry.isPending}
                onClick={() => {
                  for (const d of all.filter((d) => d.status === "error"))
                    retry.mutate(d.id);
                }}
              >
                Ponów nieudane
              </Button>
              {retry.isError && (
                <p role="alert">Nie udało się ponowić analizy.</p>
              )}
            </div>
          )}
          <div
            className="flex flex-wrap gap-2"
            role="group"
            aria-label="Szybki filtr statusu"
          >
            {[
              { label: "Wszystkie", statuses: [] },
              { label: "Pełne / częściowe", statuses: ["full", "partial"] },
              { label: "Obce", statuses: ["foreign"] },
              { label: "Błędy techniczne", statuses: ["error"] },
              { label: "W toku", statuses: ["running"] },
            ].map((item) => (
              <Button
                key={item.label}
                variant={
                  filters.statuses.join() === item.statuses.join()
                    ? "primary"
                    : "secondary"
                }
                className="min-h-11 text-xs"
                onClick={() =>
                  change({
                    ...filters,
                    statuses: item.statuses as Filters["statuses"],
                  })
                }
              >
                {item.label}{" "}
                {
                  all.filter(
                    (d) =>
                      !item.statuses.length || item.statuses.includes(d.status),
                  ).length
                }
              </Button>
            ))}
          </div>
        </>
      )}
    </>
  );
}
