import { ApiError, type ApiClient } from "../client";
import type {
  AuditEvent,
  AuditQuery,
  RetentionSettings,
  SystemInfo,
} from "../schemas";

const events: AuditEvent[] = [
  {
    id: "sys-5",
    occurredAt: "2026-10-14T09:12:00+02:00",
    user: "Marta Zielińska",
    type: "correction",
    description: "Korekta",
    object: "odwolanie.pdf · v2",
    detail:
      "Pole Numer TED. Było: •••••••• / Jest: •••••••• (maskowane przez serwer).",
  },
  {
    id: "sys-4",
    occurredAt: "2026-10-14T09:15:00+02:00",
    user: "Jan Nowak",
    type: "reveal",
    description: "Odsłonięcie",
    object: "odwolanie.pdf · v2",
    detail:
      "Odsłonięto pole Odwolujacy.pesel. Wartość nie jest zapisana w dzienniku.",
  },
  {
    id: "sys-3",
    occurredAt: "2026-10-14T09:40:00+02:00",
    user: "Anna Kowalska",
    type: "export",
    description: "Eksport",
    object: "odwolanie.pdf · v1",
    detail: "Pobrano odwolanie.json · v1.",
  },
  {
    id: "sys-2",
    occurredAt: "2026-10-14T10:02:00+02:00",
    user: "Administrator",
    type: "configuration",
    description: "Aktywacja YAML",
    object: "Zestaw klas",
    detail: "Zestaw v1 → v2. Nowe analizy użyją v2.",
  },
  {
    id: "sys-1",
    occurredAt: "2026-10-14T10:20:00+02:00",
    user: "Jan Nowak",
    type: "denied",
    description: "Odmowa odsłonięcia",
    object: "odwolanie.pdf · v2",
    detail: "Brak uprawnienia »Dane osobowe«. Wartość nie została ujawniona.",
  },
];

function filterEvents(query: AuditQuery) {
  return events.filter(
    (event) =>
      (!query.type || event.type === query.type) &&
      (!query.user ||
        event.user
          .toLocaleLowerCase("pl")
          .includes(query.user.toLocaleLowerCase("pl"))) &&
      (!query.date || event.occurredAt.startsWith(query.date)) &&
      (!query.dateFrom || event.occurredAt.slice(0, 10) >= query.dateFrom) &&
      (!query.dateTo || event.occurredAt.slice(0, 10) <= query.dateTo) &&
      (!query.object ||
        event.object
          .toLocaleLowerCase("pl")
          .includes(query.object.toLocaleLowerCase("pl"))),
  );
}

export function createMockSysMethods(
  wait: <T>(value: T) => Promise<T>,
  getSystemInfo: () => Promise<SystemInfo>,
): Pick<
  ApiClient,
  | "getRetentionSettings"
  | "saveRetention"
  | "listAuditEvents"
  | "exportAuditCsv"
  | "getReadiness"
> {
  let retention: RetentionSettings = {
    days: 30,
    minDays: 1,
    maxDays: 365,
    affectedCases: 0,
  };
  return {
    getRetentionSettings: () => wait(retention),
    async saveRetention(days) {
      if (
        !Number.isInteger(days) ||
        days < retention.minDays ||
        days > retention.maxDays
      ) {
        throw new ApiError(
          "RETENTION_RANGE",
          `Podaj liczbę dni z zakresu ${retention.minDays}–${retention.maxDays}.`,
        );
      }
      retention = { ...retention, days };
      return wait(retention);
    },
    listAuditEvents: (query = {}) => wait(filterEvents(query)),
    exportAuditCsv: (query = {}) => {
      const quote = (value: string) => `"${value.replaceAll('"', '""')}"`;
      const rows = filterEvents(query).map((event) => [
        event.occurredAt,
        event.user,
        event.description,
        event.object,
        event.detail,
      ]);
      const csv = [
        ["Czas", "Użytkownik", "Zdarzenie", "Obiekt", "Szczegóły"],
        ...rows,
      ]
        .map((row) => row.map(quote).join(";"))
        .join("\r\n");
      return wait({ fileName: "dziennik-demo.csv", csv: `\uFEFF${csv}` });
    },
    getReadiness: getSystemInfo,
  };
}
