"use client";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { FieldRow } from "@/components/molecules/FieldRow";
import { useUpdateField } from "@/lib/api/hooks";
import type { Evidence, Field } from "@/lib/api/schemas";
import { parseFieldValue, partialReasons } from "./format";
import s from "./dokument.module.css";

export function DocumentField({
  id,
  field,
  evidence,
  active,
  onSelect,
}: {
  id: string;
  field: Field;
  evidence: Evidence[];
  active: boolean;
  onSelect: () => void;
}) {
  const update = useUpdateField();
  const [editing, setEditing] = useState(false);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const beginEditing = () => {
    setInput(field.value === null ? "" : String(field.value));
    setError("");
    setEditing(true);
  };
  const states = {
    ok: "ok",
    brak: "missing",
    wyliczone: "computed",
    poprawione: "corrected",
  } as const;
  async function save(event: React.FormEvent) {
    event.preventDefault();
    try {
      setError("");
      await update.mutateAsync({
        id,
        key: field.key,
        value: parseFieldValue(field, input),
      });
      setEditing(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się zapisać pola.");
    }
  }
  return (
    <article
      id={`field-${field.key}`}
      className={`${s.libraryField} ${active ? s.activeField : ""}`}
    >
      <FieldRow
        label={field.label}
        fieldKey={field.key}
        value={field.value === null ? "brak (null)" : String(field.value)}
        state={states[field.state]}
        active={active}
        onSelect={onSelect}
        onEdit={
          !editing &&
          !["object", "array"].includes(field.type) &&
          field.key !== "OdwolanieKIO.czynnosc_opis"
            ? beginEditing
            : undefined
        }
      >
        {field.gap && (
          <p className="text-xs text-muted">
            {partialReasons[field.gap.reason].label}: {field.gap.description}{" "}
            {field.gap.codes.join(" · ")}
          </p>
        )}
        {evidence.length
          ? evidence.map((e) => (
              <p key={e.id} className="mt-1 text-xs text-muted">
                Str. {e.page} · {e.quote} · Źródło:{" "}
                {e.source === "ocr" ? "OCR" : "tekst PDF"} · Metoda:{" "}
                {e.method === "ai" ? "model" : "reguła"} · Pewność:{" "}
                {e.confidence === null
                  ? "Nie oceniono"
                  : `${Math.round(e.confidence * 100)}%`}
                {e.rule && (
                  <>
                    {" "}
                    · Reguła: {e.rule} · Przesłanki: {e.premiseIds.join(", ")}
                  </>
                )}
              </p>
            ))
          : !field.gap && (
              <p className="text-xs text-muted">
                Brak przypisanego dowodu. Sprawdź tekst dokumentu.
              </p>
            )}
        <div className={s.fieldActions}>
          {evidence.length > 0 && (
            <>
              <Link
                href={`/dokumenty/${id}?tab=dokument`}
                onClick={onSelect}
                className={`${s.rowAction} inline-flex items-center md:hidden`}
              >
                Pokaż dowód
              </Link>
            </>
          )}
          {editing ? (
            <form onSubmit={save} className="mt-3 space-y-2">
              <label htmlFor={`edit-${field.key}`} className="block text-sm">
                Nowa wartość: {field.label}
              </label>
              <Input
                id={`edit-${field.key}`}
                autoFocus
                className={s.input}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                aria-invalid={!!error}
                aria-describedby={error ? `error-${field.key}` : undefined}
              />
              <p className="text-xs text-muted">
                Puste pole zapisuje null. Daty: RRRR-MM-DD.
              </p>
              {error && (
                <p role="alert" id={`error-${field.key}`}>
                  {error}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                <Button
                  className="min-h-11"
                  type="submit"
                  disabled={update.isPending}
                >
                  Zapisz
                </Button>
                <Button
                  className="min-h-11"
                  variant="secondary"
                  onClick={() => setEditing(false)}
                >
                  Anuluj
                </Button>
              </div>
            </form>
          ) : null}
        </div>
      </FieldRow>
    </article>
  );
}
