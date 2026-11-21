"use client";
import Link from "next/link";
import { Button } from "@/components/atoms/Button";
import type { DocumentRecord } from "@/lib/api/schemas";
import s from "./dokument.module.css";

export function DocumentEvidence({ doc, select, downloadReport }: { doc: DocumentRecord; select: (id: string) => void; downloadReport: () => void }) {
  const fieldFor = (evidenceId: string) => doc.fields.find(field => field.evidenceIds.includes(evidenceId));
  return <>
    <p className="mb-3 text-xs text-muted">Dowody są zapisane poza ocenianym JSON. Czytelna postać cytatów i źródeł tego dokumentu.</p>
    {doc.evidence.length ? <>
      <div className={s.evidenceTable}><table><caption className="sr-only">Dowody pól dokumentu</caption><thead><tr><th scope="col">Pole</th><th scope="col">Str.</th><th scope="col">Fragment</th><th scope="col">Źródło tekstu</th><th scope="col">Metoda</th></tr></thead><tbody>{doc.evidence.map(e => <tr key={e.id}><td><code>{fieldFor(e.id)?.key ?? e.fieldKey}</code></td><td>{e.page}</td><td><Link href={`/dokumenty/${doc.id}?tab=przeglad`} onClick={() => select(e.id)} aria-label={`Pokaż dowód: ${e.quote}`}>„{e.quote}”</Link></td><td>{e.source === "ocr" ? "OCR" : "tekst PDF"}<br /><span className="text-muted">Pewność: {Math.round(e.confidence * 100)}%</span></td><td>Nieprzekazana</td></tr>)}</tbody></table></div>
      <div className={s.evidenceCards}>{doc.evidence.map(e => <article key={e.id} className={s.card}><h2 className="text-sm font-semibold">{fieldFor(e.id)?.label ?? e.fieldKey} · str. {e.page}</h2><blockquote className="my-2 text-sm">„{e.quote}”</blockquote><p className="text-xs text-muted">Źródło: {e.source === "ocr" ? "OCR" : "tekst PDF"} · Metoda: nieprzekazana · Pewność: {Math.round(e.confidence * 100)}%</p><Link className="inline-flex min-h-11 items-center text-sm underline" href={`/dokumenty/${doc.id}?tab=dokument`} onClick={() => select(e.id)}>Pokaż dowód na stronie {e.page}</Link></article>)}</div>
    </> : <p className={s.notice}>Brak dostępnych dowodów dla tego dokumentu.</p>}
    <section className={s.notice}><h2 className="text-sm font-semibold">Pokrycie stron</h2><p className="text-xs">Plik: {doc.pages} stron. Dostępny tekst: {doc.pageText.slice(0, doc.pages).filter(Boolean).length} stron. Dowody: {doc.evidence.length}.</p><p className="mt-1 text-xs text-muted">Szczegółowy raport przetwarzania stron i reguł nie został przekazany przez silnik.</p></section>
    <p className="mb-3 text-xs text-muted">Plik dowodów: {doc.fileName.replace(/\.pdf$/i, "")}.dowody.json · powiązany z dokumentem {doc.id}.</p>
    <Button variant="secondary" className="min-h-11" onClick={downloadReport}>Pobierz osobny raport</Button>
  </>;
}
