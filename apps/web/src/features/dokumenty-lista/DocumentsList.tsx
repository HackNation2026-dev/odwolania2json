"use client";

import Link from "next/link";
import { useState, useSyncExternalStore } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { Button } from "@/components/atoms/Button";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { useClasses, useDocuments, useRetryDocument } from "@/lib/api/hooks";
import type { DocumentRecord } from "@/lib/api/schemas";
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

export const VIEW_STORAGE_KEY = "o2j-documents-view";
function subscribeView(listener: () => void) {
  window.addEventListener("storage", listener);
  return () => window.removeEventListener("storage", listener);
}
function readView(): View | undefined {
  try {
    const saved = localStorage.getItem(VIEW_STORAGE_KEY);
    return saved === "galeria" || saved === "tabela" ? saved : undefined;
  } catch {
    return undefined;
  }
}
function subscribeFilters(listener: () => void) {
  window.addEventListener("popstate", listener);
  window.addEventListener("o2j-filters", listener);
  return () => {
    window.removeEventListener("popstate", listener);
    window.removeEventListener("o2j-filters", listener);
  };
}
function DocumentTable({ documents }: { documents: DocumentRecord[] }) {
  const retry = useRetryDocument();
  return (
    <>
      <div className="hidden overflow-hidden rounded-lg border border-border bg-surface lg:block">
        <table className="w-full table-fixed text-left text-sm">
          <caption className="sr-only">Dodane dokumenty</caption>
          <thead className="bg-subtle text-xs text-muted">
            <tr>
              {[
                "Plik",
                "Rozpoznano jako",
                "Status",
                "Pola",
                "Plik wynikowy",
                "Akcja",
              ].map((h) => (
                <th className="p-3 font-medium" scope="col" key={h}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {documents.map((d) => (
              <tr key={d.id} className="border-t border-border">
                <td className="break-all p-3">
                  <Link className="underline" href={`/dokumenty/${d.id}`}>
                    {d.fileName}
                  </Link>
                  <p className="text-xs text-muted">
                    {d.pages} str. ·{" "}
                    {new Date(d.uploadedAt).toLocaleDateString("pl-PL", {
                      timeZone: "Europe/Warsaw",
                    })}
                  </p>
                </td>
                <td className="p-3">{d.className ?? "Klasa nieustalona"}</td>
                <td className="p-3">
                  <StatusBadge status={d.status} />
                  {d.status === "running" && (
                    <p aria-live="polite">{d.progress ?? 0}%</p>
                  )}
                </td>
                <td className="p-3">
                  {d.fields.length
                    ? `${d.fields.filter((f) => f.value !== null).length}/${d.fields.length}`
                    : "—"}
                  <p className="text-xs text-muted">
                    {d.fields.filter((f) => f.gap?.reviewRequired).length} do
                    sprawdzenia
                  </p>
                </td>
                <td className="break-all p-3 text-xs">
                  {d.status === "foreign"
                    ? `${d.fileName.replace(/\.pdf$/i, ".json")} ({})`
                    : ["full", "partial"].includes(d.status)
                      ? d.fileName.replace(/\.pdf$/i, ".json")
                      : "brak zatwierdzonego wyniku"}
                </td>
                <td className="p-3">
                  {d.status === "error" ? (
                    <Button
                      variant="secondary"
                      className="min-h-11"
                      disabled={retry.isPending}
                      onClick={() => retry.mutate(d.id)}
                    >
                      Ponów
                    </Button>
                  ) : (
                    <Link
                      href={`/dokumenty/${d.id}`}
                      className="inline-flex min-h-11 items-center rounded-md border border-control px-3"
                    >
                      Przejrzyj
                    </Link>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:hidden">
        {documents.map((d) => (
          <DocumentTile key={d.id} document={d} />
        ))}
      </div>
      {retry.isError && (
        <p role="alert">Nie udało się ponowić analizy. Spróbuj ponownie.</p>
      )}
    </>
  );
}

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
  const retry = useRetryDocument();
  const [size, setSize] = useState("M");
  const [limit, setLimit] = useState(8);
  const all = documents.data ?? [];
  const results = filterDocuments(all, filters);
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
      {view === "tabela" && all.length > 0 && (
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
