"use client";
import Link from "next/link";
import { useState } from "react";
import { DocumentExportPolicy } from "./DocumentExportPolicy";
import { DocumentFooter } from "./DocumentFooter";
import { Button } from "@/components/atoms/Button";
import { DocumentHeader } from "./DocumentHeader";
import {
  useDocument,
  useDocuments,
  useExportDecision,
  useExportJson,
  useSystemInfo,
} from "@/lib/api/hooks";
import { ApiError } from "@/lib/api/client";
import { DocumentTabs } from "./DocumentTabs";
import { DocumentPreview } from "./DocumentPreview";
import { DocumentException } from "./DocumentException";
import { DocumentFields } from "./DocumentFields";
import { DocumentDiagnosis } from "./DocumentDiagnosis";
import { DocumentOcrNotice } from "./DocumentOcrNotice";
import { LoadingState } from "@/components/molecules";
import { DocumentEvidence } from "./DocumentEvidence";
import { DocumentJson } from "./DocumentJson";
import { downloadText, formatDocumentJson } from "./format";
import { DocumentProcessing } from "./DocumentProcessing";
import s from "./dokument.module.css";

export function DocumentView({
  id,
  tab = "przeglad",
}: {
  id: string;
  tab?: string;
}) {
  const query = useDocument(id);
  const documents = useDocuments();
  const decision = useExportDecision(id);
  const exportJson = useExportJson();
  const system = useSystemInfo();
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<string | null>(null);
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const activeTab = ["json", "dowody", "eksport", "dokument"].includes(tab)
    ? tab
    : "przeglad";
  if (query.isPending) return <LoadingState label="Wczytywanie dokumentu…" />;
  if (query.isError)
    return (
      <section role="alert" className="mx-auto max-w-md py-16 text-center">
        <p className="text-6xl font-bold text-muted">
          {query.error instanceof ApiError && query.error.code === "NOT_FOUND"
            ? "404"
            : "!"}
        </p>
        <h1 className="mt-4 text-xl font-semibold">
          {query.error instanceof ApiError && query.error.code === "NOT_FOUND"
            ? "Nie znaleziono strony"
            : "Nie udało się wczytać dokumentu"}
        </h1>
        <p className="my-4">
          {query.error instanceof ApiError && query.error.code === "NOT_FOUND"
            ? "Nie znaleziono tej sprawy lub dokumentu. Mógł zostać usunięty."
            : "Nie udało się połączyć z serwerem. Sprawdź połączenie i spróbuj ponownie."}
        </p>
        <Link
          href="/dodaj"
          className="inline-flex min-h-11 items-center rounded bg-primary px-4 text-on-primary"
        >
          Przejdź do nowej analizy
        </Link>
        <Button
          className="mt-3 min-h-11"
          variant="secondary"
          onClick={() => query.refetch()}
        >
          Spróbuj ponownie
        </Button>
      </section>
    );
  const doc = query.data;
  const json = formatDocumentJson(doc);
  function selectEvidence(evidenceId: string) {
    const evidence = doc.evidence.find((e) => e.id === evidenceId);
    if (!evidence) return;
    setSelected(evidence.id);
    setSelectedField(
      doc.fields.find((field) => field.evidenceIds.includes(evidence.id))
        ?.key ?? evidence.fieldKey,
    );
    setPage(evidence.page);
  }
  const selectedEvidence = doc.evidence.find((e) => e.id === selected);
  async function downloadJson() {
    // Przyjętego kliknięcia nie odrzucamy podczas odświeżania; API ponownie waliduje eksport.
    try {
      const result = await exportJson.mutateAsync(id);
      downloadText(result.fileName, result.json);
      setMessage("Pobrano JSON.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Nie udało się pobrać JSON.");
    }
  }
  function downloadReport(evidenceOnly: boolean) {
    const data = evidenceOnly
      ? {
          documentId: id,
          evidence: doc.evidence,
          ocr: doc.evidence.some((item) => item.source === "ocr")
            ? (system.data?.ocr ?? { mode: "unknown" })
            : null,
        }
      : {
          documentId: id,
          status: doc.status,
          reasons: doc.reasons,
          gaps: doc.fields
            .filter((f) => f.gap)
            .map((f) => ({ field: f.key, ...f.gap })),
          processedPages: doc.processedPages,
          unprocessedPages: doc.unprocessedPages,
          errorCode: doc.errorCode,
          pages: doc.pages,
          exportDecision: decision.data ?? null,
        };
    downloadText(
      `${doc.fileName.replace(/\.pdf$/i, "")}.${evidenceOnly ? "dowody" : "raport"}.json`,
      JSON.stringify(data, null, 2),
    );
  }
  return (
    <div className={s.workspace}>
      <DocumentHeader doc={doc} documents={documents.data} />
      <div className={s.columns}>
        <DocumentPreview
          doc={doc}
          page={page}
          setPage={setPage}
          selected={selected}
          select={selectEvidence}
          mobileVisible={activeTab === "dokument"}
        />
        <div className={s.content}>
          <DocumentTabs id={id} activeTab={activeTab} />
          <div
            role="region"
            aria-label="Zawartość widoku dokumentu"
            tabIndex={0}
            className={`${activeTab === "dokument" ? "" : "scroll-pane"} ${s.panel} ${activeTab === "dokument" ? s.mobileHidden : ""}`}
          >
            {(activeTab === "przeglad" || activeTab === "dokument") && (
              <>
                <DocumentException doc={doc} />
                <DocumentOcrNotice doc={doc} />
                <p className="text-xs text-muted">
                  {["full", "partial", "foreign"].includes(doc.status)
                    ? `Wynik v${doc.resultVersion}`
                    : "Brak zapisanej wersji wyniku"}{" "}
                  · Kontrakt: {doc.contractRevision}
                </p>
                {doc.className && (
                  <div className={s.recognition}>
                    <strong>
                      Rozpoznano: {doc.className} · na podstawie treści
                      dokumentu
                    </strong>
                    <details>
                      <summary>Dlaczego?</summary>
                      <p>
                        Wynik klasyfikacji pochodzi z silnika. Dostępne cytaty i
                        źródła znajdziesz w zakładce Dowody.
                      </p>
                    </details>
                  </div>
                )}
                <div data-document-draft-slot />
                {doc.fields.length > 0 && (
                  <DocumentFields
                    doc={doc}
                    selectedField={selectedField}
                    onSelectField={(key) => {
                      setSelectedField(key);
                      const field = doc.fields.find((item) => item.key === key);
                      const evidence = doc.evidence.find((item) =>
                        field?.evidenceIds.includes(item.id),
                      );
                      if (evidence) selectEvidence(evidence.id);
                      else setSelected(null);
                    }}
                  />
                )}
                <DocumentDiagnosis id={id} className={doc.className} />
                <DocumentProcessing id={id} />
                {selectedEvidence && (
                  <p role="status" className="my-3 text-sm">
                    Wybrany dowód: strona {selectedEvidence.page} ·{" "}
                    {selectedEvidence.quote}
                  </p>
                )}
              </>
            )}
            {activeTab === "json" && (
              <DocumentJson
                json={json}
                blocked={!decision.data?.allowed || decision.isFetching}
              />
            )}
            {activeTab === "dowody" && (
              <DocumentEvidence
                doc={doc}
                select={selectEvidence}
                downloadReport={() => downloadReport(false)}
              />
            )}
            {activeTab === "eksport" && <DocumentExportPolicy doc={doc} />}
          </div>
          <DocumentFooter
            id={id}
            decision={decision}
            activeTab={activeTab}
            downloading={exportJson.isPending}
            failed={exportJson.isError}
            downloadJson={downloadJson}
            downloadEvidence={() => downloadReport(true)}
            message={message}
          />
        </div>
      </div>
    </div>
  );
}
