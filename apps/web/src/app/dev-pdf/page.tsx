"use client";
// Tylko demo/e2e: brak linku w nawigacji produkcyjnej.
import { useState } from "react";
import { PdfViewer } from "@/components/organisms/PdfViewer";
import { pdfAsset } from "@/components/organisms/pdf/assets";
import geometry from "../../../public/demo-pdf/odwolanie.json";
export default function PdfDemoPage() {
  const [file, setFile] = useState("odwolanie");
  const [page, setPage] = useState(1);
  const [scale, setScale] = useState(1);
  const [selected, setSelected] = useState(
    geometry.find((h) => h.label.includes("Odwołujący:"))?.id,
  );
  const highlights =
    file === "odwolanie"
      ? geometry
      : file === "skan-odwolanie"
        ? geometry.filter((h) => h.page === 1)
        : [];
  return (
    <main className="min-w-0 p-2">
      <h1 className="text-xl">Syntetyczny dokument PDF</h1>
      <label htmlFor="pdf-demo-file">Dokument demo</label>
      <select
        id="pdf-demo-file"
        className="m-2 min-h-11 rounded border border-control bg-surface p-2"
        value={file}
        onChange={(event) => {
          setFile(event.target.value);
          setPage(1);
          setScale(1);
          setSelected(undefined);
        }}
      >
        <option value="odwolanie">Odwołanie</option>
        <option value="pelnomocnictwo">Pełnomocnictwo</option>
        <option value="przelew">Przelew</option>
        <option value="skan-odwolanie">Skan odwołania</option>
        <option value="missing">Brakujący plik (test błędu)</option>
      </select>
      <button
        type="button"
        className="min-h-11 rounded border border-control p-2"
        onClick={() => setSelected(geometry.find((h) => h.page === 2)?.id)}
      >
        Wybierz dowód ze strony 2
      </button>
      <PdfViewer
        file={pdfAsset(`demo-pdf/${file}.pdf`)}
        page={page}
        onPageChange={setPage}
        scale={scale}
        onScaleChange={setScale}
        highlights={highlights.map((h) => ({
          ...h,
          active: h.id === selected,
        }))}
        onHighlightClick={setSelected}
      />
    </main>
  );
}
