"use client";
import { useState } from "react";
import { Button } from "@/components/atoms";
import { groupLabels } from "@/lib/api/contract";
import type { DocumentRecord } from "@/lib/api/schemas";
import { DocumentField } from "./DocumentField";
import s from "./dokument.module.css";

export function DocumentFields({
  doc,
  selectedField,
  onSelectField,
}: {
  doc: DocumentRecord;
  selectedField: string | null;
  onSelectField: (key: string) => void;
}) {
  const [filter, setFilter] = useState("all");
  const id = doc.id;
  return (
    <>
      <div className={s.fieldFilters} aria-label="Filtry pól">
        {(
          [
            ["all", `Wszystkie pola (${doc.fields.length})`],
            [
              "review",
              `Do sprawdzenia (${doc.fields.filter((f) => f.gap?.reviewRequired || doc.evidence.some((e) => e.fieldKey === f.key && e.confidence !== null && e.confidence < 0.9)).length})`,
            ],
            [
              "missing",
              `Braki (${doc.fields.filter((f) => f.value === null).length})`,
            ],
          ] as const
        ).map(([value, label]) => (
          <Button
            key={value}
            className={s.filterButton}
            variant={filter === value ? "primary" : "ghost"}
            aria-pressed={filter === value}
            onClick={() => setFilter(value)}
          >
            {label}
          </Button>
        ))}
        <span className="text-xs text-muted">
          Wypełniono {doc.fields.filter((f) => f.value !== null).length} z{" "}
          {doc.fields.length} pól
        </span>
      </div>
      <section className={s.fieldGroup} aria-label="Pola dokumentu">
        {[...new Set(doc.fields.map((f) => f.group))]
          .sort((a, b) =>
            a === "ZamowieniePubliczne"
              ? -1
              : b === "ZamowieniePubliczne"
                ? 1
                : 0,
          )
          .map((group) => (
            <section
              key={group}
              className="mb-3 rounded border border-control p-2"
            >
              <h2 className={s.groupTitle}>
                {groupLabels[group] ?? group} · <code>{group}</code>
              </h2>
              {doc.fields
                .filter((f) => f.group === group)
                .filter(
                  (f) =>
                    filter === "all" ||
                    (filter === "missing"
                      ? f.value === null
                      : f.gap?.reviewRequired ||
                        doc.evidence.some(
                          (e) =>
                            e.fieldKey === f.key &&
                            e.confidence !== null &&
                            e.confidence < 0.9,
                        )),
                )
                .map((field) => (
                  <DocumentField
                    key={field.key}
                    id={id}
                    field={field}
                    active={selectedField === field.key}
                    evidence={doc.evidence.filter((e) =>
                      field.evidenceIds.includes(e.id),
                    )}
                    onSelect={() => {
                      onSelectField(field.key);
                    }}
                  />
                ))}
            </section>
          ))}
        {!doc.fields.some(
          (f) =>
            filter === "all" ||
            (filter === "missing"
              ? f.value === null
              : f.gap?.reviewRequired ||
                doc.evidence.some(
                  (e) =>
                    e.fieldKey === f.key &&
                    e.confidence !== null &&
                    e.confidence < 0.9,
                )),
        ) && <p className={s.notice}>Brak pól spełniających wybrany filtr.</p>}
      </section>
    </>
  );
}
