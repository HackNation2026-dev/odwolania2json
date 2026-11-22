"use client";

import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { Select } from "@/components/atoms/Select";
import { Banner } from "@/components/molecules/Banner";
import { FormField } from "@/components/molecules/FormField";
import { PageHeader } from "@/components/organisms/PageHeader";
import { DataTable } from "@/components/organisms/DataTable";
import { AppPage } from "@/components/templates/AppPage";
import { useAuditEvents, useExportAuditCsv } from "@/lib/api/hooks";
import type { AuditQuery } from "@/lib/api/schemas";

export const eventLabels: Record<string, string> = {
  upload: "Wgranie",
  analysis: "Analiza",
  error: "Błąd",
  correction: "Korekta",
  export: "Eksport",
  configuration: "Aktywacja YAML",
  reveal: "Odsłonięcie",
  denied: "Odmowa odsłonięcia",
};

export function EventsView() {
  const [filters, setFilters] = useState<AuditQuery>({});
  const query = useAuditEvents(filters);
  const csv = useExportAuditCsv();
  function filter(key: keyof AuditQuery, value: string) {
    setFilters((previous) => ({ ...previous, [key]: value }));
    csv.reset();
  }
  function download() {
    csv.mutate(filters, {
      onSuccess: (result) => {
        const url = URL.createObjectURL(
          new Blob([result.csv], { type: "text/csv;charset=utf-8" }),
        );
        const link = document.createElement("a");
        link.href = url;
        link.download = result.fileName;
        link.click();
        URL.revokeObjectURL(url);
      },
    });
  }
  const filtered = Object.values(filters).some(Boolean);
  return (
    <AppPage
      header={
        <PageHeader
          title="Dziennik zdarzeń"
          actions={
            <Button
              variant="secondary"
              disabled={csv.isPending || query.isPending || query.isError}
              onClick={download}
            >
              {csv.isPending ? "Przygotowywanie CSV…" : "Eksportuj CSV"}
            </Button>
          }
        />
      }
    >
      <Banner tone="neutral" role="note">
        E3 · Scenariusz syntetyczny. Wpisy tylko do odczytu. Szczegóły zmian
        „Było / Jest” maskuje serwer. Odsłonięcie rejestruje nazwę pola, bez
        wartości.
      </Banner>
      <div className="grid items-end gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <FormField label="Rodzaj zdarzenia">
          {(a11y) => (
            <Select
              {...a11y}
              value={filters.type ?? ""}
              onChange={(event) => filter("type", event.target.value)}
            >
              <option value="">Wszystkie zdarzenia</option>
              {Object.entries(eventLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          )}
        </FormField>
        <FormField label="Użytkownik">
          {(a11y) => (
            <Input
              {...a11y}
              value={filters.user ?? ""}
              onChange={(event) => filter("user", event.target.value)}
            />
          )}
        </FormField>
        <div className="grid gap-2">
          <FormField label="Data od">
            {(a11y) => (
              <Input
                {...a11y}
                type="date"
                value={filters.dateFrom ?? ""}
                onChange={(event) => filter("dateFrom", event.target.value)}
              />
            )}
          </FormField>
          <FormField label="Data do">
            {(a11y) => (
              <Input
                {...a11y}
                type="date"
                value={filters.dateTo ?? ""}
                onChange={(event) => filter("dateTo", event.target.value)}
              />
            )}
          </FormField>
        </div>
        <FormField label="Obiekt">
          {(a11y) => (
            <Input
              {...a11y}
              value={filters.object ?? ""}
              onChange={(event) => filter("object", event.target.value)}
            />
          )}
        </FormField>
        <Button
          variant="secondary"
          className="min-h-11"
          onClick={() => {
            setFilters({});
            csv.reset();
          }}
        >
          Wyczyść filtry
        </Button>
      </div>
      {csv.isSuccess && (
        <p role="status">CSV gotowy. Wyeksportowano zamaskowane wpisy.</p>
      )}
      {csv.isError && (
        <Banner
          tone="error"
          actions={<Button onClick={download}>Ponów</Button>}
        >
          Nie udało się przygotować CSV. Ponów.
        </Banner>
      )}
      {query.isSuccess && (
        <p role="status" aria-label="Liczba zdarzeń" className="sr-only">
          Liczba zdarzeń: {query.data.length}
        </p>
      )}
      <DataTable
        caption="Syntetyczny dziennik zdarzeń"
        rows={query.data ?? []}
        rowKey={(event) => event.id}
        cardTitle={(event) => event.description}
        loading={query.isPending}
        error={
          query.isError ? "Nie udało się wczytać dziennika zdarzeń." : undefined
        }
        onRetry={() => void query.refetch()}
        emptyTitle={
          filtered
            ? "Brak zdarzeń spełniających kryteria."
            : "Brak zdarzeń w tym zakresie."
        }
        columns={[
          {
            key: "time",
            label: "Czas",
            render: (event) => (
              <time dateTime={event.occurredAt}>
                {new Date(event.occurredAt).toLocaleString("pl-PL", {
                  timeZone: "Europe/Warsaw",
                  dateStyle: "short",
                  timeStyle: "short",
                })}
              </time>
            ),
          },
          { key: "user", label: "Użytkownik", render: (event) => event.user },
          {
            key: "event",
            label: "Zdarzenie",
            render: (event) => event.description,
          },
          { key: "object", label: "Obiekt", render: (event) => event.object },
          {
            key: "detail",
            label: "Szczegóły",
            render: (event) => event.detail,
          },
        ]}
      />
    </AppPage>
  );
}
