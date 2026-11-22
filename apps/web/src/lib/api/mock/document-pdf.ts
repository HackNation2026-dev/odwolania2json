import appeal from "../../../../public/demo-pdf/odwolanie.json";
import power from "../../../../public/demo-pdf/pelnomocnictwo.json";
import transfer from "../../../../public/demo-pdf/przelew.json";
import scan from "../../../../public/demo-pdf/skan-odwolanie.json";
import type { DocumentRecord, Evidence, Field } from "../schemas";

export function documentPdfFile(
  doc: Pick<DocumentRecord, "id" | "classId" | "fileName">,
) {
  const name =
    doc.id === "doc-4" || doc.fileName === "skan-odwolanie.pdf"
      ? "skan-odwolanie"
      : doc.classId === "przelew"
        ? "przelew"
        : doc.classId === "pelnomocnictwo"
          ? "pelnomocnictwo"
          : "odwolanie";
  return `/demo-pdf/${name}.pdf`;
}

// Skrócone PDF-y nie zawierają wszystkich pól kontraktu. Nie tworzymy dla nich fikcyjnych ramek.
export function locateDocumentEvidence(
  evidence: Evidence[],
  fields: Field[],
  classId: DocumentRecord["classId"],
  scanned: boolean,
): Evidence[] {
  const geometry = scanned
    ? scan
    : classId === "przelew"
      ? transfer
      : classId === "pelnomocnictwo"
        ? power
        : appeal;
  return evidence.map((item) => {
    const field = fields.find((field) => field.key === item.fieldKey);
    const value = typeof field?.value === "string" ? field.value : "";
    const hit =
      value.length > 3
        ? geometry.find((region) => region.label.includes(value))
        : undefined;
    if (!hit) return { ...item, box: undefined, bbox: [], words: [] };
    const { x, y, w, h } = hit.box;
    return {
      ...item,
      page: hit.page,
      quote: hit.label,
      box: hit.box,
      bbox: [[x * 595.28, y * 841.89, (x + w) * 595.28, (y + h) * 841.89]],
      words: [hit.id],
    };
  });
}
