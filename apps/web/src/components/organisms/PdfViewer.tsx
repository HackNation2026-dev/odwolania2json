"use client";
import dynamic from "next/dynamic";
import type { ReactNode } from "react";
import type { PdfSource } from "react-web-pdf-editor";
export type { PdfSource } from "react-web-pdf-editor";
export type PdfHighlight = {
  id: string;
  page: number;
  box: { x: number; y: number; w: number; h: number };
  label?: string;
  active?: boolean;
};
export type PdfViewerProps = {
  file: PdfSource | string;
  page?: number;
  onPageChange?: (page: number) => void;
  scale?: number;
  onScaleChange?: (scale: number) => void;
  highlights?: PdfHighlight[];
  onHighlightClick?: (id: string) => void;
  onLoadSuccess?: (info: { numPages: number }) => void;
  onLoadError?: (error: Error) => void;
  emptyState?: ReactNode;
  className?: string;
};
const Client = dynamic(() => import("./pdf/PdfViewerClient"), {
  ssr: false,
  loading: () => <p role="status">Ładowanie podglądu PDF…</p>,
});
export function PdfViewer(props: PdfViewerProps) {
  return <Client {...props} />;
}
export { extractPageText } from "./pdf/text";
