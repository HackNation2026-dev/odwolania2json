import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { DropZone } from "@/components/molecules/DropZone";
import { AddDocumentsView } from "./AddDocumentsView";

afterEach(() => setApiForTests(undefined));
function renderView() {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><AddDocumentsView /></QueryClientProvider>);
}
describe("DropZone and document selection", () => {
  it("accepts PDF metadata and skips DOCX on drop", () => {
    const onFiles = vi.fn();
    const view = render(<DropZone onFiles={onFiles} />);
    fireEvent.drop(view.container.firstChild!, { dataTransfer: { files: [new File(["pdf"], "appeal.pdf", { type: "application/pdf" }), new File(["docx"], "notes.docx", { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" })] } });
    expect(onFiles).toHaveBeenCalledWith([{ name: "appeal.pdf", sizeKb: 3 / 1024, type: "application/pdf" }], ["notes.docx: to nie jest PDF — pominięto."]);
  });
  it("shows skipped DOCX message and allows PDF removal while analysis is blocked without key", async () => {
    setApiForTests(createMockClient({ latencyMs: 0 }));
    renderView();
    await userEvent.setup({ applyAccept: false }).upload(screen.getByLabelText("Pliki PDF"), [new File(["pdf"], "appeal.pdf", { type: "application/pdf" }), new File(["docx"], "notes.docx")]);
    expect(screen.getByText(/notes\.docx: to nie jest PDF — pominięto\./)).toBeVisible();
    expect(screen.getByRole("button", { name: "Uruchom analizę" })).toBeDisabled();
    expect(await screen.findByRole("link", { name: "Skonfiguruj klucz" })).toHaveAttribute("href", "/klucz");
    await userEvent.click(screen.getByRole("button", { name: "Usuń appeal.pdf" }));
    expect(screen.getByRole("heading", { name: "Wybrane pliki (0)" })).toBeVisible();
  });
  it("sends metadata only and refreshes progress until completion", async () => {
    const api = createMockClient({ latencyMs: 10 });
    await api.saveKey({ value: "fake-key", persist: false });
    const add = vi.spyOn(api, "addDocuments");
    setApiForTests(api);
    renderView();
    await userEvent.upload(screen.getByLabelText("Pliki PDF"), new File(["pdf"], "appeal.pdf", { type: "application/pdf" }));
    await screen.findByText("Konfiguracja klas:", { exact: false });
    await userEvent.click(screen.getByRole("button", { name: "Uruchom analizę" }));
    expect(await screen.findByRole("heading", { name: "Analiza w toku" })).toBeVisible();
    expect(add).toHaveBeenCalledWith([{ name: "appeal.pdf", sizeKb: 3 / 1024, type: "application/pdf" }]);
    expect(await screen.findByRole("link", { name: "Przejdź do dokumentów" }, { timeout: 4000 })).toBeVisible();
    expect(within(screen.getByRole("region", { name: "Postęp analizy" })).getByText("Przetworzono 1 z 1 dokumentów")).toBeVisible();
  });
});
