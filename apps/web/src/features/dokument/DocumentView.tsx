"use client";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { useDocument, useDocuments, useExportDecision, useExportJson } from "@/lib/api/hooks";
import { ApiError } from "@/lib/api/client";
import { DocumentPreview } from "./DocumentPreview";
import { DocumentException } from "./DocumentException";
import { DocumentField } from "./DocumentField";
import { DocumentEvidence } from "./DocumentEvidence";
import { DocumentJson } from "./DocumentJson";
import { downloadText, formatDocumentJson } from "./format";
import s from "./dokument.module.css";

export function DocumentView({ id, tab = "przeglad" }: { id: string; tab?: string }) {
  const query = useDocument(id);
  const documents = useDocuments();
  const decision = useExportDecision(id);
  const exportJson = useExportJson();
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<string | null>(null);
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [filter, setFilter] = useState("all");
  const [message, setMessage] = useState("");
  const activeTab = ["json", "dowody", "eksport", "dokument"].includes(tab) ? tab : "przeglad";
  if (query.isPending) return <section aria-busy="true" aria-label="Wczytywanie dokumentu"><p role="status">Wczytywanie dokumentu…</p><div className="mt-4 grid animate-pulse gap-4 md:grid-cols-2"><div className="h-96 rounded bg-subtle" /><div className="h-96 rounded bg-subtle" /></div></section>;
  if (query.isError) return <section role="alert" className="mx-auto max-w-md py-16 text-center"><p className="text-6xl font-bold text-muted">{query.error instanceof ApiError && query.error.code === "NOT_FOUND" ? "404" : "!"}</p><h1 className="mt-4 text-xl font-semibold">{query.error instanceof ApiError && query.error.code === "NOT_FOUND" ? "Nie znaleziono strony" : "Nie udało się wczytać dokumentu"}</h1><p className="my-4">{query.error instanceof ApiError && query.error.code === "NOT_FOUND" ? "Nie znaleziono tej sprawy lub dokumentu. Mógł zostać usunięty." : "Nie udało się połączyć z serwerem. Sprawdź połączenie i spróbuj ponownie."}</p><Link href="/dodaj" className="inline-flex min-h-11 items-center rounded bg-primary px-4 text-on-primary">Przejdź do nowej analizy</Link><Button className="mt-3 min-h-11" variant="secondary" onClick={() => query.refetch()}>Spróbuj ponownie</Button></section>;
  const doc = query.data;
  const json = formatDocumentJson(doc);
  const index = documents.data?.findIndex(d => d.id === id) ?? -1;
  const previous = index > 0 ? documents.data?.[index - 1] : undefined;
  const next = index >= 0 ? documents.data?.[index + 1] : undefined;
  function selectEvidence(evidenceId: string) {
    const evidence = doc.evidence.find(e => e.id === evidenceId);
    if (!evidence) return;
    setSelected(evidence.id); setSelectedField(doc.fields.find(field => field.evidenceIds.includes(evidence.id))?.key ?? evidence.fieldKey); setPage(evidence.page);
  }
  const selectedEvidence = doc.evidence.find(e => e.id === selected);
  async function downloadJson() {
    if (!decision.data?.allowed || decision.isFetching) return;
    try { const result = await exportJson.mutateAsync(id); downloadText(result.fileName, result.json); setMessage("Pobrano JSON."); }
    catch (e) { setMessage(e instanceof Error ? e.message : "Nie udało się pobrać JSON."); }
  }
  function downloadReport(evidenceOnly: boolean) {
    const data = evidenceOnly ? { documentId: id, evidence: doc.evidence } : { documentId: id, status: doc.status, reasons: doc.reasons, errorCode: doc.errorCode, pages: doc.pages, exportDecision: decision.data ?? null };
    downloadText(`${doc.fileName.replace(/\.pdf$/i, "")}.${evidenceOnly ? "dowody" : "raport"}.json`, JSON.stringify(data, null, 2));
  }
  const blockers = <>{decision.isPending && <p role="status">Sprawdzanie warunków eksportu…</p>}{decision.isError && <div role="alert"><p>Nie udało się sprawdzić eksportu. Pobranie pozostaje zablokowane.</p><Button className="min-h-11" variant="secondary" onClick={() => decision.refetch()}>Sprawdź eksport ponownie</Button></div>}{decision.data && <section aria-label="Decyzja eksportu" className={s.notice}><h2 className="font-semibold">{decision.data.allowed ? "✓ Eksport dozwolony" : "! Eksport zablokowany"}</h2><p className="text-sm">Wariant A — ścisła walidacja eksportu</p>{decision.data.blockers.length > 0 && <ul className="mt-2 list-disc pl-5">{decision.data.blockers.map(b => <li key={`${b.code}-${b.message}`}>{b.message}</li>)}</ul>}</section>}</>;
  return <div className={s.workspace}>
    <header className={s.header}><div className="min-w-0"><p className={s.breadcrumb}><Link href="/dokumenty">Dokumenty</Link> / {doc.batchId}</p><h1 className="break-all text-lg font-semibold">{doc.fileName}</h1><div className="mt-1 flex flex-wrap items-center gap-2 text-xs"><span className="rounded bg-subtle px-2 py-1">{doc.className ?? "Klasa nieustalona"}</span><StatusBadge status={doc.status} /><span className={s.resultMeta}>{doc.status === "error" ? "Brak wyniku" : doc.status === "running" ? "Analiza trwa" : "Wynik analizy"} · dane syntetyczne</span></div></div><nav aria-label="Sąsiednie dokumenty" className={s.documentNavigation}>{previous ? <Link className="inline-flex min-h-11 items-center rounded border border-control px-3 text-sm" href={`/dokumenty/${previous.id}`}>‹ Poprzedni</Link> : <Button className="min-h-11" variant="secondary" disabled>‹ Poprzedni</Button>}<span className="text-xs">{index >= 0 ? index + 1 : "—"} z {documents.data?.length ?? "—"}</span>{next ? <Link className="inline-flex min-h-11 items-center rounded border border-control px-3 text-sm" href={`/dokumenty/${next.id}`}>Następny ›</Link> : <Button className="min-h-11" variant="secondary" disabled>Następny ›</Button>}</nav></header>
    <div className={s.columns}>
      <DocumentPreview doc={doc} page={page} setPage={setPage} selected={selected} select={selectEvidence} mobileVisible={activeTab === "dokument"} />
      <div className={s.content}>
        <nav aria-label="Widoki dokumentu" className={s.tabs}><Link className={s.mobileDoc} href={`/dokumenty/${id}?tab=dokument`} aria-current={activeTab === "dokument" ? "page" : undefined}>Dokument</Link>{[["przeglad", "Przegląd"], ["json", "JSON"], ["dowody", "Dowody"], ["eksport", "Eksport"]].map(([key, label]) => <Link key={key} aria-current={activeTab === key ? "page" : undefined} href={`/dokumenty/${id}?tab=${key}`}>{label}</Link>)}</nav>
        <div role="region" aria-label="Zawartość widoku dokumentu" tabIndex={0} className={`${activeTab === "dokument" ? "" : "scroll-pane"} ${s.panel} ${activeTab === "dokument" ? s.mobileHidden : ""}`}>
          {(activeTab === "przeglad" || activeTab === "dokument") && <>
            <DocumentException doc={doc} />
            {doc.className && <div className={s.recognition}><strong>Rozpoznano: {doc.className} · na podstawie treści dokumentu</strong><details><summary>Dlaczego?</summary><p>Wynik klasyfikacji pochodzi z silnika. Dostępne cytaty i źródła znajdziesz w zakładce Dowody.</p></details></div>}
            {doc.fields.length > 0 && <>
              <div className={s.fieldFilters} aria-label="Filtry pól">{([
                ["all", `Wszystkie pola (${doc.fields.length})`],
                ["review", `Do sprawdzenia (${doc.fields.filter(f => f.state === "missing" || doc.evidence.some(e => e.fieldKey === f.key && e.confidence < 0.9)).length})`],
                ["missing", `Braki (${doc.fields.filter(f => f.value === null).length})`],
              ] as const).map(([value, label]) => <Button key={value} className={s.filterButton} variant={filter === value ? "primary" : "ghost"} aria-pressed={filter === value} onClick={() => setFilter(value)}>{label}</Button>)}<span className="text-xs text-muted">Wypełniono {doc.fields.filter(f => f.value !== null).length} z {doc.fields.length} pól</span></div>
              <section className={s.fieldGroup} aria-label="Pola dokumentu">
                <h2 className={s.groupTitle}>{doc.className ?? "Dane dokumentu"} · <code>{doc.classId ?? "klasa nieustalona"}</code></h2>
                {doc.fields.filter(f => filter === "all" || (filter === "missing" ? f.value === null : f.state === "missing" || doc.evidence.some(e => e.fieldKey === f.key && e.confidence < 0.9))).map(field => <DocumentField key={field.key} id={id} field={field} active={selectedField === field.key} evidence={doc.evidence.filter(e => field.evidenceIds.includes(e.id))} onSelect={() => { setSelectedField(field.key); const e = doc.evidence.find(e => field.evidenceIds.includes(e.id)); if (e) selectEvidence(e.id); else setSelected(null); }} />)}
                {!doc.fields.some(f => filter === "all" || (filter === "missing" ? f.value === null : f.state === "missing" || doc.evidence.some(e => e.fieldKey === f.key && e.confidence < 0.9))) && <p className={s.notice}>Brak pól spełniających wybrany filtr.</p>}
              </section>
            </>}
            {selectedEvidence && <p className="my-3 text-sm">Wybrany dowód: strona {selectedEvidence.page} · {selectedEvidence.quote}</p>}
          </>}
          {activeTab === "json" && <DocumentJson json={json} blocked={!decision.data?.allowed || decision.isFetching} />}
          {activeTab === "dowody" && <DocumentEvidence doc={doc} select={selectEvidence} downloadReport={() => downloadReport(false)} />}
          {activeTab === "eksport" && <><h2 className="mb-4 text-xl font-semibold">Eksport przy brakach i błędach: wariant A (wybrany)</h2>{blockers}<p className={s.card}>Brak lub nieczytelność z null niedozwolonym przez schemat blokuje pobranie. Błąd techniczny oznacza brak pliku wynikowego. Pełny lub częściowy wynik jest dostępny, gdy wszystkie wartości i null są dopuszczone.</p><section className={s.card}><h3 className="font-semibold">Wariant B — jawny eksport konkursowy mimo braków (odrzucony)</h3><p>Nie jest dostępny w aplikacji. Wynik z brakami niezgodnymi ze schematem może zostać odrzucony przez ewaluator.</p><Button className="my-3 min-h-11" variant="secondary" disabled>Pobierz JSON z brakami (niedostępny)</Button><p>Błąd techniczny: brak pliku wynikowego. Niejednoznaczny lub wiele dokumentów: eksport zablokowany do rozstrzygnięcia.</p></section><ul className="list-disc space-y-2 pl-5"><li>Braków nie uzupełniamy fikcyjną wartością.</li><li>Dowody i raport są zapisane osobno.</li><li>Wynik dokumentu obcego to dokładnie {'{}'} pod nazwą bazową PDF.</li><li>Nieprzetworzone strony pozostają jawne.</li></ul>{doc.status === "foreign" && <p className={s.notice}>Wynik to dokładnie {'{}'}.</p>}</>}
        </div>
        <footer className={s.footer}>
          {activeTab !== "eksport" && <div className={s.exportSummary}>
            {decision.data ? <><h2>{decision.data.allowed ? "✓ Eksport dozwolony" : "! Eksport zablokowany"}</h2><Link href={`/dokumenty/${id}?tab=eksport`}>Wariant A · {decision.data.allowed ? "szczegóły" : "zobacz powody"}</Link></> : decision.isError ? <p role="alert">Nie udało się sprawdzić eksportu. <Button variant="ghost" className="min-h-11" onClick={() => decision.refetch()}>Sprawdź ponownie</Button></p> : <p role="status">Sprawdzanie warunków eksportu…</p>}
          </div>}
          <div className={s.footerActions}><Button className="min-h-11" disabled={!decision.data?.allowed || decision.isFetching || exportJson.isPending} onClick={downloadJson}>Pobierz JSON</Button><Button variant="secondary" className="min-h-11" onClick={() => downloadReport(true)}>Pobierz dowody</Button><span className="text-xs text-muted">Dowody zapisano osobno.</span></div>
          {message && <p role={exportJson.isError ? "alert" : "status"} className="text-sm">{message}</p>}
        </footer>
      </div>
    </div>
  </div>;
}
