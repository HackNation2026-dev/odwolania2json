import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { DocumentView } from "./DocumentView";

vi.mock("@/components/organisms/PdfViewer", () => ({
  PdfViewer: ({
    highlights = [],
    onHighlightClick,
  }: {
    highlights?: { id: string; label?: string; active?: boolean }[];
    onHighlightClick?: (id: string) => void;
  }) => (
    <div aria-label="Renderer PDF">
      {highlights.map((item) => (
        <button
          key={item.id}
          aria-pressed={item.active}
          onClick={() => onHighlightClick?.(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  ),
  extractPageText: vi.fn().mockResolvedValue(""),
}));

beforeEach(() => setApiForTests(createMockClient({ latencyMs: 0 })));
afterEach(() => {
  cleanup();
  setApiForTests(undefined);
});
function view(id: string, tab?: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <DocumentView id={id} tab={tab} />
    </QueryClientProvider>,
  );
}
describe("document review with real mock", () => {
  it.each([
    ["doc-1", "Pełny", true],
    ["doc-3", "Częściowy", true],
    ["doc-4", "Częściowy", true],
    ["doc-5", "Niejednoznaczny", false],
    ["doc-6", "Błąd techniczny", false],
    ["doc-7", "Obcy", true],
    ["doc-8", "Wiele dokumentów", false],
    ["doc-9", "W toku", false],
  ])("renders %s status and export decision", async (id, label, allowed) => {
    view(id);
    expect(
      await screen.findByText(label, { selector: "[data-status]" }),
    ).toBeVisible();
    await screen.findByText(
      allowed ? "✓ Eksport dozwolony" : "! Eksport zablokowany",
    );
    expect(screen.getByRole("button", { name: "Pobierz JSON" })).toHaveProperty(
      "disabled",
      !allowed,
    );

    if (id === "doc-9")
      expect(screen.getByRole("progressbar")).toHaveAttribute("value", "40");
  });
  it("corrects a nullable field without hiding remaining gaps", async () => {
    view("doc-3");
    const user = userEvent.setup();
    await user.click(
      await screen.findByRole("button", { name: "Edytuj Data odwołania" }),
    );
    await user.type(
      screen.getByLabelText("Nowa wartość: Data odwołania"),
      "2026-02-30",
    );
    await user.click(screen.getByRole("button", { name: "Zapisz" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "prawidłową datę",
    );
    await user.clear(screen.getByLabelText("Nowa wartość: Data odwołania"));
    await user.type(
      screen.getByLabelText("Nowa wartość: Data odwołania"),
      "2026-03-20",
    );
    await user.click(screen.getByRole("button", { name: "Zapisz" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Pobierz JSON" }),
      ).toBeEnabled(),
    );
    expect(
      screen.getByText("Częściowy", { selector: "[data-status]" }),
    ).toBeVisible();
    expect(
      screen.getAllByText("brak (null)", { exact: true }).length,
    ).toBeGreaterThan(0);
  });
  it("retries error and replaces the failed state", async () => {
    view("doc-6");
    const user = userEvent.setup();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Wynik ekstrakcji nie został zapisany",
    );
    await user.click(screen.getByRole("button", { name: "Ponów" }));
    expect(
      await screen.findByText("Pełny", { selector: "[data-status]" }),
    ).toBeVisible();
  });
  it("reextracts an ambiguous document with the selected contract", async () => {
    view("doc-5");
    const user = userEvent.setup();
    await user.click(
      await screen.findByRole("button", { name: "Wybierz: Odwołanie do KIO" }),
    );
    expect(
      await screen.findByText("Pełny", { selector: "[data-status]" }),
    ).toBeVisible();
    expect(
      await screen.findByRole("button", { name: "Edytuj Data odwołania" }),
    ).toBeVisible();
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Pobierz JSON" }),
      ).toBeEnabled(),
    );
  });
  it("synchronizes field selection, page navigation and evidence", async () => {
    view("doc-1");
    const user = userEvent.setup();
    await user.click(
      await screen.findByRole("button", {
        name: "Pokaż dowód: Data zaskarżonej czynności",
      }),
    );
    expect(screen.getByText("Strona 3 z 3")).toBeVisible();
    expect(screen.getByText(/Wybrany dowód: strona 3/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Poprzednia strona" }));
    expect(screen.getByText("Strona 2 z 3")).toBeVisible();
  });
  it("does not show substitute JSON after failure", async () => {
    view("doc-6", "json");
    expect(await screen.findByText(/Brak ocenianego JSON/)).toBeVisible();
    expect(screen.queryByLabelText("JSON dokumentu")).not.toBeInTheDocument();
  });
  it("shows evidence separately from JSON and provides report", async () => {
    view("doc-1", "dowody");
    expect(
      await screen.findByRole("button", { name: "Pobierz osobny raport" }),
    ).toBeVisible();
    expect(screen.getAllByRole("row")).toHaveLength(22);
  });
  it.each([
    ["doc-10", "Data operacji"],
    ["doc-11", "PESEL"],
  ])("binds %s fields through evidence identifiers", async (id, label) => {
    view(id);
    const user = userEvent.setup();
    const field = await screen.findByRole("button", {
      name: `Pokaż dowód: ${label}`,
    });
    await user.click(field);
    expect(field).toHaveAttribute("aria-pressed", "true");
  });
  it("shows actual OCR source and low quality warning in page text", async () => {
    view("doc-4");
    const user = userEvent.setup();
    await user.click(
      await screen.findByRole("button", { name: "Tekst strony" }),
    );
    expect(
      await screen.findByRole("heading", {
        name: "Strona 1 · Skan — tekst z OCR",
      }),
    ).toBeVisible();
    expect(screen.getByText(/Niska jakość odczytu OCR/)).toBeVisible();
  });
  it("renders application style 404 for unknown id", async () => {
    view("unknown");
    expect(
      await screen.findByRole("heading", { name: "Nie znaleziono strony" }),
    ).toBeVisible();
    expect(within(screen.getByRole("alert")).getByText("404")).toBeVisible();
  });
});
