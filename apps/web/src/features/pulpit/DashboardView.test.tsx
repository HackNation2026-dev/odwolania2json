import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { DashboardView } from "./DashboardView";

afterEach(() => setApiForTests(undefined));
describe("DashboardView", () => {
  it("renders real dashboard counts, recent documents and key warning", async () => {
    const api = createMockClient({ latencyMs: 0 });
    setApiForTests(api);
    const data = await api.getDashboard();
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><DashboardView /></QueryClientProvider>);
    expect(await screen.findByRole("link", { name: "Skonfiguruj klucz" })).toHaveAttribute("href", "/klucz");
    expect(await screen.findByRole("link", { name: new RegExp(`${data.byStatus.full}.*Pełny`) })).toHaveAttribute("href", "/dokumenty?status=full");
    expect(screen.getAllByText(data.recent[0]!.fileName).length).toBeGreaterThan(0);
  });
  it("hides key warning after configuration", async () => {
    const api = createMockClient({ latencyMs: 0 });
    await api.saveKey({ value: "fake-key", persist: false });
    setApiForTests(api);
    render(<QueryClientProvider client={new QueryClient()}><DashboardView /></QueryClientProvider>);
    await screen.findByRole("region", { name: "Liczniki dokumentów" });
    expect(screen.queryByRole("link", { name: "Skonfiguruj klucz" })).not.toBeInTheDocument();
  });
  it("renders an empty state with the real mock returning an empty session", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const initial = await api.getDashboard();
    setApiForTests({ ...api, getDashboard: async () => ({ ...initial, total: 0, byStatus: Object.fromEntries(Object.keys(initial.byStatus).map(status => [status, 0])) as typeof initial.byStatus, recent: [] }) });
    render(<QueryClientProvider client={new QueryClient()}><DashboardView /></QueryClientProvider>);
    expect(await screen.findByText("Nie masz jeszcze żadnych analiz.")).toBeVisible();
  });
});
