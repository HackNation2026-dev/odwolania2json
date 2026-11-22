"use client";
import Link from "next/link";
import { Button } from "@/components/atoms/Button";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import type { DocumentRecord } from "@/lib/api/schemas";
import { Card } from "@/components/atoms/Card";

export function DocumentResultsTable({
  documents,
  onRetry,
  retryPending,
  retryError,
}: {
  documents: DocumentRecord[];
  onRetry: (id: string) => void;
  retryPending: boolean;
  retryError: boolean;
}) {
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
                      disabled={retryPending}
                      onClick={() => onRetry(d.id)}
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
          <Card key={d.id} as="article" padding="sm" className="space-y-2">
            <div className="flex flex-wrap justify-between gap-2">
              <h2 className="min-w-0 break-all text-sm font-semibold">
                <Link
                  href={`/dokumenty/${d.id}`}
                  className="inline-flex min-h-11 items-center"
                >
                  {d.fileName}
                </Link>
              </h2>
              <StatusBadge status={d.status} />
            </div>
            <p className="text-xs text-muted">
              {d.pages} str. ·{" "}
              {d.evidence.some((e) => e.source === "ocr") ? "OCR" : "tekst"}
            </p>
            {d.errorCode && <p className="break-all text-xs">{d.errorCode}</p>}
            <p className="text-sm">Rozpoznano jako: {d.className ?? "—"}</p>
            <p className="text-sm">
              Pola:{" "}
              {d.fields.length
                ? `${d.fields.filter((f) => f.value !== null).length}/${d.fields.length}`
                : "brak wyniku ekstrakcji"}
            </p>
            <p className="break-all text-xs text-muted">
              Plik wynikowy:{" "}
              {["full", "partial", "foreign"].includes(d.status)
                ? `${d.fileName.replace(/\.pdf$/i, ".json")}${d.status === "foreign" ? " ({})" : ""}`
                : "brak wyniku"}
            </p>
            {d.status === "error" ? (
              <Button
                variant="secondary"
                className="min-h-11 w-full"
                disabled={retryPending}
                onClick={() => onRetry(d.id)}
              >
                Ponów
              </Button>
            ) : (
              <Link
                href={`/dokumenty/${d.id}`}
                className="flex min-h-11 items-center justify-center rounded-md border border-control text-sm"
              >
                Przejrzyj
              </Link>
            )}
          </Card>
        ))}
      </div>
      {retryError && (
        <p role="alert">Nie udało się ponowić analizy. Spróbuj ponownie.</p>
      )}
    </>
  );
}
