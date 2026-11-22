/** Prefiks Next jest wbudowywany także przy eksporcie statycznym. Bez zależności od głębokości trasy. */
export function pdfAsset(path: string) {
  return `${process.env.__NEXT_ROUTER_BASEPATH ?? ""}/${path.replace(/^\//, "")}`;
}
