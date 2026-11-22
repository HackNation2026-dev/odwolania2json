"use client";
import { Banner } from "@/components/molecules";
import { useSystemInfo } from "@/lib/api/hooks";
import type { DocumentRecord } from "@/lib/api/schemas";
import s from "./dokument.module.css";

export function DocumentOcrNotice({ doc }: { doc: DocumentRecord }) {
  const system = useSystemInfo();
  const unavailable = doc.codes.includes("ocr_unavailable");
  const scanned = doc.evidence.some((item) => item.source === "ocr");
  if (!unavailable && !scanned) return null;
  return (
    <div className={`${s.ocrNotice} my-2 space-y-2 text-xs`}>
      {unavailable && (
        <Banner tone="warning">
          <details>
            <summary className="flex min-h-11 cursor-pointer items-center">
              OCR niedostępny · nieprzetworzone strony:{" "}
              {doc.unprocessedPages.join(", ") || "nie przekazano"}
            </summary>
            Strony wymagające OCR pozostaną nieprzetworzone. Brak odczytu nie
            oznacza dokumentu spoza zakresu.
          </details>
        </Banner>
      )}
      {scanned && (
        <Banner tone="warning">
          <details>
            <summary className="flex min-h-11 cursor-pointer items-center">
              {system.data?.ocr.mode === "shim"
                ? "OCR tymczasowy (shim)"
                : "Zapisany odczyt OCR"}
            </summary>
            {system.data?.ocr.name} {system.data?.ocr.version} ·{" "}
            {system.data?.ocr.detail ??
              "Nie sprawdzono bieżącej gotowości OCR."}
            <p>
              Tekst odczytany z obrazu może zawierać błędy. Porównaj go z PDF.
            </p>
          </details>
        </Banner>
      )}
    </div>
  );
}
