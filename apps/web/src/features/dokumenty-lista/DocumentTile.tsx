import Link from "next/link";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import type { DocumentRecord } from "@/lib/api/schemas";
import { documentCodes } from "./filters";

export function PdfThumb() {
  return (
    <div
      aria-hidden="true"
      className="flex h-44 items-center justify-center bg-[var(--pdf-canvas)] p-4"
    >
      <svg viewBox="0 0 110 144" className="h-full drop-shadow-sm">
        <rect x="4" y="1" width="102" height="140" fill="var(--pdf-page)" />
        <path d="M18 18h64" stroke="var(--muted)" strokeWidth="7" />
        <path
          d="M18 33h74M18 44h68M18 55h76M18 66h63M18 77h48"
          stroke="var(--border-control)"
          strokeOpacity=".5"
          strokeWidth="4"
        />
      </svg>
    </div>
  );
}
export function DocumentTile({ document: d }: { document: DocumentRecord }) {
  const tone =
    d.status === "error"
      ? "border-[var(--error-fg)]"
      : d.status === "partial"
        ? "border-[var(--partial-fg)]"
        : ["ambiguous", "multi"].includes(d.status)
          ? "border-[var(--ambiguous-fg)]"
          : "border-border";
  return (
    <Link
      href={`/dokumenty/${encodeURIComponent(d.id)}`}
      className={`block min-w-0 overflow-hidden rounded-lg border bg-surface transition-shadow hover:shadow-md ${tone}`}
    >
      <PdfThumb />
      <div className="space-y-2 p-3">
        <h2 className="break-all text-sm font-semibold">{d.fileName}</h2>
        <p className="text-xs text-muted">
          {d.className ?? "Klasa nieustalona"}
        </p>
        <StatusBadge status={d.status} /><p className="break-all text-xs text-muted">Plik wynikowy: {["full", "partial", "foreign"].includes(d.status) ? d.fileName.replace(/\.pdf$/i, ".json") : "brak wyniku"}</p>
        <p className="text-xs text-muted">
          {d.pages} str. ·{" "}
          {new Date(d.uploadedAt).toLocaleDateString("pl-PL", {
            timeZone: "Europe/Warsaw",
          })}
        </p>
        {documentCodes(d).length > 0 && (
          <p className="break-words text-xs text-muted">
            {documentCodes(d).join(" · ")}
          </p>
        )}
        {d.status === "running" && (
          <p className="text-xs" aria-live="polite">
            Analiza: {d.progress ?? 0}%
          </p>
        )}
      </div>
    </Link>
  );
}
