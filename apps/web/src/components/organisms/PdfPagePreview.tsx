"use client";
import { useState } from "react";
import { Button } from "@/components/atoms";
import { Banner } from "@/components/molecules/Banner";
import { EmptyState } from "@/components/molecules/EmptyState";
export type PreviewEvidence = {
  id: string;
  page: number;
  quote: string;
  source: "ocr" | "text";
  confidence: number;
  box: { x: number; y: number; w: number; h: number };
};
export type PdfPagePreviewProps = {
  pages: number;
  page: number;
  onPageChange: (page: number) => void;
  pageText: string[];
  title?: string;
  evidence?: PreviewEvidence[];
  selected?: string | null;
  onSelect?: (id: string) => void;
};
export function PdfPagePreview({
  pages,
  page,
  onPageChange,
  pageText,
  title = "DOKUMENT",
  evidence = [],
  selected,
  onSelect,
}: PdfPagePreviewProps) {
  const [text, setText] = useState(false);
  const [thumbnails, setThumbnails] = useState(false);
  const [zoom, setZoom] = useState(100);
  const current = Math.max(1, Math.min(pages, page));
  const proofs = evidence.filter((item) => item.page === current);
  return (
    <section
      aria-label="Podgląd dokumentu"
      className="min-w-0 rounded-lg border border-border bg-subtle p-3"
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Button
          variant="ghost"
          aria-pressed={thumbnails}
          onClick={() => setThumbnails(!thumbnails)}
        >
          Miniatury
        </Button>
        <span aria-live="polite">
          Strona {pages ? current : 0} z {pages}
        </span>
        <Button
          variant="ghost"
          disabled={zoom <= 75}
          aria-label="Pomniejsz"
          onClick={() => setZoom(zoom - 25)}
        >
          −
        </Button>
        <span>{zoom}%</span>
        <Button
          variant="ghost"
          disabled={zoom >= 150}
          aria-label="Powiększ"
          onClick={() => setZoom(zoom + 25)}
        >
          +
        </Button>
        <Button variant="ghost" onClick={() => setZoom(100)}>
          Dopasuj do szerokości
        </Button>
        <Button
          variant={text ? "secondary" : "primary"}
          aria-pressed={!text}
          onClick={() => setText(false)}
        >
          PDF
        </Button>
        <Button
          variant={text ? "primary" : "secondary"}
          aria-pressed={text}
          onClick={() => setText(true)}
        >
          Tekst strony
        </Button>
      </div>
      {thumbnails && (
        <div
          className="mb-3 flex flex-wrap gap-2"
          role="group"
          aria-label="Miniatury stron"
        >
          {Array.from({ length: pages }, (_, i) => (
            <Button
              key={i}
              variant="secondary"
              aria-label={`Przejdź do strony ${i + 1}`}
              onClick={() => onPageChange(i + 1)}
            >
              {i + 1}
            </Button>
          ))}
        </div>
      )}
      {text &&
        proofs.some(
          (item) => item.source === "ocr" && item.confidence < 0.9,
        ) && (
          <Banner tone="warning" title="Niska jakość odczytu OCR">
            Porównaj fragment z dokumentem.
          </Banner>
        )}
      {pages === 0 ? (
        <EmptyState
          title="Podgląd niedostępny"
          description="Nie odczytano stron pliku."
        />
      ) : (
        <>
          <div
            role="region"
            aria-label="Strona PDF; strzałki zmieniają stronę"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
                event.preventDefault();
                onPageChange(
                  Math.max(
                    1,
                    Math.min(
                      pages,
                      current + (event.key === "ArrowRight" ? 1 : -1),
                    ),
                  ),
                );
              }
            }}
            className="relative min-h-96 overflow-hidden bg-[var(--pdf-page)] p-6 text-[var(--text)]"
            style={{
              fontSize: `${(13 * zoom) / 100}px`,
              color: "var(--evidence-border)",
            }}
          >
            <h2 className="mb-4 font-semibold">
              {text
                ? `Strona ${current} · ${proofs.some((item) => item.source === "ocr") ? "Skan — tekst z OCR" : "Tekst PDF"}`
                : title}
            </h2>
            <p className="whitespace-pre-wrap break-words">
              {pageText[current - 1] ??
                "Brak tekstu dla tej strony. Strona może wymagać OCR."}
            </p>
            {proofs.map((item) => (
              <button
                type="button"
                key={item.id}
                aria-label={`Dowód: ${item.quote}`}
                aria-pressed={selected === item.id}
                onClick={() => onSelect?.(item.id)}
                className={
                  text
                    ? "mt-4 block min-h-11 w-full rounded border border-control p-2 text-left"
                    : "absolute min-h-11 min-w-11 rounded border-2 border-[var(--evidence-border)]"
                }
                style={
                  text
                    ? selected === item.id
                      ? { background: "var(--evidence-bg)" }
                      : undefined
                    : {
                        left: `${item.box.x * 100}%`,
                        top: `${item.box.y * 100}%`,
                        width: `${item.box.w * 100}%`,
                        height: `${item.box.h * 100}%`,
                        background:
                          selected === item.id
                            ? "var(--evidence-bg)"
                            : undefined,
                      }
                }
              >
                {text ? (
                  item.quote
                ) : (
                  <span className="sr-only">{item.quote}</span>
                )}
              </button>
            ))}
          </div>
          <p className="mt-3 text-center text-xs text-muted">
            Podgląd syntetyczny, nie oryginalny PDF. Obrys według geometrii
            dowodu.
          </p>
          <div className="mt-3 flex flex-wrap justify-between gap-2">
            <Button
              variant="secondary"
              disabled={current <= 1}
              onClick={() => onPageChange(current - 1)}
            >
              Poprzednia strona
            </Button>
            <Button
              variant="secondary"
              disabled={current >= pages}
              onClick={() => onPageChange(current + 1)}
            >
              Następna strona
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
