import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { SettingsView } from "./SettingsView";

function mount(api = createMockClient({ latencyMs: 0 })) {
  setApiForTests(api);
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <SettingsView />
    </QueryClientProvider>,
  );
}
afterEach(() => {
  setApiForTests(undefined);
  localStorage.clear();
});
it("validates retention, associates the error and confirms saving", async () => {
  mount();
  const input = await screen.findByRole("spinbutton", {
    name: "Usuń sprawy po (liczba dni)",
  });
  await userEvent.clear(input);
  await userEvent.type(input, "0");
  await userEvent.click(
    screen.getByRole("button", { name: "Zapisz retencję" }),
  );
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(input).toHaveAccessibleDescription(/Podaj liczbę dni z zakresu 1–365/);
  expect(input).toHaveFocus();
  await userEvent.clear(input);
  await userEvent.type(input, "60");
  await userEvent.click(
    screen.getByRole("button", { name: "Zapisz retencję" }),
  );
  expect(screen.getByRole("dialog")).toHaveTextContent("Nowa retencja: 60 dni");
  await userEvent.click(screen.getByRole("button", { name: /^Zapisz$/ }));
  expect(
    await screen.findByText("Zapisano retencję w demonstracji."),
  ).toBeVisible();
  expect(input).toHaveValue(60);
});
it("keeps the confirmation open when saving fails", async () => {
  mount({
    ...createMockClient({ latencyMs: 0 }),
    saveRetention: async () => {
      throw new Error("Awaria");
    },
  });
  await screen.findByRole("spinbutton");
  await userEvent.click(
    screen.getByRole("button", { name: "Zapisz retencję" }),
  );
  await userEvent.click(screen.getByRole("button", { name: /^Zapisz$/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Nie zapisano");
  expect(screen.getByRole("dialog")).toBeVisible();
});
it("stores accessibility preferences without keys", async () => {
  mount();
  await userEvent.click(
    screen.getByRole("checkbox", { name: "Ogranicz animacje" }),
  );
  expect(localStorage.getItem("o2j-preferences")).toContain("reducedMotion");
  expect(
    screen.getByText("Preferencje zapisano na tym urządzeniu."),
  ).toBeVisible();
});
