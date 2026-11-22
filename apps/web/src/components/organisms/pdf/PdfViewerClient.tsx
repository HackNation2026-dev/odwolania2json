"use client";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import { createPortal } from "react-dom";
import {
  PdfEditor,
  type ToolbarApi,
  type SidebarApi,
} from "react-web-pdf-editor";
import "react-web-pdf-editor/styles.css";
import "./viewer.css";
import { Button } from "@/components/atoms";
import type { PdfViewerProps } from "../PdfViewer";
import { editorPages, editorStage } from "./editorDom";
import { pdfAsset } from "./assets";
import { extractPageText } from "./text";

function Thumbnail({ api, page }: { api: SidebarApi; page: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    let cancelled = false;
    let task: { cancel(): void } | undefined;
    void api.pdf
      ?.getPage(page)
      .then((p) => {
        const canvas = ref.current;
        if (!canvas || cancelled) return;
        const viewport = p.getViewport({
          scale: 90 / p.getViewport({ scale: 1 }).width,
        });
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        task = p.render({ canvas, viewport });
        return (task as ReturnType<typeof p.render>).promise.catch(() => {});
      })
      .catch(() => {});
    return () => {
      cancelled = true;
      task?.cancel();
    };
  }, [api.pdf, page]);
  return (
    <Button
      touch
      variant="ghost"
      aria-label={`Przejdź do strony ${page}`}
      aria-current={api.page === page ? "page" : undefined}
      onClick={() => api.setPage(page)}
    >
      <canvas ref={ref} aria-hidden="true" />
      <span>{page}</span>
    </Button>
  );
}
function Toolbar({
  api,
  root,
  file,
}: {
  api: ToolbarApi;
  root: React.RefObject<HTMLDivElement | null>;
  file: PdfViewerProps["file"];
}) {
  const [text, setText] = useState<{
    file: PdfViewerProps["file"];
    page: number;
    value: string;
  } | null>(null);
  const [textMode, setTextMode] = useState(false);
  const [thumbnails, setThumbnails] = useState(false);
  const textRequest = useRef(0);
  useEffect(() => {
    if (!textMode) return;
    const request = ++textRequest.current;
    let cancelled = false;
    void extractPageText(file, api.page)
      .then((value) => {
        if (!cancelled && request === textRequest.current)
          setText({
            file,
            page: api.page,
            value: value || "Brak warstwy tekstowej. Ta strona wymaga OCR.",
          });
      })
      .catch(() => {
        if (!cancelled && request === textRequest.current)
          setText({
            file,
            page: api.page,
            value: "Nie udało się odczytać tekstu strony.",
          });
      });
    return () => {
      cancelled = true;
    };
  }, [api.page, file, textMode]);
  return (
    <>
      <div
        role="group"
        aria-label="Nawigacja PDF"
        className="flex flex-wrap items-center gap-2 border-b border-border bg-surface p-2 text-fg"
      >
        <Button
          touch
          variant="ghost"
          disabled={api.page <= 1 || api.disabled}
          onClick={api.prevPage}
        >
          Poprzednia strona
        </Button>
        <span aria-live="polite">
          Strona {api.numPages ? api.page : 0} z {api.numPages}
        </span>
        <Button
          touch
          variant="ghost"
          disabled={api.page >= api.numPages || api.disabled}
          onClick={api.nextPage}
        >
          Następna strona
        </Button>
        <Button
          touch
          variant="ghost"
          aria-label="Pomniejsz"
          disabled={api.scale <= api.minScale || api.disabled}
          onClick={api.zoomOut}
        >
          −
        </Button>
        <output aria-label="Powiększenie">
          {Math.round(api.scale * 100)}%
        </output>
        <Button
          touch
          variant="ghost"
          aria-label="Powiększ"
          disabled={api.scale >= api.maxScale || api.disabled}
          onClick={api.zoomIn}
        >
          +
        </Button>
        <Button
          touch
          variant="ghost"
          disabled={api.disabled}
          onClick={() => {
            if (!root.current) return;
            const p = editorPages(root.current)[0];
            const stage = editorStage(root.current);
            if (p && stage)
              api.setScale(
                Math.max(
                  api.minScale,
                  Math.min(
                    api.maxScale,
                    (stage.clientWidth - 32) / (p.offsetWidth / api.scale),
                  ),
                ),
              );
          }}
        >
          Dopasuj do szerokości
        </Button>
        <Button
          touch
          variant="ghost"
          aria-pressed={thumbnails}
          onClick={() => {
            setThumbnails(!thumbnails);
            root.current?.classList.toggle("pdf-show-thumbnails", !thumbnails);
          }}
        >
          Miniatury
        </Button>
        <Button
          touch
          variant="ghost"
          aria-pressed={textMode}
          onClick={() => setTextMode(!textMode)}
        >
          Tekst strony
        </Button>
        <label className="flex min-w-0 items-center gap-2">
          Szukaj w PDF
          <input
            className="min-h-11 min-w-0 w-36 rounded border border-control bg-surface px-2"
            value={api.search.query}
            onChange={(e) => api.search.setQuery(e.target.value)}
            type="search"
          />
        </label>
        <span role="status">{api.search.matchCount} wyników</span>
        <Button
          touch
          variant="ghost"
          disabled={!api.search.matchCount}
          onClick={api.search.prev}
          aria-label="Poprzedni wynik"
        >
          ↑
        </Button>
        <Button
          touch
          variant="ghost"
          disabled={!api.search.matchCount}
          onClick={api.search.next}
          aria-label="Następny wynik"
        >
          ↓
        </Button>
      </div>
      {textMode && (
        <div
          role="region"
          aria-label="Tekst strony"
          className="max-h-60 overflow-auto whitespace-pre-wrap bg-surface p-4 text-fg"
        >
          {text?.file === file && text.page === api.page
            ? text.value
            : "Odczytywanie tekstu…"}
        </div>
      )}
    </>
  );
}
export default function PdfViewerClient({
  highlights = [],
  onHighlightClick,
  className = "",
  ...props
}: PdfViewerProps) {
  const source = props.file;
  const onError = props.onLoadError;
  const onSuccess = props.onLoadSuccess;
  const root = useRef<HTMLDivElement>(null);
  const [loadError, setLoadError] = useState<{
    file: PdfViewerProps["file"];
    error: Error;
  } | null>(null);
  const failed = loadError?.file === props.file;
  const handleLoadError = useCallback(
    (error: Error) => {
      setLoadError({ file: source, error });
      onError?.(error);
    },
    [source, onError],
  );
  const handleLoadSuccess = useCallback(
    (info: { numPages: number }) => {
      setLoadError(null);
      onSuccess?.(info);
    },
    [onSuccess],
  );
  const [shelf, setShelf] = useState<HTMLDivElement | null>(null);
  const [pages, setPages] = useState<HTMLElement[]>([]);
  const apiRef = useRef<ToolbarApi | null>(null);
  const active = highlights.find((item) => item.active);
  const activeId = active?.id;
  const activePage = active?.page;
  useEffect(() => {
    const element = root.current;
    if (!element) return;
    const update = () => {
      const next = editorPages(element);
      setPages((previous) =>
        previous.length === next.length &&
        previous.every((p, i) => p === next[i])
          ? previous
          : next,
      );
    };
    const mutation = new MutationObserver(update);
    mutation.observe(element, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["data-page-number"],
    });
    const resize = new ResizeObserver(update);
    resize.observe(element);
    update();
    return () => {
      mutation.disconnect();
      resize.disconnect();
    };
  }, []);
  useEffect(() => {
    if (!activePage || !root.current) return;
    if (apiRef.current && apiRef.current.page !== activePage)
      apiRef.current.setPage(activePage);
    const target = editorPages(root.current).find(
      (p) => Number(p.dataset.pageNumber) === activePage,
    );
    target?.scrollIntoView?.({ block: "nearest", behavior: "instant" });
  }, [activeId, activePage, pages]);
  return (
    <div
      ref={root}
      className={`pdf-viewer ${className}`}
      style={{ height: 780, maxHeight: "85vh" }}
      // Edytor dodaje obrazy przez drop także przy narzędziu select. Blokujemy ten kanał w fazie capture.
      onDropCapture={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onDragOverCapture={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onKeyDownCapture={(e) => {
        if ((e.target as HTMLElement).closest("input, textarea, button"))
          return;
        const direction = ["PageDown", "ArrowRight", "ArrowDown"].includes(
          e.key,
        )
          ? 1
          : ["PageUp", "ArrowLeft", "ArrowUp"].includes(e.key)
            ? -1
            : 0;
        const api = apiRef.current;
        if (direction && api) {
          e.preventDefault();
          e.stopPropagation();
          api.setPage(
            Math.max(1, Math.min(api.numPages, api.page + direction)),
          );
        }
      }}
    >
      {failed && (
        <p role="alert" className="bg-surface p-4 text-fg">
          Nie udało się wczytać PDF. Sprawdź plik i spróbuj ponownie.
        </p>
      )}
      <div
        ref={setShelf}
        className="pdf-thumbnail-host"
        style={failed ? { display: "none" } : undefined}
      />
      <PdfEditor
        {...props}
        onLoadError={handleLoadError}
        onLoadSuccess={handleLoadSuccess}
        style={failed ? { display: "none" } : undefined}
        workerSrc={pdfAsset("pdf/pdf.worker.min.mjs")}
        minScale={0.25}
        maxScale={3}
        toolbar={(api) => {
          apiRef.current = api;
          return <Toolbar api={api} root={root} file={props.file} />;
        }}
        showSidebar
        sidebar={(api) =>
          shelf
            ? createPortal(
                <aside aria-label="Miniatury stron" className="pdf-thumbnails">
                  {api.pages.map((p) => (
                    <Thumbnail
                      key={p.pageNumber}
                      api={api}
                      page={p.pageNumber}
                    />
                  ))}
                </aside>,
                shelf,
              )
            : null
        }
        emptyState={props.emptyState ?? <p>Wybierz dokument PDF.</p>}
      />
      {pages.map((p) =>
        createPortal(
          <div
            className="pdf-evidence-layer"
            role="group"
            aria-label={`Dowody na stronie ${p.dataset.pageNumber}`}
          >
            {highlights
              .filter((h) => h.page === Number(p.dataset.pageNumber))
              .map((h, index) => (
                <button
                  key={h.id}
                  type="button"
                  data-evidence-id={h.id}
                  aria-label={`Dowód ${index + 1}: ${h.label ?? h.id}`}
                  aria-pressed={!!h.active}
                  onClick={() => onHighlightClick?.(h.id)}
                  className="pdf-evidence"
                  style={
                    {
                      left: `${h.box.x * 100}%`,
                      top: `${h.box.y * 100}%`,
                      width: `${h.box.w * 100}%`,
                      height: `${h.box.h * 100}%`,
                      background: h.active
                        ? "color-mix(in srgb, var(--evidence-bg) 55%, transparent)"
                        : "transparent",
                    } as CSSProperties
                  }
                >
                  <span className="pdf-evidence-number" aria-hidden="true">
                    {index + 1}
                  </span>
                </button>
              ))}
          </div>,
          p,
          p.dataset.pageNumber,
        ),
      )}
    </div>
  );
}
