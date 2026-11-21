import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { SystemInfoCard } from "./SystemInfoCard";

afterEach(() => setApiForTests(undefined));
it("explains unavailable OCR without declaring foreign documents or readiness", async () => {
  const api = createMockClient({ latencyMs: 0 });
  const info = await api.getSystemInfo();
  setApiForTests({ ...api, getSystemInfo: async () => ({ ...info, ocr: { ...info.ocr, mode: "unavailable" } }) });
  render(<QueryClientProvider client={new QueryClient()}><SystemInfoCard /></QueryClientProvider>);
  expect(await screen.findByText(/× OCR niedostępny/)).toHaveTextContent("Nie oznaczamy dokumentu jako obcego");
  expect(screen.getByText("Nie sprawdzono gotowości")).toBeVisible();
  expect(screen.queryByText(/^Model gotowy:/)).not.toBeInTheDocument();
});
