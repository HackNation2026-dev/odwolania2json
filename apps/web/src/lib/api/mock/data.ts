import type { DocumentRecord, Evidence } from "../schemas";
import { contractClasses, fieldsFromResult } from "../contract";
import type { Diagnosis, Pipeline, PipelineStage } from "../processing";

export const classes = contractClasses;
export const appealResult = {
  OdwolanieKIO: { data: "2025-10-13", czynnosc_dzien: "2025-10-07", czynnosc_powod_id: 9, czynnosc_opis: "Decyzja o unieważnieniu postępowania", miejscowosc: "Pruszków" },
  Odwolujacy: [{ krs: "0000054588", nazwa: "Belmoria Rozwiązania S.A.", nip: "5210012345", regon: "012345678", "przez-pelnomocnika": 1, pelnomocnik: { imie_nazwisko: "Marta Jaworska", nazwa: "Kancelaria Jaworska", mail: "marta@example.test" } }],
  Zamawiajacy: [{ krs: "0000067890", nazwa: "Aurelink Automatyka S.A.", nip: "5250001234", regon: "987654321", prowadzacy_postepowanie: null }],
  ZamowieniePubliczne: { numer_bzp: "2026/BZP00999778", numer_postepowania: "ZP.039.2026", numer_ted: "999137-2026", tytul: "Zakup i dostawa systemów telematycznych do obsługi zgłoszeń obywateli" },
};
export const powerResult = { mocodawca: [{ data: { imie_nazwisko: null, krs: "0000054588", nazwa: "Belmoria Rozwiązania S.A.", nip: "5210012345", typ: "osoba_prawna" }, podpisujacy: [{ imie_nazwisko: "Jan Nowak" }] }], pelnomocnicy: [{ imie_nazwisko: "Marta Jaworska", pesel: "85120133547" }] };
export const transferResult = { przelew_bankowy: { data_operacji: "2026-10-13", kwota: 200.00, na_rachunek: "68101010100000000012345678", numer_transakcji: "000012342026", tytul: "Opłata od odwołania — Belmoria Rozwiązania S.A.", z_rachunku: "12102010260000000098765432" } };

function make(n: number, status: DocumentRecord["status"], classId: DocumentRecord["classId"] = "odwolanie", fileName = `odwolanie-${String(n).padStart(3, "0")}.pdf`): DocumentRecord {
  const cls = classes.find(c => c.id === classId);
  const result = classId === "przelew" ? transferResult : classId === "pelnomocnictwo" ? powerResult : appealResult;
  const fields = status === "full" || status === "partial" ? fieldsFromResult(classId!, result) : [];
  const evidence: Evidence[] = [];
  for (const field of fields) {
    if (field.value === null) { field.gap = { reason: "not_applicable", codes: [], description: "Nie dotyczy: osoba prawna lub jeden zamawiający; oceniono treść dokumentu.", reviewRequired: false }; continue; }
    const id = `e${n}-${evidence.length + 1}`;
    const derived = field.key.endsWith("czynnosc_opis");
    const quote = derived ? "Pierwszy zarzut: decyzja o unieważnieniu postępowania" : `${field.label}: ${field.value}`;
    const page = field.key.includes("czynnosc") ? 3 : 1;
    evidence.push({ id, fieldKey: field.key, page, quote, source: n === 4 ? "ocr" : "pdf", method: derived ? "rule" : /nip|krs|regon|numer|kwota/.test(field.key) ? "regex" : "ai", confidence: n === 4 ? 0.74 : null, box: { x: 0.1, y: 0.12 + (evidence.length % 20) * 0.035, w: 0.8, h: 0.03 }, bbox: [[60, 100 + evidence.length * 20, 530, 115 + evidence.length * 20]], words: [`p${page}w${evidence.length + 1}`], rule: derived ? "ze_slownika v1: czynnosc_powod_id = 9" : null, premiseIds: derived ? [`e${n}-3`] : [] });
    field.evidenceIds = [id]; if (derived) field.state = "wyliczone";
  }
  const pages = classId === "odwolanie" || n === 9 ? 3 : 1;
  const done = status !== "running";
  return { id: `doc-${n}`, fileName, pages, sizeKb: 220, status, classId, className: cls?.name ?? null, uploadedAt: `2026-11-21T10:${String(n).padStart(2, "0")}:00Z`, batchId: "przyklad_01", progress: done ? undefined : 40, fields, evidence, reasons: [], errorCode: status === "error" ? "LLM_TIMEOUT" : null, candidates: status === "ambiguous" ? ["Odwołanie do KIO", "Pełnomocnictwo"] : [], pageText: Array.from({ length: pages }, (_, i) => `Scenariusz syntetyczny · ${fileName}\n${evidence.filter(e => e.page === i + 1).map(e => e.quote).join("\n")}`), processedPages: done ? Array.from({ length: pages }, (_, i) => i + 1) : [1], unprocessedPages: done ? [] : [2, 3], codes: status === "foreign" ? ["dokument_obcy"] : status === "multi" ? ["wiele_dokumentow"] : status === "ambiguous" ? ["class_ambiguous"] : n === 4 ? ["scan", "invalid_ocr_layer"] : [], state: { progress: done ? "done" : "running", outcome: status === "full" ? "complete" : status === "error" ? "technical_error" : status === "multi" ? "ambiguous" : status === "running" ? null : status, stage: status === "error" ? "T3" : done ? "export" : "E" }, technicalErrors: status === "error" ? [{ stage: "T3", code: "LLM_TIMEOUT", description: "Przekroczono czas odpowiedzi modelu.", retryable: true, attempt: 1, page: null }] : [], resultVersion: n === 1 ? 3 : 1, contractRevision: "main-7590db8 / openapi 0.5.0" };
}

