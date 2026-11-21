import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { UsersView } from "./UsersView";

afterEach(() => setApiForTests(undefined));
it("renders synthetic users, roles and status with disabled future actions", async () => {
  setApiForTests(createMockClient({ latencyMs: 0 }));
  render(<QueryClientProvider client={new QueryClient()}><UsersView /></QueryClientProvider>);
  expect(screen.getByRole("status")).toHaveTextContent("Wczytywanie");
  expect(await screen.findByRole("rowheader", { name: "Anna Kowalska" })).toBeVisible();
  expect(screen.getByText("Administrator")).toBeVisible();
  expect(screen.getByText("◌ Zaproszony")).toBeVisible();
  expect(screen.getByText("× Zablokowany")).toBeVisible();
  expect(screen.getByRole("button", { name: "Dodaj użytkownika" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Odblokuj: Marta Lis" })).toBeDisabled();
});
