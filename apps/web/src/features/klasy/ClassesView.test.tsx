import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { ClassesView } from "./ClassesView";

function mount(api = createMockClient({ latencyMs: 0 })) {
  setApiForTests(api);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><ClassesView /></QueryClientProvider>);
}
afterEach(() => setApiForTests(undefined));

describe("ClassesView", () => {
  it("loads real mock classes and exposes required and nullable rules", async () => {
    const api = createMockClient({ latencyMs: 0 });
    const classes = await api.listClasses();
    mount(api);
    expect(screen.getByRole("status")).toHaveTextContent("Wczytywanie klas");
    for (const cls of classes.filter(c => c.id !== "obcy")) {
      const heading = await screen.findByRole("heading", { name: cls.name });
      const card = heading.closest("article")!;
      expect(within(card).getByText(`Liczba pól: ${cls.fields.length}`)).toBeVisible();
      await userEvent.click(within(card).getByText(`Szczegóły pól — ${cls.name}`));
      for (const field of cls.fields) {
        const item = within(card).getByText(field.key).closest("li")!;
        expect(item).toHaveTextContent(field.required ? "Wymagane" : "Opcjonalne");
        expect(item).toHaveTextContent(field.nullable ? "Dopuszcza null" : "Null niedozwolony");
      }
    }
    expect(screen.getByText(/Rozbudowa odbywa się przez YAML poza GUI/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Nowa klasa (po MVP)" })).toBeDisabled();
  });

  it("explains that an empty configuration blocks analysis", async () => {
    const api = createMockClient({ latencyMs: 0 });
    mount({ ...api, listClasses: async () => [] });
    expect(await screen.findByText(/Brak poprawnego zestawu klas/)).toBeVisible();
  });

  it("recovers from a read failure without starting analysis", async () => {
    const api = createMockClient({ latencyMs: 0 });
    let fail = true;
    mount({ ...api, listClasses: async () => {
      if (fail) throw new Error("Odczyt niedostępny");
      return api.listClasses();
    } });
    expect(await screen.findByRole("alert")).toHaveTextContent("Nie udało się wczytać klas");
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Spróbuj ponownie" }));
    expect(await screen.findByRole("heading", { name: (await api.listClasses())[0]!.name })).toBeVisible();
  });
});
