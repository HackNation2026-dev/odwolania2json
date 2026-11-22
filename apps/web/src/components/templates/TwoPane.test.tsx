import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, WideLeft } from "./TwoPane.stories";
beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
});
describe("TwoPane", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(
      screen.getByRole("tablist", { name: "Panele dokumentu" }),
    ).toBeInTheDocument();
  });
  it("renders wideleft state", () => {
    render(<WideLeft.render />);
    expect(
      screen.getByRole("tablist", { name: "Panele dokumentu" }),
    ).toBeInTheDocument();
  });
});

import { TwoPane } from "./TwoPane";
import userEvent from "@testing-library/user-event";
it("switches the mobile panel by keyboard without duplicating children", async () => {
  const user = userEvent.setup();
  render(
    <TwoPane
      left={<input aria-label="Pole dokumentu" />}
      right={<p>JSON</p>}
    />,
  );
  expect(screen.getAllByRole("textbox", { hidden: true })).toHaveLength(1);
  await user.click(screen.getByRole("tab", { name: "Dane" }));
  expect(screen.getByRole("tabpanel")).toHaveTextContent("JSON");
});
it("renders desktop safely without matchMedia", () => {
  vi.stubGlobal("matchMedia", undefined);
  render(<TwoPane left={<p>Lewy panel</p>} right={<p>Prawy panel</p>} />);
  expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
  expect(screen.getByText("Lewy panel")).toBeVisible();
  expect(screen.getByText("Prawy panel")).toBeVisible();
});
