"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/atoms/Button";

export type SelectedPdf = { name: string; sizeKb: number; type: string };
export function DropZone({ onFiles, disabled = false }: { onFiles: (files: SelectedPdf[], messages: string[]) => void; disabled?: boolean }) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  function select(files: FileList | File[]) {
    const accepted: SelectedPdf[] = [];
    const messages: string[] = [];
    for (const file of Array.from(files)) {
      if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) messages.push(`${file.name}: to nie jest PDF — pominięto.`);
      else accepted.push({ name: file.name, sizeKb: file.size / 1024, type: "application/pdf" });
    }
    onFiles(accepted, messages);
  }
  return <div onDragOver={event => { event.preventDefault(); if (!disabled) setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); if (!disabled) select(event.dataTransfer.files); }} className={`rounded-md border-2 border-dashed p-6 text-center ${dragging ? "border-primary bg-subtle" : "border-control bg-subtle"}`}>
    <span aria-hidden className="mb-3 inline-block rounded-full bg-surface px-4 py-2 text-2xl">↑</span>
    <p className="mb-3 font-semibold"><span className="hidden sm:inline">{dragging ? "Upuść, aby dodać" : "Przeciągnij tutaj pliki PDF"}</span><span className="sm:hidden">Wybierz pliki PDF</span></p>
    <input ref={input} id="pdf-files" aria-label="Pliki PDF" tabIndex={-1} type="file" accept="application/pdf,.pdf" multiple disabled={disabled} className="sr-only" onChange={event => { if (event.target.files) select(event.target.files); event.target.value = ""; }} />
    <Button disabled={disabled} className="min-h-11 w-full sm:w-auto" onClick={() => input.current?.click()}>Wybierz pliki</Button>
    <p className="mt-4 text-xs text-muted">Tylko PDF. Tryb demonstracyjny: przekazujemy wyłącznie nazwę, rozmiar i typ pliku.</p>
  </div>;
}
