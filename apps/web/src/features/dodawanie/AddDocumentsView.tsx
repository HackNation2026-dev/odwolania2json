"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { DropZone, type SelectedPdf } from "@/components/molecules/DropZone";
import { BatchProgress } from "./BatchProgress";
import { useAddDocuments, useClasses, useDocuments, useKeyStatus } from "@/lib/api/hooks";

const card = "min-w-0 rounded-md border border-border bg-surface p-5";

const identity = (file: SelectedPdf) => `${file.name}:${file.sizeKb}`;

export function AddDocumentsView() {
  const key = useKeyStatus();
  const classes = useClasses();
  const documents = useDocuments();
  const add = useAddDocuments();
  const [files, setFiles] = useState<SelectedPdf[]>([]);
  const [messages, setMessages] = useState<string[]>([]);
  const [submittedIds, setSubmittedIds] = useState<string[]>([]);
  const [caseName, setCaseName] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("newest");
  const submitted = submittedIds.map(id => documents.data?.find(d => d.id === id) ?? add.data?.find(d => d.id === id)).filter(d => d !== undefined);
  const completed = submitted.filter(d => d.status !== "running").length;
  const finished = submitted.length === submittedIds.length && submittedIds.length > 0 && completed === submittedIds.length;
  const locked = add.isPending || (submittedIds.length > 0 && !finished);
  const recent = [...(documents.data ?? [])].filter(d => d.fileName.toLocaleLowerCase("pl").includes(search.toLocaleLowerCase("pl"))).sort((a, b) => sort === "name" ? a.fileName.localeCompare(b.fileName, "pl") : b.uploadedAt.localeCompare(a.uploadedAt)).slice(0, 6);

  function selectFiles(incoming: SelectedPdf[], skipped: string[]) {
    const next = [...files];
    for (const file of incoming) {
      if (next.some(existing => identity(existing) === identity(file))) skipped.push(`${file.name}: ten sam plik jest już na liście.`);
      else next.push(file);
    }
    if (!caseName && next.length > 0) setCaseName(`Sprawa z ${new Date().toLocaleString("pl-PL", { dateStyle: "short", timeStyle: "short" })}`);
    setFiles(next);
    setMessages(skipped);
  }
  function analyze() {
    if (!key.data?.configured || files.length === 0 || locked) return;
    add.mutate(files, { onSuccess: added => setSubmittedIds(added.map(d => d.id)) });
  }
  function clear() {
    setFiles([]);
    setMessages([]);
    setSubmittedIds([]);
    add.reset();
  }
  return <div className="mx-auto max-w-6xl space-y-5">
    <header><h1 className="text-3xl font-semibold">Nowa analiza</h1><p className="mt-3 max-w-2xl text-sm text-muted">Wgraj dokumenty z akt sprawy odwoławczej. Rozpoznamy rodzaj każdego dokumentu po treści i wyodrębnimy dane do JSON.</p></header>
    <nav aria-label="Widoki analizy" className="flex flex-wrap gap-4 border-b border-border"><span className="inline-flex min-h-11 items-center border-b-2 border-primary font-medium">Dodaj dokumenty</span><Link className="inline-flex min-h-11 items-center" href="/dokumenty">Dodane dokumenty {documents.data && `(${documents.data.length})`}</Link></nav>
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
      <div className="min-w-0 space-y-5">
        <DropZone onFiles={selectFiles} disabled={locked || submittedIds.length > 0} />
        <section className={card} aria-labelledby="selected-files">
          <h2 id="selected-files" className="mb-3 text-lg font-semibold">Wybrane pliki ({files.length})</h2>
          <label htmlFor="case-name" className="text-sm">Nazwa sprawy</label><input id="case-name" value={caseName} disabled={locked} onChange={event => setCaseName(event.target.value)} placeholder="Nowa paczka dokumentów" className="mt-1 min-h-11 w-full rounded-md border border-control bg-surface px-3 text-sm" />
          {files.length === 0 ? <p className="my-4 text-sm text-muted">Wybierz pliki PDF, aby rozpocząć.</p> : <ul className="my-3 space-y-2">{files.map(file => <li key={identity(file)} className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-subtle p-3"><div className="min-w-0"><p className="break-all text-sm">▤ {file.name}</p><p className="text-xs text-muted">{Math.ceil(file.sizeKb)} KB</p></div><Button className="min-h-11" variant="ghost" aria-label={`Usuń ${file.name}`} disabled={locked || submittedIds.length > 0} onClick={() => setFiles(files.filter(f => identity(f) !== identity(file)))}>× Usuń</Button></li>)}</ul>}
          <div role="status" aria-live="polite">{messages.map(message => <p key={message} className="my-2 break-words rounded-md bg-[var(--partial-bg)] p-3 text-sm text-[var(--partial-fg)]">⚠ {message}</p>)}</div>
          {key.isPending && <p role="status" className="my-3 text-sm">Sprawdzanie konfiguracji klucza…</p>}
          {key.data?.configured === false && <p className="my-3 rounded-md bg-[var(--partial-bg)] p-3 text-sm text-[var(--partial-fg)]">⚠ Brak klucza API modelu. <Link href="/klucz" className="inline-flex min-h-11 items-center underline">Skonfiguruj klucz</Link></p>}
          {key.isError && <p role="alert" className="my-3">Nie udało się sprawdzić klucza. <Button className="min-h-11" variant="secondary" onClick={() => void key.refetch()}>Spróbuj ponownie</Button></p>}
          {add.isError && <p role="alert" className="my-3 text-[var(--error-fg)]">Nie udało się wysłać. Spróbuj ponownie. {add.error.message}</p>}
          <div className="flex flex-wrap gap-2"><Button className="min-h-11" disabled={!key.data?.configured || files.length === 0 || locked || submittedIds.length > 0} onClick={analyze}>{add.isPending ? "Wysyłanie…" : "Uruchom analizę"}</Button><Button className="min-h-11" variant="secondary" disabled={locked} onClick={clear}>Wyczyść</Button></div>
        </section>
        <section className={card}><div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-semibold">Gotowość i modele</h2><Button className="min-h-11" variant="secondary" onClick={() => { void key.refetch(); void classes.refetch(); }}>Sprawdź ponownie</Button></div><p className="my-3 text-xs text-muted">Gotowość nie gwarantuje powodzenia kolejnego żądania.</p><p className="mb-2 rounded-md bg-subtle p-3 text-sm">Model i OCR: nie sprawdzono gotowości. Metadane modelu, licencji i lokalizacji nie zostały udostępnione.</p><p className="mb-2 rounded-md bg-subtle p-3 text-sm">Konfiguracja klas: {classes.isPending ? "ładowanie…" : classes.isError ? "nie udało się pobrać" : `${classes.data.length} klasy`}. Wersja YAML i limit pliku: nie podano.</p><Link className="inline-flex min-h-11 items-center text-sm underline" href="/jak-to-dziala">Pokaż wszystkie modele, licencje i lokalizację ›</Link></section>
        <details open className={card}><summary className="min-h-11 cursor-pointer font-semibold">Jak grupujemy pliki</summary><p className="text-sm">Pliki wybrane razem tworzą jedną paczkę roboczą. Każdy dokument analizujemy niezależnie; nie uzupełniamy danych z innych plików.</p><p className="mt-2 text-sm">Nazwa pliku nie wpływa na rozpoznanie rodzaju dokumentu.</p></details>
      </div>
      <div className="min-w-0 space-y-5">
        {submittedIds.length > 0 && <BatchProgress documents={submitted} total={submittedIds.length} name={caseName || "Nowa paczka dokumentów"} refreshError={documents.isError} onRefresh={() => void documents.refetch()} />}
        <section aria-labelledby="recent-added"><div className="mb-3 flex flex-wrap items-center justify-between gap-2"><h2 id="recent-added" className="text-lg font-semibold">Ostatnio dodane</h2><Link className="inline-flex min-h-11 items-center text-sm underline" href="/dokumenty">Przeglądaj wszystkie ›</Link></div><div className="mb-3 flex flex-wrap gap-2"><label className="min-w-0 flex-1"><span className="sr-only">Szukaj po nazwie pliku</span><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Szukaj po nazwie pliku" className="min-h-11 w-full rounded-md border border-control bg-surface px-3 text-sm" /></label><label><span className="sr-only">Sortowanie</span><select value={sort} onChange={event => setSort(event.target.value)} className="min-h-11 max-w-full rounded-md border border-control bg-surface px-3 text-sm"><option value="newest">Najnowsze</option><option value="name">Nazwa</option></select></label></div>
          {documents.isPending ? <div role="status" className="h-48 animate-pulse rounded-md bg-subtle">Ładowanie dokumentów…</div> : documents.isError ? <div role="alert">Nie udało się pobrać dokumentów. <Button className="min-h-11" variant="secondary" onClick={() => void documents.refetch()}>Spróbuj ponownie</Button></div> : recent.length === 0 ? <p className="text-sm text-muted">{search ? "Brak dokumentów pasujących do wyszukiwania." : "Nie masz jeszcze żadnych analiz."}</p> : <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">{recent.map(d => <li className="min-w-0" key={d.id}><Link href={`/dokumenty/${d.id}`} className="block overflow-hidden rounded-md border border-border bg-surface"><div aria-hidden className="flex h-28 items-center justify-center bg-subtle"><span className="bg-surface px-6 py-4 text-3xl text-muted">▤</span></div><div className="space-y-2 p-3"><p className="break-all text-xs font-medium">{d.fileName}</p><StatusBadge status={d.status} /></div></Link></li>)}</ul>}
        </section>
      </div>
    </div>
  </div>;
}
