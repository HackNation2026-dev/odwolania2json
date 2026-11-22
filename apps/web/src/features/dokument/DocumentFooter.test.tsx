import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { useExportDecision } from "@/lib/api/hooks";
import { DocumentFooter } from "./DocumentFooter";

afterEach(() => {
  cleanup();
  setApiForTests(undefined);
});
it("keeps an allowed download enabled across a background decision refresh", async () => {
  setApiForTests(createMockClient({ latencyMs: 0 }));
  const download = vi.fn();
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  function Footer({ refreshing }: { refreshing: boolean }) {
    const decision = useExportDecision("doc-3");
    return (
      <DocumentFooter
        id="doc-3"
        decision={{ ...decision, isFetching: refreshing }}
        activeTab="przeglad"
        downloading={false}
        failed={false}
        downloadJson={download}
        downloadEvidence={() => {}}
        message=""
      />
    );
  }
  const view = (refreshing: boolean) => (
    <QueryClientProvider client={client}>
      <Footer refreshing={refreshing} />
    </QueryClientProvider>
  );
  const { rerender } = render(view(false));
  const button = await screen.findByRole("button", { name: "Pobierz JSON" });
  await screen.findByText("✓ Eksport dozwolony");
  expect(button).toBeEnabled();
  rerender(view(true));
  expect(button).toBeEnabled();
  await userEvent.click(button);
  expect(download).toHaveBeenCalledOnce();
});
