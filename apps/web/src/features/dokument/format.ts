import type { DocumentRecord, Field, PartialReason } from "@/lib/api/schemas";
import { buildResult } from "@/lib/api/contract";

export const partialReasons: Record<PartialReason, { label: string; description: string }> = {
  missing: { label: "Brak", description: "Nie znaleziono informacji na sprawdzonych stronach dokumentu." },
  not_applicable: { label: "Nie dotyczy", description: "Pole nie ma zastosowania; reguła i przesłanki są opisane przy polu." },
  unreadable: { label: "Nieczytelne", description: "Treść jest obecna, ale nie można jej wiarygodnie odczytać." },
  conflicting: { label: "Sprzeczne", description: "Znaleziono sprzeczne wartości. Porównaj dowody z tego dokumentu." },
  unprocessed: { label: "Nieprzetworzone", description: "Nie przetworzono wskazanych stron lub regionów; nie oznacza to braku informacji." },
};

export function formatDocumentJson(doc: DocumentRecord): string | null {
  if (doc.status === "foreign") return "{}";
  if (doc.status !== "full" && doc.status !== "partial") return null;
  return JSON.stringify(buildResult(doc), null, 2);
}

export function parseFieldValue(field: Field, input: string): Field["value"] {
  if (!input.trim()) { if (!field.nullable) throw new Error("Null niedozwolony przez kontrakt."); return null; }
  if (field.type === "number" || field.type === "integer") {
    const value = Number(input.replace(",", "."));
    if (!Number.isFinite(value) || (field.type === "integer" && !Number.isInteger(value))) throw new Error("Podaj prawidłową liczbę.");
    return value;
  }
  if (typeof field.value === "boolean") {
    if (input !== "true" && input !== "false") throw new Error("Podaj true albo false.");
    return input === "true";
  }
  if (/(\.data|\.data_operacji|\.czynnosc_dzien)$/.test(field.key)) {
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
