import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { keys } from "@/lib/api/hooks";
import { DocumentView } from "./DocumentView";

vi.mock("@/components/organisms/PdfViewer", () => ({ PdfViewer: () => null }));
vi.mock("@/lib/api/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/hooks")>();
  return {
    ...actual,
    useExportDecision: (id: string) => ({
      ...actual.useExportDecision(id),
      isFetching: true,
    }),
  };
});
// Odtworzenie wyścigu: stopka przyjęła kliknięcie jako aktywna, a rodzic widzi już odświeżanie decyzji.
vi.mock("./DocumentFooter", () => ({
  DocumentFooter: ({ downloadJson }: { downloadJson: () => void }) => (
    <button onClick={downloadJson}>Pobierz JSON</button>
  ),
}));
afterEach(() => {
  cleanup();
  setApiForTests(undefined);
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
it("exports an accepted click through API validation while the decision is refreshing", async () => {
  const api = createMockClient({ latencyMs: 0 });
  const exporting = vi.spyOn(api, "exportJson");
  setApiForTests(api);
  vi.stubGlobal(
    "URL",
    class extends URL {
      static createObjectURL = vi.fn(() => "blob:document-export");
      static revokeObjectURL = vi.fn();
    },
  );
  let downloadedName = "";
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
    this: HTMLAnchorElement,
  ) {
    downloadedName = this.download;
  });
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <DocumentView id="doc-3" />
    </QueryClientProvider>,
  );
  await screen.findByRole("heading", { name: "odwolanie-003.pdf" });
  await waitFor(() =>
    expect(client.getQueryData(keys.exportDecision("doc-3"))).toMatchObject({
      allowed: true,
    }),
  );
  await userEvent.click(screen.getByRole("button", { name: "Pobierz JSON" }));
  await waitFor(() => expect(exporting).toHaveBeenCalledWith("doc-3"));
  await waitFor(() => expect(downloadedName).toBe("odwolanie-003.json"));
});

it("keeps API validation authoritative when a stale control accepts a blocked export", async () => {
  const api = createMockClient({ latencyMs: 0 });
  const exporting = vi.spyOn(api, "exportJson");
  const clicking = vi.spyOn(HTMLAnchorElement.prototype, "click");
  setApiForTests(api);
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <DocumentView id="doc-6" />
    </QueryClientProvider>,
  );
  await screen.findByRole("heading", { name: "timeout.pdf" });
  await userEvent.click(screen.getByRole("button", { name: "Pobierz JSON" }));
  await waitFor(() => expect(exporting).toHaveBeenCalledWith("doc-6"));
  await expect(exporting.mock.results[0]!.value).rejects.toThrow();
  expect(clicking).not.toHaveBeenCalled();
});
