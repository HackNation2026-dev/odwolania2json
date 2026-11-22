"use client";

import { useState } from "react";
import { Input, Select } from "@/components/atoms";
import { Button } from "@/components/atoms/Button";
import { statusMeta } from "@/components/atoms/StatusBadge";
import {
  documentStatus,
  type DocumentClass,
  type DocumentRecord,
} from "@/lib/api/schemas";
import {
  documentCodes,
  emptyFilters,
  needsAttention,
  type Filters,
} from "./filters";

const control =
  "min-h-11! py-0! w-auto! max-w-full rounded-md border border-control bg-surface px-3 text-sm";
export function FilterBar({
  filters,
  onChange,
  documents,
  classes,
  shown,
  size,
  onSize,
}: {
  filters: Filters;
  onChange: (f: Filters) => void;
  documents: DocumentRecord[];
  classes: DocumentClass[];
  shown: number;
  size?: string;
  onSize?: (size: string) => void;
}) {
  const [draft, setDraft] = useState(filters.statuses);
  const codes = [...new Set(documents.flatMap(documentCodes))];
  return (
    <section
      aria-label="Filtry dokumentów"
      className="rounded-lg bg-subtle p-4"
    >
      <div className="flex flex-wrap gap-3">
        <label className="min-w-0 flex-1 basis-64">
          <span className="sr-only">Szukaj po nazwie pliku</span>
          <Input
            type="search"
            value={filters.q}
            onChange={(e) => onChange({ ...filters, q: e.target.value })}
            placeholder="Szukaj po nazwie pliku…"
            className={`${control} w-full!`}
          />
        </label>
        <label className="flex min-w-0 max-w-full flex-wrap items-center gap-2 text-sm">
          Sortuj:
          <Select
            aria-label="Sortowanie"
            value={filters.sort}
            onChange={(e) =>
              onChange({ ...filters, sort: e.target.value as Filters["sort"] })
            }
            className={`${control} min-w-0`}
          >
            <option value="newest">Data dodania (najnowsze)</option>
            <option value="oldest">Data dodania (najstarsze)</option>
            <option value="name">Nazwa pliku A–Z</option>
            <option value="name-desc">Nazwa pliku Z–A</option>
            <option value="status">Wymaga uwagi najpierw / Status</option>
            <option value="missing">Liczba braków (najwięcej)</option>
          </Select>
        </label>
        {onSize && (
          <div
            className="flex gap-1"
            role="group"
            aria-label="Rozmiar kafelków"
          >
            {["S", "M", "L"].map((s) => (
              <Button
                key={s}
                className="min-h-11 min-w-11 px-3"
                variant={size === s ? "primary" : "secondary"}
                aria-pressed={size === s}
                onClick={() => onSize(s)}
              >
                {s}
              </Button>
            ))}
          </div>
        )}
      </div>
      <div className="mt-3 flex flex-wrap items-start gap-2">
        <details
          className="relative"
          onToggle={(e) => {
            if (e.currentTarget.open) setDraft(filters.statuses);
          }}
        >
          <summary className={`${control} flex cursor-pointer items-center`}>
            Status{" "}
            {filters.statuses.length ? `(${filters.statuses.length})` : ""} ▾
          </summary>
          <div className="absolute left-0 z-20 mt-2 w-64 max-w-[calc(100vw-4rem)] rounded-lg border border-control bg-surface p-3 shadow-lg">
            <fieldset>
              <legend className="text-sm font-medium">Status dokumentu</legend>
              {documentStatus.options.map((s) => (
                <label
                  key={s}
                  className="flex min-h-11 items-center gap-2 text-sm"
                >
                  <input
                    type="checkbox"
                    checked={draft.includes(s)}
                    onChange={(e) =>
                      setDraft(
                        e.target.checked
                          ? [...draft, s]
                          : draft.filter((v) => v !== s),
                      )
                    }
                  />
                  <span aria-hidden>{statusMeta[s].icon}</span>
                  {statusMeta[s].label} (
                  {documents.filter((d) => d.status === s).length})
                </label>
              ))}
            </fieldset>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                className="min-h-11"
                onClick={() => {
                  setDraft([]);
                  onChange({ ...filters, statuses: [] });
                }}
              >
                Wyczyść
              </Button>
              <Button
                className="min-h-11"
                onClick={(e) => {
                  onChange({ ...filters, statuses: draft });
                  e.currentTarget.closest("details")?.removeAttribute("open");
                }}
              >
                Zastosuj ({draft.length})
              </Button>
            </div>
          </div>
        </details>
        <Select
          aria-label="Klasa dokumentu"
          value={filters.klasa}
          onChange={(e) => onChange({ ...filters, klasa: e.target.value })}
          className={control}
        >
          <option value="">Klasa dokumentu</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        <Select
          aria-label="Źródło tekstu"
          value={filters.source}
          onChange={(e) => onChange({ ...filters, source: e.target.value })}
          className={control}
        >
          <option value="">Źródło tekstu</option>
          <option value="pdf">Tekst PDF</option>
          <option value="ocr">OCR</option>
        </Select>
        <details className="relative">
          <summary className={`${control} flex cursor-pointer items-center`}>
            Kody odstępstw{" "}
            {filters.codes.length ? `(${filters.codes.length})` : ""} ▾
          </summary>
          <fieldset className="absolute left-0 z-20 mt-2 w-64 max-w-[calc(100vw-4rem)] rounded-lg border border-control bg-surface p-3">
            <legend className="sr-only">Kody odstępstw</legend>
            {codes.map((c) => (
              <label
                key={c}
                className="flex min-h-11 items-center gap-2 break-all text-sm"
              >
                <input
                  type="checkbox"
                  checked={filters.codes.includes(c)}
                  onChange={(e) =>
                    onChange({
                      ...filters,
                      codes: e.target.checked
                        ? [...filters.codes, c]
                        : filters.codes.filter((v) => v !== c),
                    })
                  }
                />
                {c}
              </label>
            ))}
            <Button
              variant="secondary"
              className="min-h-11"
              onClick={() => onChange({ ...filters, codes: [] })}
            >
              Wyczyść kody
            </Button>
          </fieldset>
        </details>
        <Button
          variant={filters.attention ? "primary" : "secondary"}
          className="min-h-11"
          aria-pressed={filters.attention}
          onClick={() =>
            onChange({ ...filters, attention: !filters.attention })
          }
        >
          Wymaga uwagi ({documents.filter(needsAttention).length})
        </Button>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted sm:ml-auto">
          <span>
            Pokazano {shown} z {documents.length}
          </span>
          <Button
            variant="ghost"
            className="min-h-11 text-xs"
            onClick={() => onChange({ ...emptyFilters, widok: filters.widok })}
          >
            Wyczyść filtry
          </Button>
        </div>
      </div>
    </section>
  );
}
