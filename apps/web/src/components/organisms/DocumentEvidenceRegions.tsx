"use client";
import { useState } from "react";
import { Badge, Button } from "@/components/atoms";
import { Banner, SegmentedControl } from "@/components/molecules";

export type EvidenceRegion = {
  id: string;
  page: number;
  fieldKey: string;
  groupId: string;
  groupLabel: string;
  box?: { x: number; y: number; w: number; h: number };
};
export function regionsOverlap(a: EvidenceRegion, b: EvidenceRegion) {
  if (!a.box || !b.box || a.page !== b.page) return false;
  return (
    a.box.x < b.box.x + b.box.w &&
    b.box.x < a.box.x + a.box.w &&
    a.box.y < b.box.y + b.box.h &&
    b.box.y < a.box.y + a.box.h
  );
}

export function DocumentEvidenceRegions({
  regions,
  selected,
  onSelect,
}: {
  regions: EvidenceRegion[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const [mode, setMode] = useState("fields");
  const active = regions.find((item) => item.id === selected);
  if (!active) return null;
  const related = regions.filter((item) =>
    mode === "groups"
      ? item.groupId === active.groupId
      : item.fieldKey === active.fieldKey,
  );
  const index = related.findIndex((item) => item.id === selected);
  const collision = regions.some((a) =>
    regions.some((b) => a.groupId !== b.groupId && regionsOverlap(a, b)),
  );
  return (
    <div className="mb-3 space-y-2 text-xs">
      <SegmentedControl
        label="Oznaczenia"
        value={mode}
        onChange={setMode}
        options={[
          { value: "fields", label: "Pola" },
          { value: "groups", label: "Grupy" },
        ]}
      />
      <Badge
        tone={
          active.groupId === "G2"
            ? "running"
            : active.groupId === "G3"
              ? "ambiguous"
              : "partial"
        }
      >
        {active.groupId}
      </Badge>
      {collision && (
        <Banner
          tone="warning"
          title="Grupy nakładają się. Pokazano oznaczenia pól."
        />
      )}
      <p role="status">
        {active.groupId} · {active.groupLabel} · obszar {index + 1} z{" "}
        {related.length}
      </p>
      {related.length > 1 && (
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            onClick={() =>
              onSelect(
                related[(index - 1 + related.length) % related.length]!.id,
              )
            }
          >
            Poprzedni obszar
          </Button>
          <Button
            variant="secondary"
            onClick={() => onSelect(related[(index + 1) % related.length]!.id)}
          >
            Następny obszar
          </Button>
        </div>
      )}
      <details>
        <summary className="flex min-h-11 cursor-pointer items-center">
          Legenda obszarów i powiązania pól
        </summary>
        <ul>
          {regions
            .filter((item) => item.groupId === active.groupId)
            .map((item, number) => (
              <li key={item.id}>
                <Button
                  variant="ghost"
                  aria-pressed={item.id === selected}
                  onClick={() => onSelect(item.id)}
                >
                  {item.groupId} · {number + 1} · str. {item.page} · {item.id} ·{" "}
                  {item.fieldKey} {item.box ? "— obrys" : "— bez obrysu"}
                </Button>
              </li>
            ))}
        </ul>
      </details>
    </div>
  );
}
