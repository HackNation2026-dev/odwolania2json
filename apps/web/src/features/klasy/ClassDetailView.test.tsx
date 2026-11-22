import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { setApiForTests, type ApiClient } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { createClassMock, type ClassMockScenario } from "@/lib/api/mock/klasy";
import { ClassDetailView } from "./ClassDetailView";
import {
  ConfigurationError,
  configurationError,
  useClassConfiguration,
} from "./ConfigurationGuard";

function mount(
  scenario: ClassMockScenario = "ready",
  override: Partial<ApiClient> = {},
  id = "przelew",
) {
  const api = {
    ...createMockClient({ latencyMs: 0 }),
    ...createClassMock(async (value) => value, scenario),
    ...override,
  };
  setApiForTests(api);
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <ClassDetailView id={id} />
    </QueryClientProvider>,
  );
  return api;
}
afterEach(() => setApiForTests(undefined));

async function openTest() {
  await screen.findByRole("heading", {
    name: "Potwierdzenie przelewu",
    level: 1,
  });
  await userEvent.click(screen.getByRole("tab", { name: "Test" }));
}

describe("ClassDetailView", () => {
  it("loads fields, YAML and the generated preview", async () => {
    mount();
    expect(screen.getByText("Wczytywanie klasy…")).toBeVisible();
    await screen.findByRole("heading", { name: "Pola i reguły kontraktu" });
    await userEvent.click(screen.getByRole("tab", { name: "YAML" }));
    expect(
      screen.getByRole("region", { name: "przelew.yaml" }),
    ).toHaveTextContent("kwota");
    expect(
      screen.getByRole("link", { name: "Pobierz przelew.yaml" }),
    ).toHaveAttribute("download", "przelew.yaml");
    expect(screen.getByRole("button", { name: "Kopiuj" })).toBeVisible();
    await userEvent.click(
      screen.getByRole("tab", { name: "Podgląd formularza" }),
    );
    expect(
      screen.getByRole("heading", { name: "Podgląd formularza" }),
    ).toBeVisible();
  });

  it("invalidates a test after editing and blocks saving invalid drafts", async () => {
    mount("invalid");
    await openTest();
    expect(
      screen.getByRole("button", { name: "Zapisz i aktywuj wersję 2" }),
    ).toBeDisabled();
    await userEvent.click(
      screen.getByRole("button", { name: "Testuj wersję roboczą" }),
    );
    expect(
      await screen.findByText("Linia 14: brak normalizatora"),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Aktywuj zestaw" }),
    ).toBeDisabled();
    const editor = screen.getByRole("textbox", {
      name: /edycja demonstracyjna/,
    });
    const corrected = "id: przelew\npola:\n  - sciezka: oznaczenie_sprawy";
    fireEvent.change(editor, { target: { value: corrected } });
    await userEvent.click(
      screen.getByRole("button", { name: "Testuj wersję roboczą" }),
    );
    expect(await screen.findByText("Walidacja: poprawna")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Aktywuj zestaw" }),
    ).toBeEnabled();
    fireEvent.change(editor, { target: { value: `${corrected}\n# zmiana` } });
    expect(
      screen.getByText("Wynik poprzedniego testu jest nieaktualny"),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Aktywuj zestaw" }),
    ).toBeDisabled();
  });

  it("keeps the dialog open after failure and retries activation", async () => {
    mount("activation-error");
    await openTest();
    await userEvent.click(
      screen.getByRole("button", { name: "Testuj wersję roboczą" }),
    );
    await screen.findByText("Walidacja: poprawna");
    await userEvent.click(
      screen.getByRole("button", { name: "Aktywuj zestaw" }),
    );
    const dialog = screen.getByRole("dialog");
    expect(
      within(dialog).getByText(/dodano pole oznaczenie_sprawy/),
    ).toBeVisible();
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Aktywuj" }),
    );
    expect(await within(dialog).findByRole("alert")).toHaveTextContent(
      "Nie aktywowano. Nadal aktywny v1. Ponów",
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Ponów" }),
    );
    expect(await screen.findByText("Zestaw v2 aktywny")).toBeVisible();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText("wersja v2 · 7 pól")).toBeVisible();
  });

  it("prevents duplicate activation while pending", async () => {
    let resolve!: (
      value: Awaited<ReturnType<ApiClient["activateClassSet"]>>,
    ) => void;
    const activateClassSet = vi.fn(
      () =>
        new Promise<Awaited<ReturnType<ApiClient["activateClassSet"]>>>(
          (done) => {
            resolve = done;
          },
        ),
    );
    const api = mount("ready", { activateClassSet });
    await openTest();
    await userEvent.click(
      screen.getByRole("button", { name: "Testuj wersję roboczą" }),
    );
    await screen.findByText("Walidacja: poprawna");
    await userEvent.click(
      screen.getByRole("button", { name: "Aktywuj zestaw" }),
    );
    await userEvent.dblClick(
      within(screen.getByRole("dialog")).getByRole("button", {
        name: "Aktywuj",
      }),
    );
    expect(activateClassSet).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Anuluj" })).toBeDisabled();
    await userEvent.keyboard("{Escape}");
    expect(screen.getByRole("dialog")).toBeVisible();
    resolve((await api.listClassVersions())[0]!);
    await screen.findByText("Zestaw v2 aktywny");
  });

  it("handles empty, missing and unavailable configurations", async () => {
    const rendered = mount("no-configuration");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      configurationError,
    );
    expect(screen.queryByText("{}", { exact: true })).not.toBeInTheDocument();
    expect(rendered).toBeDefined();
  });

  it("renders not found and recovers from a read error", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const getClassDetail = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValue(await api.getClassDetail("przelew"));
    mount("ready", { getClassDetail });
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Nie udało się wczytać klasy",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Spróbuj ponownie" }),
    );
    expect(
      await screen.findByRole("heading", {
        name: "Potwierdzenie przelewu",
        level: 1,
      }),
    ).toBeVisible();
  });

  it("renders a missing class without fabricating a definition", async () => {
    mount("ready", {}, "unknown");
    expect(await screen.findByText("Nie znaleziono klasy")).toBeVisible();
  });
});

function GuardConsumer() {
  const state = useClassConfiguration();
  return state.blocked ? <ConfigurationError /> : <p>Gotowe</p>;
}

it("shares the configuration blocker with upload consumers", async () => {
  setApiForTests({
    ...createMockClient({ latencyMs: 0 }),
    ...createClassMock(async (value) => value, "no-configuration"),
  });
  render(
    <QueryClientProvider client={new QueryClient()}>
      <GuardConsumer />
    </QueryClientProvider>,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    configurationError,
  );
});
