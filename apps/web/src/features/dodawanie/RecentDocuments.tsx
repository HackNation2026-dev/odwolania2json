"use client";
import Link from "next/link";
import { Button, Input, Select, StatusBadge } from "@/components/atoms";
import { type useAddDocumentsState } from "./useAddDocumentsState";
export function RecentDocuments({
  state,
}: {
  state: ReturnType<typeof useAddDocumentsState>;
}) {
  const { documents, search, setSearch, sort, setSort, recent } = state;
  return (
    <section aria-labelledby="recent-added">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 id="recent-added" className="text-lg font-semibold">
          Ostatnio dodane
        </h2>
        <Link
          className="inline-flex min-h-11 items-center text-sm underline"
          href="/dokumenty"
        >
          Przeglądaj wszystkie ›
        </Link>
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        <label className="min-w-0 flex-1">
          <span className="sr-only">Szukaj po nazwie pliku</span>
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Szukaj po nazwie pliku"
            className="min-h-11 md:min-h-11 py-0 w-full rounded-md border border-control bg-surface px-3 text-sm"
          />
        </label>
        <label>
          <span className="sr-only">Sortowanie</span>
          <Select
            value={sort}
            onChange={(event) => setSort(event.target.value)}
            className="min-h-11 md:min-h-11 py-0 w-auto max-w-full rounded-md border border-control bg-surface px-3 text-sm"
          >
            <option value="newest">Najnowsze</option>
            <option value="name">Nazwa</option>
          </Select>
        </label>
      </div>
      {documents.isPending ? (
        <div role="status" className="h-48 animate-pulse rounded-md bg-subtle">
          Ładowanie dokumentów…
        </div>
      ) : documents.isError ? (
        <div role="alert">
          Nie udało się pobrać dokumentów.{" "}
          <Button
            className="min-h-11"
            variant="secondary"
            onClick={() => void documents.refetch()}
          >
            Spróbuj ponownie
          </Button>
        </div>
      ) : recent.length === 0 ? (
        <p className="text-sm text-muted">
          {search
            ? "Brak dokumentów pasujących do wyszukiwania."
            : "Nie masz jeszcze żadnych analiz."}
        </p>
      ) : (
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {recent.map((d) => (
            <li className="min-w-0" key={d.id}>
              <Link
                href={`/dokumenty/${d.id}`}
                className="block overflow-hidden rounded-md border border-border bg-surface"
              >
                <div
                  aria-hidden
                  className="flex h-28 items-center justify-center bg-subtle"
                >
                  <span className="bg-surface px-6 py-4 text-3xl text-muted">
                    ▤
                  </span>
                </div>
                <div className="space-y-2 p-3">
                  <p className="break-all text-xs font-medium">{d.fileName}</p>
                  <StatusBadge status={d.status} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
