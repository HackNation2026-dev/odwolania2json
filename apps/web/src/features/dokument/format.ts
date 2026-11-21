import type { DocumentRecord, Field, PartialReason } from "@/lib/api/schemas";

export const partialReasons: Record<PartialReason, { label: string; description: string }> = {
  ocr_unavailable: { label: "OCR niedostępny", description: "Strony wymagające OCR pozostają nieprzetworzone. Brak OCR nie oznacza dokumentu obcego." },
  unreadable_scan: { label: "Nieczytelny skan", description: "Treść jest obecna, ale nie można jej odczytać." },
  missing_field: { label: "Brak informacji", description: "Nie znaleziono informacji na sprawdzonych stronach. Uzupełnij pole po przeglądzie dokumentu." },
  low_confidence: { label: "Niska pewność", description: "Odczyt wymaga sprawdzenia. Porównaj wartość z dowodem." },
  page_limit: { label: "Limit stron", description: "Nie przetworzono wszystkich stron z powodu limitu. Brak odczytu nie oznacza braku informacji." },
};

export function formatDocumentJson(doc: DocumentRecord): string | null {
  if (doc.status === "foreign") return "{}";
  if (doc.status !== "full" && doc.status !== "partial") return null;
  return JSON.stringify(Object.fromEntries(doc.fields.map(f => [f.key, f.value])), null, 2);
}

export function parseFieldValue(field: Field, input: string): Field["value"] {
  if (!input.trim()) return null;
  if (typeof field.value === "number") {
    const value = Number(input.replace(",", "."));
    if (!Number.isFinite(value)) throw new Error("Podaj prawidłową liczbę.");
    return value;
  }
  if (typeof field.value === "boolean") {
    if (input !== "true" && input !== "false") throw new Error("Podaj true albo false.");
    return input === "true";
  }
  if (/^data_/.test(field.key)) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(input) || Number.isNaN(Date.parse(input)) || new Date(input).toISOString().slice(0, 10) !== input) throw new Error("Podaj prawidłową datę w formacie RRRR-MM-DD.");
  }
  return input.trim();
}

export function downloadText(fileName: string, value: string) {
  const url = URL.createObjectURL(new Blob([value], { type: "application/json;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
