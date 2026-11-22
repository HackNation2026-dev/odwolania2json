import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
function view(node: React.ReactNode) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      {node}
    </QueryClientProvider>,
  );
}
afterEach(() => setApiForTests(undefined));
import { BatchBrowser } from "./BatchBrowser";
import { emptyFilters } from "./filters";
it("groups the selected batch and exposes E2 restrictions", async () => {
  const api = createMockClient({ latencyMs: 0 });
  setApiForTests(api);
  const documents = await api.listDocuments();
  const onChange = vi.fn();
  view(
    <BatchBrowser
      documents={documents}
      filters={{ ...emptyFilters, partia: "B-01" }}
      onChange={onChange}
    />,
  );
  expect(
    await screen.findByRole("cell", { name: "Katalog główny" }),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Pobierz dowody partii · E2" }),
  ).toBeDisabled();
  await userEvent.selectOptions(screen.getByLabelText("Partia"), "przyklad_01");
  expect(onChange).toHaveBeenCalledWith(
    expect.objectContaining({
      partia: "przyklad_01",
      documentIds: expect.arrayContaining(["doc-1"]),
    }),
  );
});
