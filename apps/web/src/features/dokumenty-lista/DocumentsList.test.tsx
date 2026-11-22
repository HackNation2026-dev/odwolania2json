import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { DocumentsListContent, VIEW_STORAGE_KEY } from "./DocumentsList";
import { emptyFilters } from "./filters";

function Harness() {
  const [filters, setFilters] = useState(emptyFilters);
  return <DocumentsListContent filters={filters} onChange={setFilters} />;
}
function setup(client = createMockClient({ latencyMs: 0 })) {
  setApiForTests(client);
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <Harness />
    </QueryClientProvider>,
  );
}
afterEach(() => {
  setApiForTests(undefined);
  localStorage.clear();
});
describe("document list with real mock", () => {
  it("filters status, search and class, sorts, changes view and clears empty results", async () => {
    setup();
    expect(
      screen.getByRole("status", { name: "Ładowanie dokumentów" }),
    ).toBeInTheDocument();
    await screen.findByTestId("document-gallery");
    fireEvent.click(screen.getByText(/^Status.*▾/));
    fireEvent.click(screen.getByRole("checkbox", { name: /Pełny/ }));
    fireEvent.click(screen.getByRole("button", { name: "Zastosuj (1)" }));
    expect(screen.getByRole("status")).toHaveTextContent(
      "Znaleziono 5 dokumentów",
    );
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "wodociagi" },
    });
    expect(
      within(screen.getByTestId("document-gallery")).getAllByRole("link"),
    ).toHaveLength(1);
    expect(
      screen.getByRole("link", { name: /odwolanie-wodociagi/ }),
    ).toHaveAttribute("href", "/dokumenty/doc-2");
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "" } });
    fireEvent.change(
      screen.getByRole("combobox", { name: "Klasa dokumentu" }),
      { target: { value: "przelew" } },
    );
    expect(
      within(screen.getByTestId("document-gallery")).getAllByRole("link"),
    ).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Wyczyść filtry" }));
    fireEvent.change(screen.getByRole("combobox", { name: "Sortowanie" }), {
      target: { value: "name" },
    });
    expect(
      within(screen.getByTestId("document-gallery")).getAllByRole("link")[0],
    ).toHaveTextContent("menu-restauracji.pdf");
    fireEvent.click(screen.getByRole("button", { name: /Lista/ }));
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(localStorage.getItem(VIEW_STORAGE_KEY)).toBe("tabela");
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "nieistniejacy" },
    });
    expect(
      screen.getByText("Brak dokumentów spełniających kryteria"),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getAllByRole("button", { name: "Wyczyść filtry" })[1]!,
    );
    expect(screen.getByRole("table")).toBeInTheDocument();
  });
  it("shows error and retries the list", async () => {
    const client = createMockClient({ latencyMs: 0 });
    let failed = true;
    setup({
      ...client,
      listDocuments: () =>
        failed ? Promise.reject(new Error("offline")) : client.listDocuments(),
    });
    await screen.findByRole("alert");
    failed = false;
    fireEvent.click(screen.getByRole("button", { name: "Spróbuj ponownie" }));
    await screen.findByTestId("document-gallery");
  });
  it("defaults to table below seven documents and displays an empty session", async () => {
    const client = createMockClient({ latencyMs: 0 });
    const docs = await client.listDocuments();
    const view = setup({
      ...client,
      listDocuments: async () => docs.slice(0, 6),
    });
    await screen.findByRole("table");
    view.unmount();
    setup({ ...client, listDocuments: async () => [] });
    await screen.findByText("Nie dodano jeszcze dokumentów");
    await waitFor(() =>
      expect(screen.queryByRole("table")).not.toBeInTheDocument(),
    );
  });
});
