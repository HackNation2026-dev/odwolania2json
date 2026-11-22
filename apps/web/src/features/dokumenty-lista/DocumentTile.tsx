import {
  DocumentResultTile,
  PdfThumb,
} from "@/components/molecules/DocumentResultTile";
import type { DocumentRecord } from "@/lib/api/schemas";
import { documentCodes } from "./filters";
export { PdfThumb };
export function DocumentTile({ document }: { document: DocumentRecord }) {
  return (
    <DocumentResultTile document={document} codes={documentCodes(document)} />
  );
}
