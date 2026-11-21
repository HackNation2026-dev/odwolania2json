"use client";

import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { useEvents } from "@/lib/api/hooks";
import type { EventType } from "@/lib/api/schemas";

export const eventLabels: Record<EventType, string> = { upload: "Wgranie", analysis: "Analiza", error: "Błąd", correction: "Korekta", export: "Eksport", configuration: "Konfiguracja YAML" };
const results = { success: { label: "✓ Powodzenie", tone: "text-[var(--full-fg)]" }, blocked: { label: "! Zablokowano", tone: "text-[var(--partial-fg)]" }, error: { label: "× Błąd", tone: "text-[var(--error-fg)]" } };

export function EventsView() {
  const query = useEvents();
  const [type, setType] = useState("");
  const events = query.data?.filter((event) => !type || event.type === type) ?? [];
  return <div className="space-y-5">
    <header className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-2xl font-semibold">Dziennik zdarzeń</h1><Button disabled variant="secondary" className="min-h-11">Eksportuj CSV (po MVP)</Button></header>
    <p className="rounded-lg bg-subtle p-4 text-sm">Po MVP / E3. Widok demonstracyjny z danymi syntetycznymi. Wpisy są tylko do odczytu i nie stanowią rzeczywistego rejestru działań użytkowników. Wartości pól pozostają zamaskowane.</p>
    <div className="flex flex-wrap items-end gap-3"><label className="flex min-w-0 flex-col gap-1 text-sm">Rodzaj zdarzenia<select className="min-h-11 max-w-full rounded-md border border-control bg-surface px-3" value={type} onChange={(event) => setType(event.target.value)}><option value="">Wszystkie zdarzenia</option>{Object.entries(eventLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><Button variant="secondary" className="min-h-11" onClick={() => setType("")}>Wyczyść filtry</Button></div>
    {query.isPending ? <div role="status" className="space-y-3"><p>Wczytywanie zdarzeń…</p><div aria-hidden className="h-48 animate-pulse rounded-lg bg-subtle" /></div> : query.isError ? <div role="alert" className="space-y-3 rounded-lg border border-control bg-surface p-4"><p>Nie udało się wczytać dziennika zdarzeń. Spróbuj ponownie.</p><Button className="min-h-11" onClick={() => void query.refetch()}>Spróbuj ponownie</Button></div> : events.length === 0 ? <p role="status">{type ? "Brak zdarzeń spełniających kryteria." : "Brak zdarzeń w tym zakresie."}</p> : <>
      <p role="status" aria-live="polite" className="text-sm text-muted">Liczba zdarzeń: {events.length}</p>
      <table className="w-full overflow-hidden rounded-lg border border-border bg-surface text-left text-sm max-lg:block"><caption className="sr-only">Syntetyczny dziennik zdarzeń</caption><thead className="bg-subtle text-muted max-lg:sr-only"><tr>{["Czas", "Zdarzenie", "Dokument", "Wynik"].map((label) => <th scope="col" className="p-3 font-medium" key={label}>{label}</th>)}</tr></thead><tbody className="max-lg:block">{events.map((event) => <tr key={event.id} className="border-t border-border align-top max-lg:block max-lg:p-3">
        <td className="p-3 max-lg:block max-lg:p-1"><span className="lg:hidden">Czas: </span><time dateTime={event.occurredAt}>{new Date(event.occurredAt).toLocaleString("pl-PL", { timeZone: "Europe/Warsaw", dateStyle: "short", timeStyle: "short" })}</time></td>
        <th scope="row" className="p-3 font-medium max-lg:block max-lg:p-1"><span className="lg:hidden">Zdarzenie: </span>{event.description}<p className="mt-1 font-normal text-muted">{eventLabels[event.type]}</p></th>
        <td className="break-all p-3 max-lg:block max-lg:p-1"><span className="lg:hidden">Dokument: </span>{event.documentName ?? "Nie dotyczy"}</td>
        <td className="max-w-md p-3 max-lg:block max-lg:p-1"><span className="lg:hidden">Wynik: </span><span className={results[event.result].tone}>{results[event.result].label}</span><details className="mt-1"><summary className="min-h-11 cursor-pointer py-3">Szczegóły zdarzenia</summary><p className="break-words">{event.detail}</p></details></td>
      </tr>)}</tbody></table>
    </>}
  </div>;
}
