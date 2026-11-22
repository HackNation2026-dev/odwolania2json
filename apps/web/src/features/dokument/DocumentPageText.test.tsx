import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { seedDocuments } from "@/lib/api/mock/data";
import { extractPageText } from "@/components/organisms/PdfViewer";
import { DocumentPageText } from "./DocumentPageText";
import { DocumentDiagnosis } from "./DocumentDiagnosis";

vi.mock("@/components/organisms/PdfViewer", () => ({
  extractPageText: vi.fn(),
}));
beforeEach(() => {
  setApiForTests(createMockClient({ latencyMs: 0 }));
  vi.mocked(extractPageText)
    .mockReset()
    .mockResolvedValue("Tekst odczytany z prawdziwego PDF");
});
afterEach(() => {
  cleanup();
  setApiForTests(undefined);
});
function mount(node: React.ReactNode) {
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
describe("document text and diagnosis", () => {
  it("reads the selected PDF page through extractPageText", async () => {
    mount(
      <DocumentPageText
        doc={seedDocuments()[0]!}
        file="/demo-pdf/odwolanie.pdf"
        page={1}
        select={vi.fn()}
      />,
    );
    expect(
      await screen.findByText("Tekst odczytany z prawdziwego PDF"),
    ).toBeVisible();
    expect(extractPageText).toHaveBeenCalledWith("/demo-pdf/odwolanie.pdf", 1);
  });
  it("keeps unread pages distinct from absent information", async () => {
    mount(
      <DocumentPageText
        doc={seedDocuments()[2]!}
        file="/demo-pdf/odwolanie.pdf"
        page={2}
        select={vi.fn()}
      />,
    );
    expect(await screen.findByText("Nie przetworzono strony")).toBeVisible();
    expect(
      screen.getByText(/Brak odczytu nie oznacza braku informacji/),
    ).toBeVisible();
  });
  it("retries a failed text extraction", async () => {
    vi.mocked(extractPageText).mockRejectedValueOnce(new Error("offline"));
    mount(
      <DocumentPageText
        doc={seedDocuments()[0]!}
        file="/demo-pdf/odwolanie.pdf"
        page={1}
        select={vi.fn()}
      />,
    );
    await screen.findByText("Nie udało się odczytać tekstu strony");
    await userEvent.click(
      screen.getByRole("button", { name: /Ponów|Spróbuj ponownie/ }),
    );
    expect(
      await screen.findByText("Tekst odczytany z prawdziwego PDF"),
    ).toBeVisible();
  });
  it("navigates document, page and region diagnosis in a focus trapped drawer", async () => {
    mount(<DocumentDiagnosis id="doc-3" className="Odwołanie do KIO" />);
    await userEvent.click(
      screen.getByRole("button", {
        name: "Diagnoza dokumentu, stron i regionów",
      }),
    );
    await screen.findByRole("tab", { name: "Region" });
    await userEvent.click(screen.getByRole("tab", { name: "Region" }));
    await userEvent.selectOptions(screen.getByLabelText("Strona regionu"), "2");
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Region" }),
      "R3",
    );
    expect(await screen.findByText("zla_warstwa_ocr")).toBeVisible();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
