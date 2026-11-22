"use client";

import Link from "next/link";
import { Card } from "@/components/atoms/Card";
import { SystemReadiness } from "@/features/dodawanie/SystemReadiness";
import { StatusBadge, statusMeta } from "@/components/atoms/StatusBadge";
import { Button } from "@/components/atoms/Button";
import { useDashboard, useKeyStatus } from "@/lib/api/hooks";
import type { DocumentStatus } from "@/lib/api/schemas";

const statuses: DocumentStatus[] = [
  "full",
  "partial",
  "ambiguous",
  "foreign",
  "error",
  "running",
  "multi",
];
const actionClass =
  "inline-flex min-h-11 items-center justify-center rounded-md border border-control px-4 text-sm font-medium";

export function DashboardView() {
  const dashboard = useDashboard();
  const key = useKeyStatus();
  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <header>
        <h1 className="text-3xl font-semibold">Pulpit</h1>
        <p className="mt-1 text-sm text-muted">
          Stan systemu i ostatnia aktywność
        </p>
      </header>
      {key.data?.configured === false && (
        <div
          role="note"
          className="rounded-md bg-[var(--partial-bg)] p-4 text-[var(--partial-fg)]"
        >
          ⚠ Brak klucza API modelu.{" "}
          <Link
            className="inline-flex min-h-11 items-center underline"
            href="/klucz"
          >
            Skonfiguruj klucz
          </Link>
        </div>
      )}
      {key.isError && (
        <p role="alert">
          Nie udało się sprawdzić konfiguracji klucza.{" "}
          <Button
            className="min-h-11"
            variant="secondary"
            onClick={() => void key.refetch()}
          >
            Spróbuj ponownie
          </Button>
        </p>
      )}
      <SystemReadiness />
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-subtle p-3 text-sm">
        <span>Gotowość modelu i OCR: nie sprawdzono</span>
        <Link
          href="/jak-to-dziala"
          className="inline-flex min-h-11 items-center underline"
        >
          Szczegóły gotowości ›
        </Link>
      </div>
      {dashboard.isPending ? (
        <div
          role="status"
          aria-label="Ładowanie pulpitu"
          className="h-32 animate-pulse rounded-md bg-subtle"
        />
      ) : dashboard.isError ? (
        <div role="alert" className="rounded-md border border-border p-4">
          Nie udało się wczytać pulpitu.{" "}
          <Button
            className="min-h-11"
            variant="secondary"
            onClick={() => void dashboard.refetch()}
          >
            Spróbuj ponownie
          </Button>
        </div>
      ) : (
        <>
          <section
            aria-label="Liczniki dokumentów"
            className="grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-8"
          >
            <Link
              href="/dokumenty"
              className="rounded-md border border-border bg-surface p-4"
            >
              <strong className="block text-3xl">{dashboard.data.total}</strong>
              <span className="text-sm">Dokumenty łącznie</span>
            </Link>
            {statuses.map((status) => (
              <Link
                key={status}
                href={`/dokumenty?status=${status}`}
                className={`rounded-md p-4 ${statusMeta[status].tone}`}
              >
                <strong className="block text-3xl">
                  {dashboard.data.byStatus[status] ?? 0}
                </strong>
                <span className="break-words text-xs">
                  {statusMeta[status].icon} {statusMeta[status].label}
                </span>
              </Link>
            ))}
          </section>
          <section
            aria-label="Szybkie akcje"
            className="grid gap-4 md:grid-cols-2"
          >
            <Card
              padding="none"
              className="rounded-md! border-control bg-subtle! p-5!"
            >
              <h2 className="text-xl font-semibold">Dodaj dokumenty</h2>
              <p className="my-3 text-sm text-muted">
                Wgraj pliki PDF z akt sprawy i uruchom analizę. Każdy dokument
                analizujemy niezależnie.
              </p>
              <Link
                className={`${actionClass} bg-primary text-on-primary`}
                href="/dodaj"
              >
                + Dodaj dokumenty
              </Link>
            </Card>
            <Card padding="none" className="rounded-md! p-5!">
              <h2 className="text-xl font-semibold">Przeglądaj dokumenty</h2>
              <p className="my-3 text-sm text-muted">
                {dashboard.data.total} dokumentów. Wyszukiwanie, filtrowanie i
                sortowanie.
              </p>
              <Link className={actionClass} href="/dokumenty">
                Przeglądaj dokumenty
              </Link>
            </Card>
          </section>
          <div className="grid gap-4 md:grid-cols-2">
            <Card as="section" padding="none" className="rounded-md! p-5!">
              <h2 className="mb-3 text-lg font-semibold">Wymaga uwagi</h2>
              {dashboard.data.recent
                .filter((d) =>
                  ["error", "ambiguous", "partial", "multi"].includes(d.status),
                )
                .map((d) => (
                  <Link
                    key={d.id}
                    href={`/dokumenty/${d.id}`}
                    className="flex min-h-11 flex-wrap items-center justify-between gap-2 py-2"
                  >
                    <span className="min-w-0 break-all text-sm">
                      {d.fileName}
                    </span>
                    <StatusBadge status={d.status} />
                  </Link>
                ))}
              <Link
                href="/dokumenty?status=error"
                className="inline-flex min-h-11 items-center text-sm underline"
              >
                Zobacz błędy ›
              </Link>
            </Card>
            <Card as="section" padding="none" className="rounded-md! p-5!">
              <h2 className="mb-3 text-lg font-semibold">Ostatnie dokumenty</h2>
              {dashboard.data.recent.length === 0 ? (
                <p className="text-sm text-muted">
                  Nie masz jeszcze żadnych analiz.
                </p>
              ) : (
                <ul>
                  {dashboard.data.recent.map((d) => (
                    <li key={d.id}>
                      <Link
                        className="flex min-h-11 flex-wrap items-center justify-between gap-2 py-2"
                        href={`/dokumenty/${d.id}`}
                      >
                        <span className="min-w-0 break-all text-sm">
                          {d.fileName}
                        </span>
                        <StatusBadge status={d.status} />
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
              <Link
                href="/dokumenty"
                className="inline-flex min-h-11 items-center text-sm underline"
              >
                Zobacz wszystkie ›
              </Link>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
