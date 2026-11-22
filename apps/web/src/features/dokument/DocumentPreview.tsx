"use client";
import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import type { DocumentRecord } from "@/lib/api/schemas";
import { useDiagnosis } from "@/lib/api/hooks";
import s from "./dokument.module.css";

export function DocumentPreview({ doc, page, setPage, selected, select, mobileVisible }: { doc: DocumentRecord; page: number; setPage: (n: number) => void; selected: string | null; select: (id: string) => void; mobileVisible: boolean }) {
  const [text, setText] = useState(false);
  const [thumbnails, setThumbnails] = useState(false);
  const [zoom, setZoom] = useState(100);
  const diagnosis = useDiagnosis(doc.id);
  const pageDiagnosis = diagnosis.data?.pages.find(p => p.number === page);
  const sourceLabel = pageDiagnosis?.text_source === "ocr" ? "Skan — tekst z OCR" : pageDiagnosis?.text_source === "pdf" ? "Tekst PDF" : pageDiagnosis?.text_source === "mixed" ? "Tekst PDF i OCR" : pageDiagnosis?.text_source === "none" ? "Strona nieprzetworzona" : "Źródło tekstu nieustalone";
  const evidence = doc.evidence.filter(e => e.page === page);
  return <section aria-label="Podgląd dokumentu" className={`${s.preview} ${mobileVisible ? s.mobilePreview : ""}`}>
    <div className={s.toolbar}>
      <Button variant="ghost" className="min-h-11 px-2" aria-pressed={thumbnails} onClick={() => setThumbnails(!thumbnails)}>Miniatury</Button>
      <span aria-live="polite">Strona {doc.pages ? page : 0} z {doc.pages}</span>
      <Button variant="ghost" className="min-h-11 px-2" disabled={zoom <= 75} aria-label="Pomniejsz" onClick={() => setZoom(zoom - 25)}>−</Button><span>{zoom}%</span>
      <Button variant="ghost" className="min-h-11 px-2" disabled={zoom >= 150} aria-label="Powiększ" onClick={() => setZoom(zoom + 25)}>+</Button>
      <Button variant="ghost" className="min-h-11 px-2" onClick={() => setZoom(100)}>Dopasuj do szerokości</Button>
      <Button variant={text ? "secondary" : "primary"} className="min-h-11 px-2" aria-pressed={!text} onClick={() => setText(false)}>PDF</Button>
      <Button variant={text ? "primary" : "secondary"} className="min-h-11 px-2" aria-pressed={text} onClick={() => setText(true)}>Tekst strony</Button>
    </div>
    {thumbnails && <div className="mb-3 flex flex-wrap gap-2" aria-label="Miniatury stron">{Array.from({ length: doc.pages }, (_, i) => <Button key={i} className="min-h-11" variant="secondary" aria-label={`Przejdź do strony ${i + 1}`} onClick={() => setPage(i + 1)}>{i + 1}</Button>)}</div>}
    {text && evidence.some(e => e.source === "ocr" && e.confidence !== null && e.confidence < 0.9) && <p className="mb-3 rounded bg-[var(--partial-bg)] p-3 text-sm text-[var(--partial-fg)]">⚠ Niska jakość odczytu OCR na tej stronie. Porównaj fragment z dokumentem.</p>}
    {doc.pages === 0 ? <p role="status" className={s.notice}>Podgląd niedostępny: nie odczytano stron pliku.</p> : <>
      <div role="region" aria-label="Strona PDF; strzałki zmieniają stronę" tabIndex={0} onKeyDown={e => { if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); setPage(Math.max(1, Math.min(doc.pages, page + (e.key === "ArrowRight" ? 1 : -1)))); } }} className={s.paper} style={{ fontSize: `${13 * zoom / 100}px`, overflow: text ? "visible" : "hidden", height: text ? "auto" : undefined }}>
        {text ? <><h2 className="mb-4 font-semibold">Strona {page} · {sourceLabel}</h2>{diagnosis.isError && <p role="alert">Nie udało się odczytać źródła tekstu. <Button onClick={() => diagnosis.refetch()}>Ponów diagnozę</Button></p>}<p className="whitespace-pre-wrap">{pageDiagnosis?.text_source === "none" ? "Nie przetworzono strony. Szczegóły i kody w diagnozie." : doc.pageText[page - 1] ?? "Brak tekstu dla tej strony. Strona może wymagać OCR."}</p>{evidence.map(e => <button key={e.id} className="mt-4 block min-h-11 w-full rounded border border-control p-2 text-left" style={selected === e.id ? { background: "var(--evidence-bg)", color: "var(--evidence-border)" } : undefined} aria-pressed={selected === e.id} onClick={() => select(e.id)}>{e.quote}</button>)}</> : <>
          <p className="text-right text-xs">Materiał syntetyczny · str. {page}</p><h2 className={s.pageTitle}>{doc.className ?? "DOKUMENT"}</h2>
          <p className="whitespace-pre-wrap">{doc.pageText[page - 1] ?? "Brak tekstu strony."}</p>
          <div aria-hidden="true" className="mt-10 space-y-3">{Array.from({ length: 6 }, (_, i) => <div key={i} className="h-1 bg-border" style={{ width: `${100 - i * 7}%` }} />)}</div>
          {evidence.filter(e => e.box && e.id === selected).map(e => <button key={e.id} title={e.quote} aria-label={`Dowód: ${e.quote}`} aria-pressed={selected === e.id} className={`${s.evidence} ${selected === e.id ? s.selected : ""}`} style={{ left: `${e.box!.x * 100}%`, top: `${e.box!.y * 100}%`, width: `${e.box!.w * 100}%`, height: `${e.box!.h * 100}%` }} onClick={() => select(e.id)} />)}
        </>}
      </div>
      <p className="mt-3 text-center text-xs text-muted">Podgląd syntetyczny, nie oryginalny PDF. Obrys według geometrii dowodu.</p>
      <div className="mt-3 flex items-center justify-between gap-2"><Button variant="secondary" className="min-h-11" disabled={page <= 1} onClick={() => setPage(page - 1)}>Poprzednia strona</Button><Button variant="secondary" className="min-h-11" disabled={page >= doc.pages} onClick={() => setPage(page + 1)}>Następna strona</Button></div>
    </>}
  </section>;
}
