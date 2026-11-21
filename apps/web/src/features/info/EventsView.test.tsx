import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { EventsView } from "./EventsView";

function mount(api = createMockClient({ latencyMs: 0 })) {
  setApiForTests(api);
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><EventsView /></QueryClientProvider>);
}
afterEach(() => setApiForTests(undefined));

describe("EventsView", () => {
  it("loads real mock events, filters and clears without exposing field values", async () => {
    mount();
    expect(screen.getByText("Wczytywanie zdarzeń…")).toBeVisible();
    const table = await screen.findByRole("table", { name: "Syntetyczny dziennik zdarzeń" });
    expect(within(table).getAllByRole("row")).toHaveLength(7);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Rodzaj zdarzenia" }), "export");
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    expect(screen.queryByText("Błąd OCR")).not.toBeInTheDocument();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Rodzaj zdarzenia" }), "configuration");
    expect(screen.getByRole("status")).toHaveTextContent("Brak zdarzeń spełniających kryteria");
    await userEvent.click(screen.getByRole("button", { name: "Wyczyść filtry" }));
    expect(screen.getByText("Korekta pola")).toBeVisible();
    expect(screen.getByText(/Było: •••; Jest: •••/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Eksportuj CSV (po MVP)" })).toBeDisabled();
  });
  it("explains an empty event list", async () => {
    mount({ ...createMockClient({ latencyMs: 0 }), listEvents: async () => [] });
    expect(await screen.findByText("Brak zdarzeń w tym zakresie.")).toBeVisible();
  });
  it("retries a failed read", async () => {
    const api = createMockClient({ latencyMs: 0 });
    let fail = true;
    mount({ ...api, listEvents: async () => { if (fail) throw new Error("Brak połączenia"); return api.listEvents(); } });
    expect(await screen.findByRole("alert")).toHaveTextContent("Nie udało się wczytać dziennika");
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Spróbuj ponownie" }));
    expect(await screen.findByRole("table")).toBeVisible();
  });
});
