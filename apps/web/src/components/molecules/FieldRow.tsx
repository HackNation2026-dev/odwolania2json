"use client";
import type { ReactNode } from "react";
import { Button } from "@/components/atoms";
export type FieldRowProps = {
  label: string;
  fieldKey: string;
  value: ReactNode;
  state: "ok" | "missing" | "computed" | "corrected";
  active?: boolean;
  onSelect?: () => void;
  onEdit?: () => void;
  children?: ReactNode;
};
const states = {
  ok: "↙ Z dokumentu",
  missing: "— Brak (null)",
  computed: "ƒ Wyliczone",
  corrected: "✓ Poprawione",
};
export function FieldRow({
  label,
  fieldKey,
  value,
  state,
  active = false,
  onSelect,
  onEdit,
  children,
}: FieldRowProps) {
  return (
    <article
      className={`min-w-0 space-y-2 rounded-lg border p-3 ${active ? "border-primary bg-subtle" : "border-border bg-surface"}`}
    >
      <div className="flex flex-wrap justify-between gap-2">
        <h3 className="text-sm font-semibold">
          {label} <code className="font-normal text-muted">{fieldKey}</code>
        </h3>
        <span className="text-xs">{states[state]}</span>
      </div>
      <p className="break-words">{value ?? "brak (null)"}</p>
      {children}
      <div className="flex flex-wrap gap-2">
        {onSelect && (
          <Button variant="ghost" aria-pressed={active} onClick={onSelect}>
            Pokaż dowód: {label}
          </Button>
        )}
        {onEdit && (
          <Button variant="ghost" onClick={onEdit}>
            Edytuj {label}
          </Button>
        )}
      </div>
    </article>
  );
}
