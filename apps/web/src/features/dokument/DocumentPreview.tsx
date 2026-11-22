"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/atoms/Button";
import { EmptyState } from "@/components/molecules/EmptyState";
import { Banner } from "@/components/molecules/Banner";
import { PdfViewer } from "@/components/organisms/PdfViewer";
import type { DocumentRecord } from "@/lib/api/schemas";
import { documentPdfFile } from "@/lib/api/mock/document-pdf";
import { DocumentPageText } from "./DocumentPageText";
import { DocumentGeometryStyles } from "./DocumentGeometryStyles";
import { DocumentRegions } from "./DocumentRegions";
import s from "./dokument.module.css";

type Props = {
  doc: DocumentRecord;
  page: number;
  setPage: (page: number) => void;
  selected: string | null;
  select: (id: string) => void;
  mobileVisible: boolean;
};

export function DocumentPreview({
  doc,
  page,
  setPage,
  selected,
  select,
  mobileVisible,
}: Props) {
  const root = useRef<HTMLElement>(null);
  const fit = () => {
    if (root.current)
      setScale(Math.max(0.25, (root.current.clientWidth - 48) / 595.28));
  };
  const [text, setText] = useState(false);
  const [thumbnails, setThumbnails] = useState(false);
  const [scale, setScale] = useState(0.7);
  const [loadedPages, setLoadedPages] = useState<number>();
  const evidence = doc.evidence.find((item) => item.id === selected);
  const selectedField = doc.fields.find((field) =>
    field.evidenceIds.includes(selected ?? ""),
  );
  const file = documentPdfFile(doc);
  const visiblePage = Math.min(page, loadedPages ?? doc.pages);
  useEffect(() => {
    if (!root.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      if (root.current)
        setScale(Math.max(0.25, (root.current.clientWidth - 48) / 595.28));
    });
    observer.observe(root.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={root}
      aria-label="Podgląd dokumentu"
      className={`${s.preview} ${mobileVisible ? s.mobilePreview : ""}`}
    >
      <DocumentGeometryStyles doc={doc} />
      <div className={s.toolbar}>
        <Button
          variant="ghost"
          className={s.thumbnailToggle}
          aria-pressed={thumbnails}
          onClick={() => setThumbnails(!thumbnails)}
        >
          Miniatury
        </Button>
        <span aria-live="polite">
          Strona {visiblePage} z {loadedPages ?? doc.pages}
        </span>
        <Button
          variant="ghost"
          aria-label="Pomniejsz"
          disabled={scale <= 0.3}
          onClick={() => setScale(Math.max(0.3, scale - 0.1))}
        >
          −
        </Button>
        <output aria-label="Powiększenie">{Math.round(scale * 100)}%</output>
        <Button
          variant="ghost"
          aria-label="Powiększ"
          disabled={scale >= 2}
          onClick={() => setScale(Math.min(2, scale + 0.1))}
        >
          +
        </Button>
        <Button variant="ghost" onClick={fit}>
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
      {loadedPages !== undefined && loadedPages !== doc.pages && (
        <Banner tone="warning">
          Plik demo ma {loadedPages} stron; zapisany rekord wskazuje {doc.pages}
          . Pozostałe strony nie są dostępne w tym zasobie.
        </Banner>
      )}
      {doc.pages === 0 ? (
        <EmptyState title="Podgląd niedostępny: nie odczytano stron pliku." />
      ) : (
        <>
          {selected && (
            <DocumentRegions doc={doc} selected={selected} select={select} />
          )}
          {text ? (
            <DocumentPageText
              key={`${file}-${visiblePage}`}
              doc={doc}
              file={file}
              page={visiblePage}
              select={select}
            />
          ) : (
            <div
              role="region"
              aria-label="Strona PDF; strzałki zmieniają stronę"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.target !== event.currentTarget) return;
                if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
                  event.preventDefault();
                  setPage(
                    Math.max(
                      1,
                      Math.min(
                        loadedPages ?? doc.pages,
                        page + (event.key === "ArrowRight" ? 1 : -1),
                      ),
                    ),
                  );
                }
              }}
            >
              <PdfViewer
                className={`${s.pdf} ${thumbnails ? "pdf-show-thumbnails" : ""}`}
                file={file}
                page={visiblePage}
                onPageChange={setPage}
                scale={scale}
                onScaleChange={setScale}
                onLoadSuccess={({ numPages }) => setLoadedPages(numPages)}
                highlights={doc.evidence
                  .filter((item) => item.box)
                  .map((item) => ({
                    id: item.id,
                    page: item.page,
                    box: item.box!,
                    label: `${item.fieldKey} · ${item.id} · ${item.quote}`,
                    active: item.id === selected,
                  }))}
                onHighlightClick={select}
              />
            </div>
          )}
          <details className="my-2 text-xs">
            <summary className="flex min-h-11 cursor-pointer items-center">Dowody na stronie — lista obszarów</summary>
            <div className="flex flex-col items-start gap-2">
              {doc.evidence.filter(item => item.page === visiblePage).map(item => (
                <Button key={item.id} variant="ghost" className="min-h-11 max-w-full whitespace-normal text-left" aria-pressed={item.id === selected} onClick={() => select(item.id)}>{item.id} · {item.fieldKey} · {item.quote}</Button>
              ))}
              {!doc.evidence.some(item => item.page === visiblePage) && <p>Brak dowodów dla tej strony.</p>}
            </div>
          </details>
          <p className="my-3 text-center text-xs text-muted">
            Materiał demonstracyjny — prawdziwy PDF, dane syntetyczne.
            {evidence &&
              !evidence.box &&
              " Położenie przybliżone. Brak dokładnej geometrii dowodu."}
          </p>
          <div className="flex flex-wrap justify-between gap-2">
            <Button
              variant="secondary"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              Poprzednia strona
            </Button>
            <Button
              variant="secondary"
              disabled={page >= (loadedPages ?? doc.pages)}
              onClick={() => setPage(page + 1)}
            >
              Następna strona
            </Button>
          </div>
          {selectedField && (
            <Link
              className="mt-3 inline-flex min-h-11 items-center underline"
              href={`/dokumenty/${doc.id}?tab=przeglad#field-${selectedField.key}`}
            >
              ‹ Wróć do pola {selectedField.label}
            </Link>
          )}
        </>
      )}
    </section>
  );
}
