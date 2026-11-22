"use client";
import { useState } from "react";
import { usePipeline, useVersions, useRestoreVersion } from "@/lib/api/hooks";
import { compareVersions } from "@/lib/api/processing";
import { Button } from "@/components/atoms/Button";

export function DocumentProcessing({ id }: { id: string }) {
  const pipeline = usePipeline(id);
  const versions = useVersions(id);
  const restore = useRestoreVersion();
  const [before, setBefore] = useState(1);
  const [after, setAfter] = useState(3);
  const a = versions.data?.results.find((v) => v.version === before);
  const b = versions.data?.results.find((v) => v.version === after);
  return (
    <div className="my-3 space-y-3 text-sm">
      <details className="rounded border border-control p-3">
        <summary className="min-h-11 cursor-pointer py-3">
          Przebieg przetwarzania
        </summary>
        {pipeline.isPending ? (
          <p role="status">Wczytywanie przebiegu…</p>
        ) : pipeline.isError ? (
          <p role="alert">
            Nie udało się odczytać przebiegu.{" "}
            <Button onClick={() => pipeline.refetch()}>Ponów</Button>
          </p>
        ) : !pipeline.data.stages.length ? (
          <p>Brak etapów.</p>
        ) : (
          <ol aria-live="polite" className="space-y-3">
            {pipeline.data.stages.map((s) => (
              <li key={s.id}>
                <strong>
                  {s.id} · {s.name}
                </strong>
                <p>
                  {s.state} ·{" "}
                  {s.durationMs === null
                    ? "Czas nieustalony"
                    : `${s.durationMs} ms`}{" "}
                  {s.errorCode}
                </p>
                {s.counts && (
                  <p>
                    {s.counts.pages !== undefined && (
                      <>
                        Strony: {s.counts.pages} · Wymagające OCR:{" "}
                        {s.counts.ocrPages}.{" "}
                      </>
                    )}
                    {s.counts.className} {s.counts.routerSignals?.join("; ")}
                    {s.counts.filled !== undefined && (
                      <>
                        Wypełnione: {s.counts.filled}, puste: {s.counts.empty},
                        dowody: {s.counts.evidence}.
                      </>
                    )}
                  </p>
                )}
              </li>
            ))}
          </ol>
        )}
      </details>
      <details className="rounded border border-control p-3">
        <summary className="min-h-11 cursor-pointer py-3">
          Historia i porównanie wersji
        </summary>
        {versions.isPending ? (
          <p role="status">Wczytywanie wersji…</p>
        ) : versions.isError ? (
          <p role="alert">
            Nie udało się odczytać wersji.{" "}
            <Button onClick={() => versions.refetch()}>Ponów</Button>
          </p>
        ) : (
          <>
            <h2 className="font-semibold">Wersje dokumentu</h2>
            {versions.data.documents.map((v) => (
              <p key={v.version}>
                v{v.version} · {v.fileName} · {v.sha256.slice(0, 8)}
              </p>
            ))}
            <h2 className="mt-3 font-semibold">Wersje wyniku</h2>
            {versions.data.results.map((v) => (
              <p key={v.version}>
                v{v.version} · {v.kind}{" "}
                <Button
                  className="min-h-11"
                  variant="ghost"
                  disabled={restore.isPending || v.json === null}
                  onClick={() => restore.mutate({ id, version: v.version })}
                >
                  Przywróć v{v.version} jako nową wersję
                </Button>
              </p>
            ))}
            <div className="flex flex-wrap gap-3">
              {(["before", "after"] as const).map((side) => (
                <label key={side}>
                  {side === "before" ? "Wersja przed" : "Wersja po"}
                  <select
                    className="ml-2 min-h-11 border border-control bg-surface"
                    value={side === "before" ? before : after}
                    onChange={(e) =>
                      (side === "before" ? setBefore : setAfter)(
                        Number(e.target.value),
                      )
                    }
                  >
                    {versions.data.results.map((v) => (
                      <option key={v.version} value={v.version}>
                        v{v.version}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
            {a && b ? (
              compareVersions(a, b).map((d) => (
                <p key={d.key} className="my-2 break-all">
                  <code>{d.key}</code> · Było: {String(d.before)} · Jest:{" "}
                  {String(d.after)}
                </p>
              ))
            ) : (
              <p>Wybierz dwie dostępne wersje.</p>
            )}
            {restore.isError && (
              <p role="alert">Nie udało się przywrócić wersji.</p>
            )}
            {restore.isSuccess && (
              <p role="status">Utworzono nową wersję wyniku.</p>
            )}
          </>
        )}
      </details>
    </div>
  );
}
