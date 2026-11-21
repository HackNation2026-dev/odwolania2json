import type { DocumentClass, DocumentRecord, Evidence, Field } from "../schemas";

export const classes: DocumentClass[] = [
  {
    id: "odwolanie",
    name: "Odwołanie od decyzji",
    description: "Pismo odwoławcze do organu wyższego stopnia.",
    fields: [
      { key: "sygnatura", label: "Sygnatura sprawy", required: true, nullable: false },
      { key: "data_pisma", label: "Data pisma", required: true, nullable: false },
      { key: "organ", label: "Organ rozpatrujący", required: true, nullable: false },
      { key: "wnioskodawca", label: "Wnioskodawca", required: true, nullable: false },
      { key: "kwota", label: "Kwota sporu (PLN)", required: false, nullable: true },
    ],
  },
  {
    id: "decyzja",
    name: "Decyzja administracyjna",
    description: "Decyzja organu pierwszej instancji.",
    fields: [
      { key: "sygnatura", label: "Sygnatura sprawy", required: true, nullable: false },
      { key: "data_decyzji", label: "Data decyzji", required: true, nullable: false },
      { key: "organ", label: "Organ wydający", required: true, nullable: false },
      { key: "rozstrzygniecie", label: "Rozstrzygnięcie", required: true, nullable: false },
    ],
  },
  {
    id: "pelnomocnictwo",
    name: "Pełnomocnictwo",
    description: "Upoważnienie do działania w imieniu strony.",
    fields: [
      { key: "mocodawca", label: "Mocodawca", required: true, nullable: false },
      { key: "pelnomocnik", label: "Pełnomocnik", required: true, nullable: false },
      { key: "zakres", label: "Zakres", required: false, nullable: true },
    ],
  },
];

const ev = (id: string, fieldKey: string, page: number, quote: string, y: number, source: "text" | "ocr" = "text", confidence = 0.96): Evidence => ({
  id,
  fieldKey,
  page,
  quote,
  box: { x: 0.12, y, w: 0.6, h: 0.035 },
  confidence,
  source,
});
const f = (key: string, label: string, value: Field["value"], evidenceIds: string[], state: Field["state"] = "ok"): Field => ({ key, label, value, evidenceIds, state });

const base = {
  sizeKb: 220,
  batchId: "batch-1",
  errorCode: null,
  candidates: [] as string[],
  reasons: [] as DocumentRecord["reasons"],
  evidence: [] as Evidence[],
  fields: [] as Field[],
  pageText: ["Treść strony 1 (dane syntetyczne)."],
};

export function seedDocuments(): DocumentRecord[] {
  const odw = (n: number, status: DocumentRecord["status"], extra: Partial<DocumentRecord> = {}): DocumentRecord => ({
    ...base,
    id: `doc-${n}`,
    fileName: `odwolanie-${String(n).padStart(3, "0")}.pdf`,
    pages: 3,
    status,
    classId: "odwolanie",
    className: "Odwołanie od decyzji",
    uploadedAt: `2026-11-2${(n % 5) + 1}T10:${String(10 + n).padStart(2, "0")}:00Z`,
    pageText: [
      "Odwołanie od decyzji z dnia 12.03.2026. Sygnatura: SKO-2026/114. Organ: Samorządowe Kolegium Odwoławcze.",
      "Wnioskodawca: Anna Kowalska (dane syntetyczne). Kwota sporu: 4 200,00 PLN.",
      "Podpis i data pisma: 20.03.2026.",
    ],
    evidence: [
      ev(`e${n}-1`, "sygnatura", 1, "Sygnatura: SKO-2026/114", 0.22),
      ev(`e${n}-2`, "organ", 1, "Samorządowe Kolegium Odwoławcze", 0.28),
      ev(`e${n}-3`, "wnioskodawca", 2, "Wnioskodawca: Anna Kowalska", 0.2),
      ev(`e${n}-4`, "data_pisma", 3, "20.03.2026", 0.4),
    ],
    fields: [
      f("sygnatura", "Sygnatura sprawy", "SKO-2026/114", [`e${n}-1`]),
      f("data_pisma", "Data pisma", "2026-03-20", [`e${n}-4`]),
      f("organ", "Organ rozpatrujący", "Samorządowe Kolegium Odwoławcze", [`e${n}-2`]),
      f("wnioskodawca", "Wnioskodawca", "Anna Kowalska", [`e${n}-3`]),
      f("kwota", "Kwota sporu (PLN)", 4200, [], "computed"),
    ],
    ...extra,
  });

  return [
    odw(1, "full"),
    odw(2, "full", { fileName: "odwolanie-wodociagi.pdf", pages: 5 }),
    odw(3, "partial", {
      reasons: ["missing_field", "low_confidence"],
      fields: [
        f("sygnatura", "Sygnatura sprawy", "SKO-2026/115", ["e3-1"]),
        f("data_pisma", "Data pisma", null, [], "missing"),
        f("organ", "Organ rozpatrujący", "Samorządowe Kolegium Odwoławcze", ["e3-2"]),
        f("wnioskodawca", "Wnioskodawca", "Jan Nowak", ["e3-3"]),
        f("kwota", "Kwota sporu (PLN)", null, [], "missing"),
      ],
    }),
    odw(4, "partial", { fileName: "skan-odwolanie.pdf", reasons: ["ocr_unavailable", "unreadable_scan"] }),
    odw(5, "ambiguous", { classId: null, className: null, candidates: ["Odwołanie od decyzji", "Decyzja administracyjna"], fields: [], evidence: [] }),
    odw(6, "error", { classId: null, className: null, errorCode: "FILE_MISSING", fields: [], evidence: [], pages: 0, fileName: "uszkodzony.pdf" }),
    odw(7, "foreign", { classId: null, className: null, fields: [], evidence: [], fileName: "menu-restauracji.pdf", pages: 1 }),
    odw(8, "multi", { classId: null, className: null, fields: [], evidence: [], fileName: "zbiorczy-skan.pdf", pages: 12 }),
    odw(9, "running", { classId: null, className: null, fields: [], evidence: [], progress: 40, fileName: "nowe-odwolanie.pdf" }),
    {
      ...odw(10, "full"),
      fileName: "decyzja-0412.pdf",
      classId: "decyzja",
      className: "Decyzja administracyjna",
      fields: [
        f("sygnatura", "Sygnatura sprawy", "UM-0412/2026", ["e10-1"]),
        f("data_decyzji", "Data decyzji", "2026-02-11", ["e10-4"]),
        f("organ", "Organ wydający", "Urząd Miasta", ["e10-2"]),
        f("rozstrzygniecie", "Rozstrzygnięcie", "Odmowa przyznania świadczenia", ["e10-3"]),
      ],
    },
    {
      ...odw(11, "full"),
      fileName: "pelnomocnictwo-kowalska.pdf",
      classId: "pelnomocnictwo",
      className: "Pełnomocnictwo",
      pages: 1,
      fields: [
        f("mocodawca", "Mocodawca", "Anna Kowalska", ["e11-1"]),
        f("pelnomocnik", "Pełnomocnik", "mec. Piotr Zieliński", ["e11-2"]),
        f("zakres", "Zakres", null, [], "missing"),
      ],
    },
    odw(12, "full", { fileName: "odwolanie-podatek.pdf" }),
  ];
}
