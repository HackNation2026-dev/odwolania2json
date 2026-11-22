"use client";
import type { ReactNode } from "react";
import { Button } from "@/components/atoms";
import { SearchBox } from "@/components/molecules/SearchBox";
export type FilterBarProps = {
  query: string;
  onQueryChange: (query: string) => void;
  children?: ReactNode;
  onReset?: () => void;
  shown?: number;
  total?: number;
  searchLabel?: string;
};
export function FilterBar({
  query,
  onQueryChange,
  children,
  onReset,
  shown,
  total,
  searchLabel = "Szukaj po nazwie pliku",
}: FilterBarProps) {
  return (
    <section
      aria-label="Filtry dokumentów"
      className="space-y-3 rounded-lg bg-subtle p-4"
    >
      <SearchBox
        label={searchLabel}
        placeholder={`${searchLabel}…`}
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        onClear={query ? () => onQueryChange("") : undefined}
      />
      <div className="flex flex-wrap items-center gap-2">
        {children}
        {shown !== undefined && total !== undefined && (
          <span role="status" className="text-xs text-muted">
            Pokazano {shown} z {total}
          </span>
        )}
        {onReset && (
          <Button variant="ghost" onClick={onReset}>
            Wyczyść filtry
          </Button>
        )}
      </div>
    </section>
  );
}
