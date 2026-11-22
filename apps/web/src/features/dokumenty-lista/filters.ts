import {
  documentStatus,
  type DocumentRecord,
  type DocumentStatus,
} from "@/lib/api/schemas";

export type View = "galeria" | "tabela";
export const sorts = [
  "newest",
  "oldest",
  "name",
  "status",
  "name-desc",
  "missing",
] as const;
export type Filters = {
  q: string;
  statuses: DocumentStatus[];
  klasa: string;
  sort: (typeof sorts)[number];
  widok?: View;
  source: string;
  codes: string[];
  attention: boolean;
};
export const emptyFilters: Filters = {
  q: "",
  statuses: [],
  klasa: "",
  sort: "status",
  source: "",
  codes: [],
  attention: false,
};
export function parseFilters(params: URLSearchParams): Filters {
  const statuses = params
    .getAll("status")
    .flatMap((v) => v.split(","))
    .filter((v): v is DocumentStatus => documentStatus.safeParse(v).success);
  const sort = params.get("sort");
  const widok = params.get("widok");
  return {
    q: params.get("q") ?? "",
    statuses: [...new Set(statuses)],
    klasa: params.get("klasa") ?? "",
    sort: sorts.find((s) => s === sort) ?? "status",
    widok: widok === "galeria" || widok === "tabela" ? widok : undefined,
    source: ["pdf", "ocr"].includes(params.get("source") ?? "")
      ? params.get("source")!
      : "",
    codes: [...new Set(params.getAll("kod"))],
    attention: params.get("uwaga") === "1",
  };
}
export function serializeFilters(filters: Filters): URLSearchParams {
  const p = new URLSearchParams();
  if (filters.q) p.set("q", filters.q);
  for (const s of filters.statuses) p.append("status", s);
  if (filters.klasa) p.set("klasa", filters.klasa);
  if (filters.sort !== "status") p.set("sort", filters.sort);
  if (filters.widok) p.set("widok", filters.widok);
  if (filters.source) p.set("source", filters.source);
  for (const c of filters.codes) p.append("kod", c);
  if (filters.attention) p.set("uwaga", "1");
  return p;
}
export const needsAttention = (d: DocumentRecord) =>
  ["partial", "error", "ambiguous", "multi"].includes(d.status);
export const documentCodes = (d: DocumentRecord) => [
  ...d.codes,
  ...d.fields.flatMap(f => f.gap?.codes ?? []),
  ...(d.errorCode ? [d.errorCode] : []),
];
export function filterDocuments(
  documents: DocumentRecord[],
  f: Filters,
): DocumentRecord[] {
  const statusOrder: DocumentStatus[] = [
    "error",
    "ambiguous",
    "multi",
    "partial",
    "running",
    "foreign",
    "full",
  ];
  return documents
    .filter(
      (d) =>
        d.fileName
          .toLocaleLowerCase("pl")
          .includes(f.q.toLocaleLowerCase("pl")) &&
        (!f.statuses.length || f.statuses.includes(d.status)) &&
        (!f.klasa || d.classId === f.klasa) &&
        (!f.source || d.evidence.some((e) => e.source === f.source)) &&
        (!f.codes.length ||
          f.codes.some((c) => documentCodes(d).includes(c))) &&
        (!f.attention || needsAttention(d)),
    )
    .sort((a, b) => {
      const order =
        f.sort === "name"
          ? a.fileName.localeCompare(b.fileName, "pl")
          : f.sort === "name-desc"
            ? b.fileName.localeCompare(a.fileName, "pl")
            : f.sort === "oldest"
              ? a.uploadedAt.localeCompare(b.uploadedAt)
              : f.sort === "status"
                ? statusOrder.indexOf(a.status) - statusOrder.indexOf(b.status)
                : f.sort === "missing"
                  ? b.fields.filter((v) => v.value === null).length -
                    a.fields.filter((v) => v.value === null).length
                  : b.uploadedAt.localeCompare(a.uploadedAt);
      return order || a.id.localeCompare(b.id, "pl", { numeric: true });
    });
}
