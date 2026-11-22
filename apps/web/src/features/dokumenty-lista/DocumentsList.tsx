"use client";

import Link from "next/link";
import {
  VIEW_STORAGE_KEY,
  subscribeView,
  readView,
  subscribeFilters,
} from "./viewStorage";
export { VIEW_STORAGE_KEY } from "./viewStorage";
import { QuickStatusFilters } from "./QuickStatusFilters";
import { useState, useSyncExternalStore } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { Button } from "@/components/atoms/Button";
import { DocumentTable } from "./DocumentTable";
import { BatchBrowser } from "./BatchBrowser";
import { useClasses, useDocuments, useBatches } from "@/lib/api/hooks";
import { DocumentTile } from "./DocumentTile";
import { FilterBar } from "./FilterBar";
import {
  emptyFilters,
  filterDocuments,
  parseFilters,
  serializeFilters,
  type Filters,
  type View,
} from "./filters";

export function DocumentsListContent({
  filters,
  onChange,
  preferredView,
}: {
  filters: Filters;
  onChange: (filters: Filters) => void;
  preferredView?: View;
}) {
  const documents = useDocuments();
  const classes = useClasses();
  const [size, setSize] = useState("M");
  const [limit, setLimit] = useState(8);
  const all = documents.data ?? [];
  const batches = useBatches();
  const batch = batches.data?.find((b) => b.id === filters.partia);
  const results = filterDocuments(all, {
    ...filters,
    documentIds: batch?.entries.map((e) => e.documentId) ?? filters.documentIds,
  });
  const view =
    filters.widok ?? preferredView ?? (all.length >= 7 ? "galeria" : "tabela");
  const visible = results.slice(0, limit);
  function change(f: Filters) {
    setLimit(8);
    onChange(f);
  }
  function changeView(widok: View) {
    try {
      localStorage.setItem(VIEW_STORAGE_KEY, widok);
    } catch {
      /* Pamięć przeglądarki może być niedostępna. */
    }
    onChange({ ...filters, widok });
  }
  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <p className="text-sm text-muted">Dokumenty / Dodane dokumenty</p>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Dodane dokumenty</h1>
          <p className="mt-1 text-sm text-muted">
            {all.length} dokumentów · bieżąca sesja
          </p>
        </div>
        <div
          className="flex flex-wrap gap-2"
          role="group"
          aria-label="Widok dokumentów"
        >
          <Button
            className="min-h-11"
            variant={view === "galeria" ? "primary" : "secondary"}
            aria-pressed={view === "galeria"}
            onClick={() => changeView("galeria")}
          >
            ▦ Kafelki
          </Button>
          <Button
            className="min-h-11"
            variant={view === "tabela" ? "primary" : "secondary"}
            aria-pressed={view === "tabela"}
            onClick={() => changeView("tabela")}
          >
            ☷ Lista
          </Button>
        </div>
      </div>
      <FilterBar
        filters={filters}
        onChange={change}
        documents={all}
        classes={classes.data ?? []}
        shown={visible.length}
        size={size}
        onSize={view === "galeria" ? setSize : undefined}
      />
      <BatchBrowser key={filters.partia ?? "all"} filters={filters} onChange={change} documents={all} />
      {view === "tabela" && (
        <QuickStatusFilters all={all} filters={filters} change={change} />
      )}
      {documents.isPending || classes.isPending ? (
        <div role="status" aria-label="Ładowanie dokumentów">
          <p className="sr-only">Ładowanie dokumentów…</p>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 8 }, (_, i) => (
              <div
                key={i}
                className="h-72 animate-pulse rounded-lg border border-border bg-subtle"
              />
            ))}
          </div>
        </div>
      ) : documents.isError || classes.isError ? (
        <div
          role="alert"
          className="rounded-lg border border-[var(--error-fg)] bg-surface p-6"
        >
          <h2 className="font-semibold">
            Nie udało się wczytać dokumentów lub filtrów
          </h2>
          <p className="my-2 text-sm">Sprawdź połączenie i spróbuj ponownie.</p>
          <Button
            className="min-h-11"
            onClick={() => {
              void documents.refetch();
              void classes.refetch();
            }}
          >
            Spróbuj ponownie
          </Button>
        </div>
      ) : (
        <>
          <p className="sr-only" role="status" aria-live="polite">
            Znaleziono {results.length} dokumentów
          </p>
          {results.length === 0 ? (
            <div className="rounded-lg border border-border bg-surface px-4 py-16 text-center">
              <span aria-hidden className="text-3xl text-muted">
                ⌕
              </span>
              <h2 className="mt-3 font-semibold">
                {all.length
                  ? "Brak dokumentów spełniających kryteria"
                  : "Nie dodano jeszcze dokumentów"}
              </h2>
              <p className="my-3 text-sm text-muted">
                {all.length
                  ? `Nic nie pasuje do wybranych filtrów${filters.q ? ` i frazy „${filters.q}”` : ""}. Zmień kryteria lub wyczyść filtry.`
                  : "Dodaj pliki PDF, aby zobaczyć wyniki analizy."}
              </p>
              {all.length ? (
                <Button
                  variant="secondary"
                  className="min-h-11"
                  onClick={() =>
                    change({ ...emptyFilters, widok: filters.widok })
                  }
                >
                  Wyczyść filtry
                </Button>
              ) : (
                <Link
                  href="/dodaj"
                  className="inline-flex min-h-11 items-center rounded-md bg-primary px-4 text-on-primary"
                >
                  Dodaj dokumenty
                </Link>
              )}
            </div>
          ) : view === "galeria" ? (
            <div
              data-testid="document-gallery"
              className={`grid gap-4 sm:grid-cols-2 ${size === "S" ? "lg:grid-cols-4 2xl:grid-cols-5" : size === "L" ? "xl:grid-cols-3" : "xl:grid-cols-4"}`}
            >
              {visible.map((d) => (
                <DocumentTile key={d.id} document={d} />
              ))}
            </div>
          ) : (
            <DocumentTable documents={visible} />
          )}
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
            <span>
              Wczytano {visible.length} z {results.length} dokumentów
            </span>
            {visible.length < results.length && (
              <Button
                variant="ghost"
                className="min-h-11"
                onClick={() => setLimit(limit + 8)}
              >
                Wczytaj kolejne 8
              </Button>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export function DocumentsList() {
  const params = useSearchParams();
  const pathname = usePathname();
  const preferredView = useSyncExternalStore(
    subscribeView,
    readView,
    () => undefined,
  );
  const search = useSyncExternalStore(
    subscribeFilters,
    () => window.location.search,
    () => params.toString(),
  );
  const filters = parseFilters(new URLSearchParams(search));
  return (
    <DocumentsListContent
      filters={filters}
      preferredView={preferredView}
      onChange={(f) => {
        const query = serializeFilters(f).toString();
        window.history.replaceState(
          null,
          "",
          `${pathname}${query ? `?${query}` : ""}`,
        );
        window.dispatchEvent(new Event("o2j-filters"));
      }}
    />
  );
}
