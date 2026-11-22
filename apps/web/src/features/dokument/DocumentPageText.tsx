"use client";
import { useEffect, useState } from "react";
import { extractPageText } from "@/components/organisms/PdfViewer";
import {
  Banner,
  EmptyState,
  ErrorState,
  EvidenceQuote,
  LoadingState,
} from "@/components/molecules";
import { useDiagnosis, useSystemInfo } from "@/lib/api/hooks";
import type { DocumentRecord } from "@/lib/api/schemas";

export function DocumentPageText({
  doc,
  file,
  page,
  select,
}: {
  doc: DocumentRecord;
  file: string;
  page: number;
  select: (id: string) => void;
}) {
  const diagnosis = useDiagnosis(doc.id);
  const system = useSystemInfo();
  const [result, setResult] = useState<{ text: string } | { error: true }>();
  const [attempt, setAttempt] = useState(0);
  const source = diagnosis.data?.pages.find(
    (item) => item.number === page,
  )?.text_source;
  const evidence = doc.evidence.filter((item) => item.page === page);
  const ocr = source === "ocr";
  useEffect(() => {
    let cancelled = false;
    extractPageText(file, page).then(
      (text) => {
        if (!cancelled) setResult({ text });
      },
      () => {
        if (!cancelled) setResult({ error: true });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [file, page, attempt]);
  return (
    <section
      aria-label="Tekst odczytany ze strony"
      className="space-y-3 rounded border border-border bg-surface p-4"
    >
      <h2 className="font-semibold">
        Strona {page} ·{" "}
        {ocr
          ? "Skan — tekst z OCR"
          : source === "none"
            ? "Strona nieprzetworzona"
            : "Tekst PDF"}
      </h2>
      {diagnosis.isPending && (
        <LoadingState label="Wczytywanie źródła tekstu…" />
      )}
      {diagnosis.isError && (
        <ErrorState
          title="Nie udało się odczytać źródła tekstu"
          onRetry={() => diagnosis.refetch()}
        />
      )}
      {ocr && (
        <Banner
          tone="warning"
          title="Niska jakość odczytu OCR na tej stronie. Porównaj fragment z dokumentem."
        >
          Źródło: OCR{" "}
          {system.data?.ocr.mode === "shim"
            ? "tymczasowy (shim)"
            : "— zapisany odczyt"}
          . {system.data?.ocr.detail}
        </Banner>
      )}
      {source === "none" ? (
        <EmptyState
          title="Nie przetworzono strony"
          description="Szczegóły i kody w diagnozie. Brak odczytu nie oznacza braku informacji."
        />
      ) : !result ? (
        <LoadingState label="Odczytywanie tekstu…" />
      ) : "error" in result ? (
        <ErrorState
          title="Nie udało się odczytać tekstu strony"
          onRetry={() => {
            setResult(undefined);
            setAttempt(attempt + 1);
          }}
        />
      ) : result.text ? (
        <p className="whitespace-pre-wrap break-words">{result.text}</p>
      ) : ocr ? (
        <p className="whitespace-pre-wrap break-words">
          {doc.pageText[page - 1] ||
            "Brak zapisanego tekstu OCR dla tej strony."}
        </p>
      ) : (
        <EmptyState title="Brak warstwy tekstowej. Ta strona wymaga OCR." />
      )}
      {evidence.map((item) => (
        <EvidenceQuote
          key={item.id}
          quote={item.quote}
          page={item.page}
          source={item.source === "ocr" ? "ocr" : "text"}
          confidence={item.confidence ?? undefined}
          onSelect={() => select(item.id)}
        />
      ))}
    </section>
  );
}
