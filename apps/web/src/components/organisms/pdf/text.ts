import type { PdfSource } from "react-web-pdf-editor";
import { pdfAsset } from "./assets";
export async function extractPageText(
  file: PdfSource,
  page: number,
): Promise<string> {
  const { getDocument, GlobalWorkerOptions } = await import(
    "pdfjs-dist/legacy/build/pdf.mjs"
  );
  GlobalWorkerOptions.workerSrc = pdfAsset("pdf/pdf.worker.min.mjs");
  const source =
    file instanceof Blob
      ? new Uint8Array(await file.arrayBuffer())
      : file instanceof URL
        ? file.href
        : file;
  const task = getDocument(
    typeof source === "string"
      ? { url: source }
      : { data: source instanceof Uint8Array ? source.slice() : source },
  );
  try {
    const pdf = await task.promise;
    const content = await (await pdf.getPage(page)).getTextContent();
    return content.items
      .map((item) =>
        "str" in item ? item.str + (item.hasEOL ? "\n" : " ") : "",
      )
      .join("")
      .trim();
  } finally {
    await task.destroy();
  }
}
