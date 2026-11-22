import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { UsersView } from "./UsersView";

afterEach(() => setApiForTests(undefined));
it("explains an empty user list", async () => {
  setApiForTests({
    ...createMockClient({ latencyMs: 0 }),
    listUsers: async () => [],
  });
  render(
    <QueryClientProvider client={new QueryClient()}>
      <UsersView />
    </QueryClientProvider>,
  );
  expect(await screen.findByText("Brak użytkowników.")).toBeVisible();
});
it("retries a failed user read", async () => {
  const api = createMockClient({ latencyMs: 0 });
  let fail = true;
  setApiForTests({
    ...api,
    listUsers: async () => {
      if (fail) throw new Error("Awaria");
      return api.listUsers();
    },
  });
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <UsersView />
    </QueryClientProvider>,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Nie udało się wczytać użytkowników",
  );
  fail = false;
  await userEvent.click(
    screen.getByRole("button", { name: "Spróbuj ponownie" }),
  );
  expect(
    await screen.findByRole("rowheader", { name: "Anna Kowalska" }),
  ).toBeVisible();
});
it("renders synthetic users, roles and status with disabled future actions", async () => {
  setApiForTests(createMockClient({ latencyMs: 0 }));
  render(
    <QueryClientProvider client={new QueryClient()}>
      <UsersView />
    </QueryClientProvider>,
  );
  expect(screen.getByRole("status")).toHaveTextContent("Wczytywanie");
  expect(
    await screen.findByRole("rowheader", { name: "Anna Kowalska" }),
  ).toBeVisible();
  expect(screen.getByText("Administrator")).toBeVisible();
  expect(screen.getByText("◌ Zaproszony")).toBeVisible();
  expect(screen.getByText("× Zablokowany")).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Dodaj użytkownika" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Odblokuj: Marta Lis" }),
  ).toBeDisabled();
});

it("opens role and case scope preview without changing permissions", async () => {
  setApiForTests(createMockClient({ latencyMs: 0 }));
  render(
    <QueryClientProvider client={new QueryClient()}>
      <UsersView />
    </QueryClientProvider>,
  );
  await userEvent.click(
    await screen.findByRole("button", { name: "Edytuj: Anna Kowalska" }),
  );
  expect(screen.getByRole("dialog")).toHaveTextContent("E3");
  expect(screen.getByRole("combobox", { name: "Zakres spraw" })).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Zapisz (po MVP)" }),
  ).toBeDisabled();
  await userEvent.keyboard("{Escape}");
  expect(
    screen.getByRole("button", { name: "Edytuj: Anna Kowalska" }),
  ).toHaveFocus();
});
