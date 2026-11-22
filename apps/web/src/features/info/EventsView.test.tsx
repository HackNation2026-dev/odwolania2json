import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { EventsView } from "./EventsView";

function mount(api = createMockClient({ latencyMs: 0 })) {
  setApiForTests(api);
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <EventsView />
    </QueryClientProvider>,
  );
}
afterEach(() => setApiForTests(undefined));
describe("EventsView", () => {
  it("loads masked events, filters and clears the selected filters", async () => {
    mount();
    const table = await screen.findByRole("table", {
      name: "Syntetyczny dziennik zdarzeń",
    });
    expect(within(table).getAllByRole("row")).toHaveLength(6);
    expect(screen.getByRole("status", { name: "Liczba zdarzeń" })).toHaveTextContent("Liczba zdarzeń: 5");
    expect(within(table).getByText(/Było: ••••••••/)).toBeVisible();
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Rodzaj zdarzenia" }),
      "reveal",
    );
    expect(
      await screen.findByText(/Wartość nie jest zapisana w dzienniku/),
    ).toBeVisible();
    expect(screen.getByRole("status", { name: "Liczba zdarzeń" })).toHaveTextContent("Liczba zdarzeń: 1");
    await userEvent.type(
      screen.getByRole("textbox", { name: "Użytkownik" }),
      "Nieznany",
    );
    expect(
      await screen.findByText("Brak zdarzeń spełniających kryteria."),
    ).toBeVisible();
    expect(screen.getByRole("status", { name: "Liczba zdarzeń" })).toHaveTextContent("Liczba zdarzeń: 0");
    await userEvent.click(
      screen.getByRole("button", { name: "Wyczyść filtry" }),
    );
    expect(await screen.findByText(/Było: ••••••••/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Eksportuj CSV" })).toBeEnabled();
  });
  it("explains an empty event list", async () => {
    mount({
      ...createMockClient({ latencyMs: 0 }),
      listAuditEvents: async () => [],
    });
    expect(
      await screen.findByText("Brak zdarzeń w tym zakresie."),
    ).toBeVisible();
  });
  it("reports an export failure without providing a replacement file", async () => {
    mount({
      ...createMockClient({ latencyMs: 0 }),
      exportAuditCsv: async () => {
        throw new Error("Awaria eksportu");
      },
    });
    await screen.findByRole("table");
    await userEvent.click(
      screen.getByRole("button", { name: "Eksportuj CSV" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Nie udało się przygotować CSV",
    );
    expect(screen.getByRole("button", { name: "Ponów" })).toBeEnabled();
  });
  it("retries a failed audit read", async () => {
    const api = createMockClient({ latencyMs: 0 });
    let fail = true;
    mount({
      ...api,
      listAuditEvents: async (query) => {
        if (fail) throw new Error("Brak połączenia");
        return api.listAuditEvents(query);
      },
    });
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Nie udało się wczytać dziennika",
    );
    fail = false;
    await userEvent.click(
      screen.getByRole("button", { name: "Spróbuj ponownie" }),
    );
    expect(await screen.findByRole("table")).toBeVisible();
  });
});
