"use client";
import Link from "next/link";
import { Button, Input, Card } from "@/components/atoms";
import { identity, type useAddDocumentsState } from "./useAddDocumentsState";
const card = "min-w-0 rounded-md! border border-border bg-surface p-5!";
export function SelectedFilesPanel({
  state,
}: {
  state: ReturnType<typeof useAddDocumentsState>;
}) {
  const {
    key,
    classes,
    add,
    files,
    setFiles,
    messages,
    submittedIds,
    caseName,
    setCaseName,
    locked,
    analyze,
    clear,
  } = state;
  return (
    <Card
      as="section"
      padding="none"
      className={card}
      aria-labelledby="selected-files"
    >
      <h2 id="selected-files" className="mb-3 text-lg font-semibold">
        Wybrane pliki ({files.length})
      </h2>
      <label htmlFor="case-name" className="text-sm">
        Nazwa sprawy
      </label>
      <Input
        id="case-name"
        value={caseName}
        disabled={locked}
        onChange={(event) => setCaseName(event.target.value)}
        placeholder="Nowa paczka dokumentów"
        className="mt-1 min-h-11 md:min-h-11 py-0 w-full rounded-md border border-control bg-surface px-3 text-sm"
      />
      {files.length === 0 ? (
        <p className="my-4 text-sm text-muted">
          Wybierz pliki PDF, aby rozpocząć.
        </p>
      ) : (
        <ul className="my-3 space-y-2">
          {files.map((file) => (
            <li
              key={identity(file)}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-subtle p-3"
            >
              <div className="min-w-0">
                <p className="break-all text-sm">▤ {file.name}</p>
                <p className="text-xs text-muted">
                  {Math.ceil(file.sizeKb)} KB
                </p>
              </div>
              <Button
                className="min-h-11"
                variant="ghost"
                aria-label={`Usuń ${file.name}`}
                disabled={locked || submittedIds.length > 0}
                onClick={() =>
                  setFiles(files.filter((f) => identity(f) !== identity(file)))
                }
              >
                × Usuń
              </Button>
            </li>
          ))}
        </ul>
      )}
      <div role="status" aria-live="polite">
        {messages.map((message) => (
          <p
            key={message}
            className="my-2 break-words rounded-md bg-[var(--partial-bg)] p-3 text-sm text-[var(--partial-fg)]"
          >
            ⚠ {message}
          </p>
        ))}
      </div>
      {key.isPending && (
        <p role="status" className="my-3 text-sm">
          Sprawdzanie konfiguracji klucza…
        </p>
      )}
      {key.data?.configured === false && (
        <p className="my-3 rounded-md bg-[var(--partial-bg)] p-3 text-sm text-[var(--partial-fg)]">
          ⚠ Brak klucza API modelu.{" "}
          <Link
            href="/klucz"
            className="inline-flex min-h-11 items-center underline"
          >
            Skonfiguruj klucz
          </Link>
        </p>
      )}
      {key.isError && (
        <p role="alert" className="my-3">
          Nie udało się sprawdzić klucza.{" "}
          <Button
            className="min-h-11"
            variant="secondary"
            onClick={() => void key.refetch()}
          >
            Spróbuj ponownie
          </Button>
        </p>
      )}
      {add.isError && (
        <p role="alert" className="my-3 text-[var(--error-fg)]">
          Nie udało się wysłać. Spróbuj ponownie. {add.error.message}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <Button
          className="min-h-11"
          disabled={
            !classes.data?.some((c) => c.id !== "obcy") ||
            !key.data?.configured ||
            files.length === 0 ||
            locked ||
            submittedIds.length > 0
          }
          onClick={analyze}
        >
          {add.isPending ? "Wysyłanie…" : "Uruchom analizę"}
        </Button>
        <Button
          className="min-h-11"
          variant="secondary"
          disabled={locked}
          onClick={clear}
        >
          Wyczyść
        </Button>
      </div>
    </Card>
  );
}
