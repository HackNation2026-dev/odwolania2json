"use client";
import Link from "next/link";
import { Button } from "@/components/atoms";
import { EmptyState } from "@/components/molecules";
import { DataTable, type DataColumn } from "@/components/organisms/DataTable";
import type { DocumentRecord, Evidence } from "@/lib/api/schemas";
import s from "./dokument.module.css";

export function DocumentEvidence({
  doc,
  select,
  downloadReport,
}: {
  doc: DocumentRecord;
  select: (id: string) => void;
  downloadReport: () => void;
}) {
  const fieldFor = (id: string) =>
    doc.fields.find((field) => field.evidenceIds.includes(id));
  const columns: DataColumn<Evidence>[] = [
    {
      key: "field",
      label: "Pole",
      render: (item) => <code>{fieldFor(item.id)?.key ?? item.fieldKey}</code>,
    },
    { key: "page", label: "Str.", render: (item) => item.page },
    {
      key: "quote",
      label: "Fragment",
      render: (item) => (
        <Link
          href={`/dokumenty/${doc.id}?tab=dokument`}
          onClick={() => select(item.id)}
          aria-label={`Pokaż dowód: ${item.quote}`}
        >
          „{item.quote}”
        </Link>
      ),
    },
    {
      key: "source",
      label: "Źródło tekstu",
      render: (item) => (
        <>
          {item.source === "ocr" ? "OCR — zapisany odczyt" : "tekst PDF"}
          <br />
          <span className="text-muted">
            Pewność:{" "}
            {item.confidence === null
              ? "Nie oceniono"
              : `${Math.round(item.confidence * 100)}%`}
          </span>
        </>
      ),
    },
    {
      key: "method",
      label: "Metoda",
      render: (item) => (
        <>
          {item.method === "ai"
            ? "model"
            : item.method === "rule"
              ? "wyliczone"
              : "reguła"}
          <br />
          {item.rule} {item.premiseIds.join(", ")}
          {!item.box && <p>Brak dokładnej geometrii dowodu.</p>}
        </>
      ),
    },
  ];
  return (
    <>
      <p className="mb-3 text-xs text-muted">
        Dowody są zapisane poza ocenianym JSON. Czytelna postać cytatów i źródeł
        tego dokumentu.
      </p>
      {doc.evidence.length ? (
        <div className={s.evidenceData}>
          <DataTable
            columns={columns}
            rows={doc.evidence}
            rowKey={(item) => item.id}
            cardTitle={(item) =>
              `${fieldFor(item.id)?.label ?? item.fieldKey} · str. ${item.page}`
            }
            caption="Dowody pól dokumentu"
          />
        </div>
      ) : (
        <EmptyState title="Brak dostępnych dowodów dla tego dokumentu." />
      )}
      <section className={s.notice}>
        <h2 className="text-sm font-semibold">Pokrycie stron</h2>
        <p className="text-xs">
          Plik: {doc.pages} stron. Dostępny tekst:{" "}
          {doc.pageText.slice(0, doc.pages).filter(Boolean).length} stron.
          Dowody: {doc.evidence.length}.
        </p>
        <p className="mt-1 text-xs text-muted">
          Sprawdzone strony: {doc.processedPages.join(", ") || "brak"}.
          Nieprzetworzone strony: {doc.unprocessedPages.join(", ") || "brak"}.
        </p>
      </section>
      <p className="mb-3 text-xs text-muted">
        Plik dowodów: {doc.fileName.replace(/\.pdf$/i, "")}.dowody.json ·
        powiązany z dokumentem {doc.id}.
      </p>
      <Button variant="secondary" className="min-h-11" onClick={downloadReport}>
        Pobierz osobny raport
      </Button>
    </>
  );
}
