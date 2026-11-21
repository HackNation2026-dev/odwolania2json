import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { documentStatus } from "@/lib/api/schemas";
import { HowItWorksView } from "./HowItWorksView";
import userEvent from "@testing-library/user-event";

afterEach(() => setApiForTests(undefined));
describe("HowItWorksView", () => {
  it("explains all six stages, every API status and strict export rules", async () => {
    setApiForTests(createMockClient({ latencyMs: 0 }));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { container } = render(<QueryClientProvider client={client}><HowItWorksView /></QueryClientProvider>);
    expect(container.querySelectorAll("ol > li")).toHaveLength(6);
    for (const status of documentStatus.options) expect(container.querySelector(`[data-status="${status}"]`)).toBeVisible();
    expect(screen.getByRole("heading", { name: /Wariant A eksportu/ })).toBeVisible();
    expect(screen.getByText(/brak zastępczego/)).toBeVisible();
    expect(screen.getByText(/Przy 401 lub 403/)).toBeVisible();
    expect(screen.getByRole("link", { name: /Sprawdź konfigurację/ })).toHaveAttribute("href", "/ustawienia");
    expect(screen.getByText(/To tryb demonstracyjny bez logowania i backendu/)).toBeVisible();
    expect(await screen.findByRole("heading", { name: "MiniMax-M3.1-Flash-Preview" })).toBeVisible();
    expect(screen.getByText(/Nie ustalono największego modelu/)).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Sprawdź ponownie" }));
    expect(await screen.findByText(/Kontrola demonstracyjna zakończona/)).toBeVisible();
  });
});
