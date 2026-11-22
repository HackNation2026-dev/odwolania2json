import type { DocumentRecord } from "@/lib/api/schemas";
import s from "./dokument.module.css";

export function DocumentGeometryStyles({ doc }: { doc: DocumentRecord }) {
  const groups = [...new Set(doc.fields.map((field) => field.group))];
  const colors = [
    "var(--evidence-border)",
    "color-mix(in srgb, var(--running-fg) 35%, var(--evidence-border))",
    "color-mix(in srgb, var(--ambiguous-fg) 35%, var(--evidence-border))",
  ];
  const patterns = ["solid", "dashed", "dotted"];
  const rules = doc.evidence.flatMap((item) => {
    if (!item.box || !/^[a-zA-Z0-9_-]+$/.test(item.id)) return [];
    const field = doc.fields.find((field) =>
      field.evidenceIds.includes(item.id),
    );
    const group = groups.indexOf(field?.group ?? "");
    const selector = `.${s.pdf} [data-evidence-id="${item.id}"]`;
    return [
      `${selector} { --document-region-color: ${colors[(group + 3) % 3]}; border-color:var(--document-region-color); border-style:${patterns[(group + 3) % 3]}; }`,
      `${selector}[aria-pressed="true"] { border-color:var(--evidence-border); border-style:solid; }`,
      `${selector} .pdf-evidence-number { background:var(--document-region-color); }`,
      `${selector} .pdf-evidence-number::before { content:"G${group + 1} · "; }`,
    ];
  });
  return <style>{rules.join("\n")}</style>;
}
