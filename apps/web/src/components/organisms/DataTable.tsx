"use client";
import { useState, type ReactNode, type Key } from "react";
import { EmptyState } from "@/components/molecules/EmptyState";
import { ErrorState } from "@/components/molecules/ErrorState";
import { LoadingState } from "@/components/molecules/LoadingState";
import { useDesktopLayout } from "@/components/useDesktopLayout";
export type DataColumn<Row> = {
  key: string;
  label: string;
  render: (row: Row) => ReactNode;
  sortValue?: (row: Row) => string | number | null;
};
export type TableSort = { key: string; direction: "asc" | "desc" };
export type DataTableProps<Row> = {
  columns: DataColumn<Row>[];
  rows: Row[];
  rowKey: (row: Row) => Key;
  cardTitle: (row: Row) => ReactNode;
  caption: string;
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
  emptyTitle?: string;
  sort?: TableSort;
  onSortChange?: (sort: TableSort) => void;
};
export function DataTable<Row>({
  columns,
  rows,
  rowKey,
  cardTitle,
  caption,
  loading,
  error,
  onRetry,
  emptyTitle = "Brak wyników",
  sort,
  onSortChange,
}: DataTableProps<Row>) {
  const [internal, setInternal] = useState<TableSort>();
  const wide = useDesktopLayout();
  const activeSort = sort ?? internal;
  function changeSort(key: string) {
    const next: TableSort = {
      key,
      direction:
        activeSort?.key === key && activeSort.direction === "asc"
          ? "desc"
          : "asc",
    };
    if (sort === undefined) setInternal(next);
    onSortChange?.(next);
  }
  if (loading) return <LoadingState />;
  if (error) return <ErrorState description={error} onRetry={onRetry} />;
  if (!rows.length) return <EmptyState title={emptyTitle} />;
  const column = columns.find((column) => column.key === activeSort?.key);
  const sorted = column?.sortValue
    ? [...rows].sort((a, b) => {
        const x = column.sortValue!(a),
          y = column.sortValue!(b);
        const order =
          x === null
            ? y === null
              ? 0
              : 1
            : y === null
              ? -1
              : typeof x === "number" && typeof y === "number"
                ? x - y
                : String(x).localeCompare(String(y), "pl");
        return activeSort?.direction === "desc" ? -order : order;
      })
    : rows;
  return (
    <div className="min-w-0">
      {wide ? (
        <div>
          <table className="w-full table-fixed border-collapse text-left text-sm">
            <caption className="mb-2 text-left font-semibold">
              {caption}
            </caption>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    scope="col"
                    key={column.key}
                    aria-sort={
                      column.sortValue
                        ? activeSort?.key === column.key
                          ? activeSort.direction === "asc"
                            ? "ascending"
                            : "descending"
                          : "none"
                        : undefined
                    }
                    className="break-words border-b border-border p-3"
                  >
                    {column.sortValue ? (
                      <button
                        type="button"
                        className="min-h-11 text-left underline"
                        onClick={() => changeSort(column.key)}
                      >
                        {column.label}
                        <span aria-hidden="true">
                          {" "}
                          {activeSort?.key === column.key
                            ? activeSort.direction === "asc"
                              ? "↑"
                              : "↓"
                            : "↕"}
                        </span>
                      </button>
                    ) : (
                      column.label
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <tr key={rowKey(row)}>
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className="break-words border-b border-border p-3 align-top"
                    >
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <section aria-label={caption} className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {columns
              .filter((column) => column.sortValue)
              .map((column) => (
                <button
                  type="button"
                  key={column.key}
                  onClick={() => changeSort(column.key)}
                  className="min-h-11 rounded border border-control px-3 text-sm"
                  aria-label={`Sortuj: ${column.label}${activeSort?.key === column.key ? (activeSort.direction === "asc" ? ", rosnąco" : ", malejąco") : ""}`}
                >
                  {column.label} <span aria-hidden="true">↕</span>
                </button>
              ))}
          </div>
          {sorted.map((row) => (
            <article
              key={rowKey(row)}
              className="rounded-lg border border-border bg-surface p-4"
            >
              <h2 className="break-words font-semibold">{cardTitle(row)}</h2>
              <dl>
                {columns.map((column) => (
                  <div key={column.key} className="my-2 min-w-0">
                    <dt className="text-xs text-muted">{column.label}</dt>
                    <dd className="break-words text-sm">
                      {column.render(row)}
                    </dd>
                  </div>
                ))}
              </dl>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
