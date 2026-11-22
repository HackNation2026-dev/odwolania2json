"use client";
import { Button } from "@/components/atoms";
export function EvidenceQuote({
  quote,
  page,
  source,
  confidence,
  onSelect,
}: {
  quote: string;
  page: number;
  source: "ocr" | "text";
  confidence?: number;
  onSelect?: () => void;
}) {
  return (
    <figure className="min-w-0 space-y-2 rounded border border-border p-3">
      <blockquote className="break-words text-sm">„{quote}”</blockquote>
      <figcaption className="text-xs text-muted">
        Str. {page} · Źródło: {source === "ocr" ? "OCR" : "tekst PDF"}
        {confidence !== undefined &&
          ` · Pewność: ${Math.round(confidence * 100)}%`}
      </figcaption>
      {onSelect && (
        <Button variant="ghost" onClick={onSelect}>
          Pokaż dowód na stronie {page}
        </Button>
      )}
    </figure>
  );
}
