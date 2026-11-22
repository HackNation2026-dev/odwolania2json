import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { KeyView } from "./KeyView";
import { SelfCheckView } from "./SelfCheckView";

afterEach(() => {
  cleanup();
  setApiForTests(undefined);
  localStorage.clear();
});

function setup(
  view: React.ReactNode,
  api = createMockClient({ latencyMs: 0 }),
) {
  setApiForTests(api);
  const query = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return {
    ...render(<QueryClientProvider client={query}>{view}</QueryClientProvider>),
    query,
  };
}

describe("API key configuration", () => {
  it("reveals the key only on request and masks it again without persisting it", async () => {
    setup(<KeyView />);
    const field = await screen.findByLabelText("Klucz API", { exact: true });
    await userEvent.type(field, "synthetic-visible-key");
    const reveal = screen.getByRole("button", { name: "Pokaż klucz" });
    expect(reveal).toHaveAttribute("aria-pressed", "false");
    await userEvent.click(reveal);
    expect(field).toHaveAttribute("type", "text");
    expect(screen.getByRole("button", { name: "Ukryj klucz" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await userEvent.click(screen.getByRole("button", { name: "Ukryj klucz" }));
    expect(field).toHaveAttribute("type", "password");
    expect(localStorage.length).toBe(0);
  });
  it("rejects an empty key", async () => {
    setup(<KeyView />);
    await userEvent.click(
      await screen.findByRole("button", { name: "Sprawdź i zapisz" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Podaj klucz API.",
    );
  });

  it("saves consent and displays only configured state without retaining the secret", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const { container, query } = setup(<KeyView />, api);
    const field = await screen.findByLabelText("Klucz API", { exact: true });
    expect(field).toHaveAttribute("type", "password");
    await userEvent.type(field, "synthetic-secret");
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(
      screen.getByRole("button", { name: "Sprawdź i zapisz" }),
    );
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Klucz: skonfigurowany",
    );
    expect(container.innerHTML).not.toContain("synthetic-secret");
    expect(JSON.stringify(localStorage)).not.toContain("synthetic-secret");
    await waitFor(() =>
      expect(
        JSON.stringify(
          query
            .getMutationCache()
            .getAll()
            .map((m) => m.state.variables),
        ),
      ).not.toContain("synthetic-secret"),
    );
    expect(await api.getKeyStatus()).toMatchObject({
      configured: true,
      persisted: true,
    });
  });
});

describe("Self check", () => {
  it("shows an empty configuration with a link to the key form", async () => {
    setup(<SelfCheckView />);
    expect(
      await screen.findByRole("link", { name: "Wpisz klucz API" }),
    ).toHaveAttribute("href", "/klucz");
    expect(
      screen.queryByRole("button", { name: "Sprawdź ponownie" }),
    ).not.toBeInTheDocument();
  });

  it("streams five successful checks", async () => {
    const api = createMockClient({ latencyMs: 5 });
    await api.saveKey({ value: "synthetic", persist: false });
    setup(<SelfCheckView />, api);
    await userEvent.click(
      await screen.findByRole("button", { name: "Sprawdź ponownie" }),
    );
    expect(
      await screen.findByRole("link", { name: "Przejdź do pulpitu" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/: Powodzenie$/)).toHaveLength(5);
  });

  it("stops on 401 without retries and enables checking after a corrected configuration", async () => {
    const api = createMockClient({ latencyMs: 0, failKey: true });
    await api.saveKey({ value: "synthetic", persist: false });
    const run = vi.spyOn(api, "runSelfCheck");
    const { unmount } = setup(<SelfCheckView />, api);
    await userEvent.click(
      await screen.findByRole("button", { name: "Sprawdź ponownie" }),
    );
    expect(
      await screen.findByRole("heading", {
        name: "API odrzuciło uwierzytelnienie (401)",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Nie ponawiamy automatycznie",
    );
    expect(
      screen.queryByRole("button", { name: "Sprawdź ponownie" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Dostępność i zgodność modelu z konfiguracją: Pominięto",
      ),
    ).toBeInTheDocument();
    expect(run).toHaveBeenCalledTimes(1);
    unmount();
    const second = setup(<SelfCheckView />, api);
    expect(
      await screen.findByRole("link", { name: "Wpisz klucz ponownie" }),
    ).toBeInTheDocument();
    expect(run).toHaveBeenCalledTimes(1);
    second.unmount();
    await api.saveKey({ value: "corrected-synthetic", persist: false });
    setup(<SelfCheckView />, api);
    expect(
      await screen.findByRole("button", { name: "Sprawdź ponownie" }),
    ).toBeEnabled();
  });
});
