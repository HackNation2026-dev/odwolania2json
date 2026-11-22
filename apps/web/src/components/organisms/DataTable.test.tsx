import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Empty, Loading, Error } from "./DataTable.stories";
beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
});
describe("DataTable", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(
      screen.getByRole("table", { name: "Dokumenty" }),
    ).toBeInTheDocument();
  });
  it("renders empty state", () => {
    render(<Empty.render />);
    expect(screen.getByRole("status")).toHaveTextContent("Brak wyników");
  });
  it("renders loading state", () => {
    render(<Loading.render />);
    expect(screen.getByText("Wczytywanie…")).toBeInTheDocument();
  });
  it("renders error state", () => {
    render(<Error.render />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

import userEvent from "@testing-library/user-event";
import { within } from "@testing-library/react";
import { DataTable } from "./DataTable";
it("renders mobile cards with sorting and a single copy of each row", async () => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
  const user = userEvent.setup();
  render(
    <DataTable
      columns={columns}
      rows={[
        { id: "z", name: "Zet" },
        { id: "a", name: "Alfa" },
      ]}
      rowKey={(row) => row.id}
      cardTitle={(row) => row.name}
      caption="Dokumenty"
    />,
  );
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
  expect(screen.getAllByRole("article")).toHaveLength(2);
  await user.click(screen.getByRole("button", { name: "Sortuj: Nazwa" }));
  expect(screen.getAllByRole("article")[0]).toHaveTextContent("Alfa");
});
const columns = [
  {
    key: "name",
    label: "Nazwa",
    render: (row: { id: string; name: string }) => row.name,
    sortValue: (row: { id: string; name: string }) => row.name,
  },
];
it("sorts rows in both directions through a header button", async () => {
  const user = userEvent.setup();
  render(
    <DataTable
      columns={columns}
      rows={[
        { id: "z", name: "Zet" },
        { id: "a", name: "Alfa" },
      ]}
      rowKey={(row) => row.id}
      cardTitle={(row) => row.name}
      caption="Dokumenty"
    />,
  );
  const table = screen.getByRole("table");
  const header = within(table).getByRole("columnheader", { name: /Nazwa/ });
  await user.click(within(table).getByRole("button", { name: /Nazwa/ }));
  expect(header).toHaveAttribute("aria-sort", "ascending");
  expect(within(table).getAllByRole("row")[1]).toHaveTextContent("Alfa");
  await user.click(within(table).getByRole("button", { name: /Nazwa/ }));
  expect(header).toHaveAttribute("aria-sort", "descending");
  expect(within(table).getAllByRole("row")[1]).toHaveTextContent("Zet");
});
it("calls retry from its error state", async () => {
  const user = userEvent.setup(),
    retry = vi.fn();
  render(
    <DataTable
      columns={columns}
      rows={[]}
      rowKey={(row) => row.id}
      cardTitle={(row) => row.name}
      caption="Dokumenty"
      error="Awaria"
      onRetry={retry}
    />,
  );
  await user.click(screen.getByRole("button", { name: "Spróbuj ponownie" }));
  expect(retry).toHaveBeenCalledOnce();
});