export function seedDocuments(): DocumentRecord[] {
  const partial = make(3, "partial");
  partial.fields.find(f => f.key === "Zamawiajacy.0.prowadzacy_postepowanie")!.value = 1;
  const reasons = ["missing", "not_applicable", "unreadable", "conflicting", "unprocessed"] as const;
  const keys = ["OdwolanieKIO.data", "Odwolujacy.0.regon", "Odwolujacy.0.krs", "ZamowieniePubliczne.numer_ted", "ZamowieniePubliczne.numer_postepowania"];
  keys.forEach((key, i) => {
    const field = partial.fields.find(f => f.key === key)!;
    field.value = null; field.state = "brak"; field.evidenceIds = [];
    field.gap = { reason: reasons[i]!, codes: [["information_not_explicit"], [], ["low_quality"], [], ["ocr_unavailable"]][i]!, description: ["Nie znaleziono informacji. Sprawdzone strony: 1, 3.", "Nie dotyczy: identyfikator nie ma zastosowania w tym scenariuszu.", "Treść jest obecna, ale nie można jej odczytać.", "Znaleziono sprzeczne wartości. Porównaj dowody.", "Nie przetworzono strony 2: OCR niedostępny."][i]!, reviewRequired: i >= 2 };
  });
  partial.evidence = partial.evidence.filter(e => !keys.includes(e.fieldKey));
  partial.reasons = [...reasons]; partial.processedPages = [1, 3]; partial.unprocessedPages = [2]; partial.codes = ["ocr_unavailable"];
  return [make(1, "full", "odwolanie", "odwolanie.pdf"), make(2, "full", "odwolanie", "odwolanie-wodociagi.pdf"), partial, make(4, "partial", "odwolanie", "skan-odwolanie.pdf"), make(5, "ambiguous", null), make(6, "error", null, "timeout.pdf"), make(7, "foreign", "obcy", "menu-restauracji.pdf"), make(8, "multi", null, "zbiorczy-skan.pdf"), make(9, "running", null, "nowe-odwolanie.pdf"), make(10, "full", "przelew", "przelew.pdf"), make(11, "full", "pelnomocnictwo", "pelnomocnictwo.pdf"), make(12, "full", "odwolanie", "odwolanie-uzupelnione.pdf")];
}

export function diagnosisFor(doc: DocumentRecord): Diagnosis {
  const scan = doc.id === "doc-4" || doc.id === "doc-3";
  const part = { text_source: doc.id === "doc-4" ? "ocr" as const : scan ? "mixed" as const : "pdf" as const, coverage: doc.unprocessedPages.length ? 0.65 : 1, rotation_degrees: 0, confidence: null, method: "diagnosis-v1-demo", requires_ocr: scan, signals: [{ code: "text_layer", value: !scan, description: scan ? "Obraz z tekstem; warstwa OCR wymaga kontroli" : "Odczytano tekst cyfrowy" }], codes: doc.codes };
  return { ...part, schema_version: 1, pages: Array.from({ length: doc.pages }, (_, i) => ({ ...part, number: i + 1, text_source: doc.unprocessedPages.includes(i + 1) ? "none" : doc.id === "doc-4" ? "ocr" : "pdf", coverage: doc.unprocessedPages.includes(i + 1) ? 0 : 1, regions: scan && i === 1 ? [{ ...part, id: "R3", bbox: [40, 100, 500, 300], rotation_degrees: 90, text_source: "ocr", signals: [{ code: "orientation", value: 90, description: "Obraz z tekstem, obrót 90° → 0°, niska jakość; tekst warstwy niezgodny z obrazem" }], codes: ["zla_warstwa_ocr"] }] : [] })) };
}

export function pipelineFor(doc: DocumentRecord): Pipeline {
  const stages: [PipelineStage["id"], string][] = [["E", "Odczyt i diagnoza PDF / OCR"], ["L", "Trwały zapis odczytu"], ["T1", "Segmenty i rozpoznanie klasy"], ["T2", "Podmioty i role"], ["T3", "Kandydaci pól i dowody"], ["T4", "Scalanie i pokrycie"], ["T5", "Normalizacja i walidacja"], ["export", "Eksport wyniku"]];
  const stop = doc.status === "running" ? 0 : doc.status === "error" ? 4 : ["foreign", "ambiguous", "multi"].includes(doc.status) ? 2 : 7;
  return { documentId: doc.id, stages: stages.map(([id, name], i) => {
    const skipped = id === "T2" || id === "T4" || (i > stop && !(id === "export" && doc.status === "foreign"));
    const state = doc.status === "running" ? i === 0 ? "w toku" : "oczekuje" : doc.status === "error" && i === stop ? "błąd" : skipped ? "pominięty" : "zakończony";
    return { id, name, state, durationMs: state === "zakończony" || state === "błąd" ? 120 + i * 80 : null, errorCode: state === "błąd" ? doc.errorCode : null, counts: state !== "zakończony" ? null : id === "E" ? { pages: doc.pages, ocrPages: doc.id === "doc-4" ? doc.pages : doc.id === "doc-3" ? 1 : 0 } : id === "T1" ? { className: doc.className ?? "Klasa nieustalona", routerSignals: doc.status === "foreign" ? ["Wystarczający odczyt; brak funkcji odwołania, umocowania i potwierdzenia płatności"] : doc.status === "ambiguous" || doc.status === "multi" ? ["Konflikt funkcji dokumentu; brak jednoznacznego rozstrzygnięcia"] : [`Treść wskazuje funkcję: ${doc.className}`] } : { filled: doc.fields.filter(f => f.value !== null).length, empty: doc.fields.filter(f => f.value === null).length, evidence: doc.evidence.length } };
  }) };
}
