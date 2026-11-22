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
import { AddDocumentsView } from "./AddDocumentsView";
import { PipelineProgress } from "./PipelineProgress";
import { SystemReadiness } from "./SystemReadiness";
it("requires an explicit collision choice and cancellation preserves the selection", async () => {
  const api = createMockClient({ latencyMs: 0 });
  await api.saveKey({ value: "synthetic", persist: false });
  const submit = vi.spyOn(api, "addResolvedDocuments");
  setApiForTests(api);
  view(<AddDocumentsView />);
  await screen.findByText(/Konfiguracja klas:/);
  await userEvent.upload(
    screen.getByLabelText("Pliki PDF"),
    new File(["different"], "odwolanie.pdf", { type: "application/pdf" }),
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Uruchom analizę" }),
  );
  expect(
    await screen.findByRole("dialog", { name: "Kolizja ścieżki" }),
  ).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Anuluj" }));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(
    screen.getByRole("heading", { name: "Wybrane pliki (1)" }),
  ).toBeVisible();
  expect(submit).not.toHaveBeenCalled();
  await userEvent.click(
    screen.getByRole("button", { name: "Uruchom analizę" }),
  );
  await userEvent.click(
    await screen.findByRole("button", { name: "Nowa wersja dokumentu" }),
  );
  expect(
    await screen.findByRole("heading", { name: "Analiza zakończona" }),
  ).toBeVisible();
  expect(submit).toHaveBeenCalledWith(
    expect.objectContaining({ choice: "version" }),
  );
});
it("blocks analysis when no class configuration is active", async () => {
  const api = createMockClient({ latencyMs: 0 });
  await api.saveKey({ value: "synthetic", persist: false });
  setApiForTests({ ...api, listClasses: async () => [] });
  view(<AddDocumentsView />);
  expect(await screen.findByText(/Brak poprawnego zestawu klas/)).toBeVisible();
  await userEvent.upload(
    screen.getByLabelText("Pliki PDF"),
    new File(["pdf"], "new.pdf", { type: "application/pdf" }),
  );
  expect(
    screen.getByRole("button", { name: "Uruchom analizę" }),
  ).toBeDisabled();
});
it("renders all pipeline stages and final counts from the model", async () => {
  setApiForTests(createMockClient({ latencyMs: 0 }));
  view(<PipelineProgress documentId="doc-1" fileName="odwolanie.pdf" />);
  await userEvent.click(screen.getByText("Etapy potoku: odwolanie.pdf"));
  expect(await screen.findByText(/E · Odczyt i diagnoza/)).toBeVisible();
  expect(screen.getByText(/T5 · Normalizacja/)).toBeVisible();
  expect(screen.getByText(/Eksport · Eksport wyniku/)).toBeVisible();
  expect(screen.getByText(/Strony: 3 · OCR: 0/)).toBeVisible();
});
it("uses the unavailable OCR state from system metadata", async () => {
  const api = createMockClient({ latencyMs: 0 });
  const info = await api.getSystemInfo();
  setApiForTests({
    ...api,
    getSystemInfo: async () => ({
      ...info,
      ocr: { ...info.ocr, mode: "unavailable" },
    }),
  });
  view(<SystemReadiness />);
  expect(await screen.findByRole("alert")).toHaveTextContent("OCR niedostępny");
});
