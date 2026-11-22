"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import type { DocumentRecord } from "@/lib/api/schemas";

export function BatchProgress({ documents, total, name, refreshError, onRefresh }: { documents: DocumentRecord[]; total: number; name: string; refreshError: boolean; onRefresh: () => void }) {
  const [filter, setFilter] = useState("all");
  const completed = documents.filter(d => d.status !== "running").length;
  const finished = documents.length === total && completed === total;
  const filters = [{ id: "all", label: "Wszystkie", count: total }, { id: "ready", label: "Pełne / częściowe", count: documents.filter(d => ["full", "partial"].includes(d.status)).length }, { id: "foreign", label: "Obce", count: documents.filter(d => d.status === "foreign").length }, { id: "error", label: "Błędy techniczne", count: documents.filter(d => d.status === "error").length }, { id: "running", label: "W toku", count: documents.filter(d => d.status === "running").length }];
  const visible = documents.filter(d => filter === "all" || (filter === "ready" ? ["full", "partial"].includes(d.status) : d.status === filter));
  return <section className="min-w-0 rounded-md border border-border bg-surface p-5" aria-label="Postęp analizy">
    <h2 className="mb-3 text-xl font-semibold">{finished ? "Analiza zakończona" : "Analiza w toku"}</h2>
    <p className="mb-3 break-words text-sm text-muted">{name}</p>
    <div aria-live="polite" role="status"><p className="rounded-md bg-[var(--running-bg)] p-3 text-sm text-[var(--running-fg)]">Przetworzono {completed} z {total} dokumentów</p><progress aria-label="Postęp analizy" className="my-3 h-3 w-full accent-primary" max={total} value={completed} /></div>
    <div aria-label="Filtr postępu" className="mb-3 flex flex-wrap gap-2">{filters.map(item => <Button key={item.id} className="min-h-11 px-3 text-xs" variant={filter === item.id ? "primary" : "secondary"} aria-pressed={filter === item.id} onClick={() => setFilter(item.id)}>{item.label} {item.count}</Button>)}</div>
    <div className="hidden xl:block"><table className="w-full table-fixed text-left text-xs"><thead className="bg-subtle"><tr><th className="p-2">Plik</th><th className="p-2">Rozpoznano jako</th><th className="p-2">Status</th><th className="p-2">Pola</th><th className="p-2">Akcja</th></tr></thead><tbody>{visible.map(d => <tr key={d.id} className="border-t border-border"><td className="break-all p-2">{d.fileName}<span className="block text-muted">{d.pages} str.</span></td><td className="break-words p-2">{d.className ?? "—"}</td><td className="p-2"><StatusBadge status={d.status} /></td><td className="p-2">{d.fields.length ? `${d.fields.filter(f => f.state === "ok" || f.state === "poprawione").length}/${d.fields.length}` : "—"}</td><td className="p-2">{d.status === "running" ? <span className="text-muted">W toku</span> : <Link className="inline-flex min-h-11 items-center underline" href={`/dokumenty/${d.id}`}>Przejrzyj</Link>}</td></tr>)}</tbody></table></div>
    <ul className="xl:hidden">{visible.map(d => <li key={d.id} className="space-y-2 border-t border-border py-3"><div className="flex flex-wrap items-center justify-between gap-2"><span className="min-w-0 break-all text-sm">{d.fileName}</span><StatusBadge status={d.status} /></div><p className="text-xs text-muted">{d.pages} str. · {d.className ?? "Rozpoznawanie w toku"}</p>{d.status !== "running" && <Link className="inline-flex min-h-11 items-center text-sm underline" href={`/dokumenty/${d.id}`}>Przejrzyj</Link>}</li>)}</ul>
    {visible.length === 0 && <p className="py-3 text-sm text-muted">Brak dokumentów o wybranym statusie.</p>}
    {refreshError && <p role="alert">Nie udało się odświeżyć postępu. <Button className="min-h-11" variant="secondary" onClick={onRefresh}>Spróbuj ponownie</Button></p>}
    {finished && <Link href="/dokumenty" className="mt-4 inline-flex min-h-11 items-center rounded-md bg-primary px-4 text-sm text-on-primary">Przejdź do dokumentów</Link>}
  </section>;
}
