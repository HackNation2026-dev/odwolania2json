import {
  DocumentEvidenceRegions,
  type EvidenceRegion,
} from "@/components/organisms/DocumentEvidenceRegions";
import type { DocumentRecord } from "@/lib/api/schemas";
export function DocumentRegions({
  doc,
  selected,
  select,
}: {
  doc: DocumentRecord;
  selected: string;
  select: (id: string) => void;
}) {
  const groups = [...new Set(doc.fields.map((item) => item.group))];
  const regions: EvidenceRegion[] = doc.evidence.map((item) => {
    const field = doc.fields.find((field) =>
      field.evidenceIds.includes(item.id),
    );
    return {
      id: item.id,
      page: item.page,
      fieldKey: item.fieldKey,
      box: item.box,
      groupId: `G${groups.indexOf(field?.group ?? "") + 1}`,
      groupLabel: field?.label ?? item.fieldKey,
    };
  });
  return (
    <DocumentEvidenceRegions
      regions={regions}
      selected={selected}
      onSelect={select}
    />
  );
}
