"use client";

import Link from "next/link";
import { SystemReadiness } from "@/features/dodawanie/SystemReadiness";
import { Dialog } from "@/components/organisms/Dialog";
import { Banner } from "@/components/molecules/Banner";
import { Card } from "@/components/atoms";
import { useAddDocumentsState } from "./useAddDocumentsState";
import { Button } from "@/components/atoms/Button";
import { DropZone } from "@/components/molecules/DropZone";
import { SelectedFilesPanel } from "./SelectedFilesPanel";
import { RecentDocuments } from "./RecentDocuments";
import { BatchProgress } from "./BatchProgress";

const card = "min-w-0 rounded-md! border border-border bg-surface p-5!";

export function AddDocumentsView() {
  const state = useAddDocumentsState();
  const {
    key,
    classes,
    documents,
    submittedIds,
    caseName,
    submitted,
    locked,
    selectFiles,
    collision,
    resolved,
    collisionOpen,
    setCollisionOpen,
    resolveCollision,
  } = state;
  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <header>
        <h1 className="text-3xl font-semibold">Nowa analiza</h1>
        <p className="mt-3 max-w-2xl text-sm text-muted">
          Wgraj dokumenty z akt sprawy odwoławczej. Rozpoznamy rodzaj każdego
          dokumentu po treści i wyodrębnimy dane do JSON.
        </p>
      </header>
      <SystemReadiness />
      {classes.data && !classes.data.some((c) => c.id !== "obcy") && (
        <Banner tone="error" title="Błąd konfiguracji">
          Brak poprawnego zestawu klas. Analiza zablokowana.{" "}
          <Link href="/klasy" className="underline">
            Szczegóły błędu
          </Link>
        </Banner>
      )}
      <Dialog
        open={collisionOpen}
        onClose={() => {
          if (!resolved.isPending) setCollisionOpen(false);
        }}
        title="Kolizja ścieżki"
        description="Wybierz nową wersję dokumentu, osobną paczkę albo anuluj."
        actions={
          <>
            <Button
              disabled={resolved.isPending}
              onClick={() => resolveCollision("version")}
            >
              Nowa wersja dokumentu
            </Button>
            <Button
              variant="secondary"
              disabled={resolved.isPending}
              onClick={() => resolveCollision("package")}
            >
              Osobna paczka
            </Button>
            <Button
              variant="secondary"
              disabled={resolved.isPending}
              onClick={() => setCollisionOpen(false)}
            >
              Anuluj
            </Button>
          </>
        }
      >
        <ul className="space-y-2 break-all text-sm">
          {collision.data?.map((item) => (
            <li key={item.incomingIndex}>{item.path} · kolizja ścieżki</li>
          ))}
        </ul>
        <p className="mt-3 text-sm">
          Bez automatycznego (2) i bez nadpisania. Decyzja dotyczy kolidujących ścieżek z tej listy. Scenariusz syntetyczny — przesyłane są metadane PDF.
        </p>
        {resolved.isError && (
          <Banner tone="error">{resolved.error.message}</Banner>
        )}
      </Dialog>
      {collision.isError && (
        <Banner tone="error">
          Nie udało się sprawdzić kolizji ścieżek. Spróbuj ponownie.
        </Banner>
      )}
      <nav
        aria-label="Widoki analizy"
        className="flex flex-wrap gap-4 border-b border-border"
      >
        <span className="inline-flex min-h-11 items-center border-b-2 border-primary font-medium">
          Dodaj dokumenty
        </span>
        <Link className="inline-flex min-h-11 items-center" href="/dokumenty">
          Dodane dokumenty {documents.data && `(${documents.data.length})`}
        </Link>
      </nav>
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="min-w-0 space-y-5">
          <DropZone
            onFiles={selectFiles}
            disabled={locked || submittedIds.length > 0}
          />
          <SelectedFilesPanel state={state} />
          <Card as="section" padding="none" className={card}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-semibold">Gotowość i modele</h2>
              <Button
                className="min-h-11"
                variant="secondary"
                onClick={() => {
                  void key.refetch();
                  void classes.refetch();
                }}
              >
                Sprawdź ponownie
              </Button>
            </div>
            <p className="my-3 text-xs text-muted">
              Gotowość nie gwarantuje powodzenia kolejnego żądania.
            </p>
            <p className="mb-2 rounded-md bg-subtle p-3 text-sm">
              Model i OCR: nie sprawdzono gotowości. Metadane modelu, licencji i
              lokalizacji nie zostały udostępnione.
            </p>
            <p className="mb-2 rounded-md bg-subtle p-3 text-sm">
              Konfiguracja klas:{" "}
              {classes.isPending
                ? "ładowanie…"
                : classes.isError
                  ? "nie udało się pobrać"
                  : `${classes.data.filter((c) => c.id !== "obcy").length} klasy`}
              . Wersja zestawu: {classes.data?.[0]?.version ?? "nie pobrano"}.
              Limit pliku: nie podano.
            </p>
            <Link
              className="inline-flex min-h-11 items-center text-sm underline"
              href="/jak-to-dziala"
            >
              Pokaż wszystkie modele, licencje i lokalizację ›
            </Link>
          </Card>
          <details open className={card}>
            <summary className="min-h-11 cursor-pointer font-semibold">
              Jak grupujemy pliki
            </summary>
            <p className="text-sm">
              Pliki wybrane razem tworzą jedną paczkę roboczą. Każdy dokument
              analizujemy niezależnie; nie uzupełniamy danych z innych plików.
            </p>
            <p className="mt-2 text-sm">
              Nazwa pliku nie wpływa na rozpoznanie rodzaju dokumentu.
            </p>
          </details>
        </div>
        <div className="min-w-0 space-y-5">
          {submittedIds.length > 0 && (
            <BatchProgress
              documents={submitted}
              total={submittedIds.length}
              name={caseName || "Nowa paczka dokumentów"}
              refreshError={documents.isError}
              onRefresh={() => void documents.refetch()}
            />
          )}
          <RecentDocuments state={state} />
        </div>
      </div>
    </div>
  );
}
