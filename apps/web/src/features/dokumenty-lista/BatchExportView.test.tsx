import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
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
import { BatchExportView } from "./BatchExportView";
it("shows three included and three omitted entries from the real mock", async () => {
  setApiForTests(createMockClient({ latencyMs: 0 }));
  view(<BatchExportView batchId="B-01" />);
  expect(
    await screen.findByRole(
      "heading",
      { name: "Uwzględnione (3)" },
      { timeout: 10000 },
    ),
  ).toBeVisible();
  expect(screen.getByRole("heading", { name: "Pominięte (3)" })).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Pobierz 3 wyniki" }),
  ).toBeEnabled();
  expect(screen.getByText(/zastępczy.*dla awarii nie powstaje/)).toBeVisible();
});
it("offers retry on a missing batch", async () => {
  setApiForTests(createMockClient({ latencyMs: 0 }));
  view(<BatchExportView batchId="missing" />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Nie udało się przygotować",
  );
  expect(
    screen.getByRole("button", { name: "Spróbuj ponownie" }),
  ).toBeVisible();
});
it("shows an empty plan without offering an empty archive", async () => {
  const api = createMockClient({ latencyMs: 0 });
  setApiForTests({
    ...api,
    getBatchExportPlan: async () => ({
      batchId: "empty",
      included: [],
      omitted: [],
    }),
  });
  view(<BatchExportView batchId="empty" />);
  expect(
    await screen.findByRole("heading", { name: "Brak wyników do pobrania" }),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Pobierz 0 wyniki" }),
  ).toBeDisabled();
});
