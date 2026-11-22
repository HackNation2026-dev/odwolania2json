import Link from "next/link";
import { Button } from "@/components/atoms/Button";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import type { DocumentRecord } from "@/lib/api/schemas";
import s from "./dokument.module.css";
export function DocumentHeader({
  doc,
  documents,
}: {
  doc: DocumentRecord;
  documents?: DocumentRecord[];
}) {
  const index = documents?.findIndex((item) => item.id === doc.id) ?? -1;
  const previous = index > 0 ? documents?.[index - 1] : undefined;
  const next = index >= 0 ? documents?.[index + 1] : undefined;
  return (
    <header className={s.header}>
      <div className="min-w-0">
        <p className={s.breadcrumb}>
          <Link href="/dokumenty">Dokumenty</Link> / {doc.batchId}
        </p>
        <h1 className="break-all text-lg font-semibold">{doc.fileName}</h1>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded bg-subtle px-2 py-1">
            {doc.className ?? "Klasa nieustalona"}
          </span>
          <StatusBadge status={doc.status} />
          <span className={s.resultMeta}>
            {doc.status === "error"
              ? "Brak wyniku"
              : doc.status === "running"
                ? "Analiza trwa"
                : "Wynik analizy"}{" "}
            · dane syntetyczne
          </span>
        </div>
      </div>
      <nav aria-label="Sąsiednie dokumenty" className={s.documentNavigation}>
        {previous ? (
          <Link
            className="inline-flex min-h-11 items-center rounded border border-control px-3 text-sm"
            href={`/dokumenty/${previous.id}`}
          >
            ‹ Poprzedni
          </Link>
        ) : (
          <Button className="min-h-11" variant="secondary" disabled>
            ‹ Poprzedni
          </Button>
        )}
        <span className="text-xs">
          {index >= 0 ? index + 1 : "—"} z {documents?.length ?? "—"}
        </span>
        {next ? (
          <Link
            className="inline-flex min-h-11 items-center rounded border border-control px-3 text-sm"
            href={`/dokumenty/${next.id}`}
          >
            Następny ›
          </Link>
        ) : (
          <Button className="min-h-11" variant="secondary" disabled>
            Następny ›
          </Button>
        )}
      </nav>
    </header>
  );
}
