import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { ReadinessView } from "./ReadinessView";

function mount(api = createMockClient({ latencyMs: 0 })) {
  setApiForTests(api);
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <ReadinessView />
    </QueryClientProvider>,
  );
}
afterEach(() => setApiForTests(undefined));
it("loads readiness metadata and runs an explicitly simulated check", async () => {
  mount();
  expect(screen.getByRole("status")).toHaveTextContent("Wczytywanie modeli");
  expect(
    await screen.findByRole("heading", { name: "MiniMax-M3.1-Flash-Preview" }),
  ).toBeVisible();
  expect(screen.getByText(/Kraj firmy:/)).toHaveTextContent("Nie podano");
  await userEvent.click(
    screen.getByRole("button", { name: "Sprawdź ponownie" }),
  );
  expect(
    await screen.findByText(/Kontrola demonstracyjna zakończona/),
  ).toBeVisible();
});
it("retries a readiness read and explains missing models", async () => {
  const api = createMockClient({ latencyMs: 0 });
  const info = await api.getSystemInfo();
  let fail = true;
  mount({
    ...api,
    getReadiness: async () => {
      if (fail) throw new Error("Awaria");
      return { ...info, models: [] };
    },
  });
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Nie udało się wczytać modeli",
  );
  fail = false;
  await userEvent.click(
    screen.getByRole("button", { name: "Spróbuj ponownie" }),
  );
  expect(
    await screen.findByText("Brak skonfigurowanych modeli."),
  ).toBeVisible();
});
