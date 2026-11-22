import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Controlled } from "./Tabs.stories";
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
describe("Tabs", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("tablist")).toHaveAccessibleName();
    expect(screen.getByRole("tabpanel")).toHaveAccessibleName();
  });
  it("renders controlled state", () => {
    render(<Controlled.render />);
    expect(screen.getByRole("tablist")).toHaveAccessibleName();
    expect(screen.getByRole("tabpanel")).toHaveAccessibleName();
  });
});

import userEvent from "@testing-library/user-event";
import { Tabs, TabList, Tab, TabPanel } from "./Tabs";
function TabExample({
  value,
  onValueChange,
}: {
  value?: string;
  onValueChange?: (value: string) => void;
}) {
  return (
    <Tabs value={value} onValueChange={onValueChange}>
      <TabList aria-label="Test">
        <Tab value="one">Pierwsza</Tab>
        <Tab value="disabled" disabled>
          Wyłączona
        </Tab>
        <Tab value="two">Druga</Tab>
      </TabList>
      <TabPanel value="one">Panel pierwszy</TabPanel>
      <TabPanel value="two">Panel drugi</TabPanel>
    </Tabs>
  );
}
it("selects the first enabled tab by default and uses roving focus", async () => {
  const user = userEvent.setup();
  render(<TabExample />);
  const first = screen.getByRole("tab", { name: "Pierwsza" }),
    second = screen.getByRole("tab", { name: "Druga" });
  expect(first).toHaveAttribute("aria-selected", "true");
  expect(first).toHaveAttribute("tabindex", "0");
  expect(second).toHaveAttribute("tabindex", "-1");
  await user.tab();
  expect(first).toHaveFocus();
  await user.keyboard("{ArrowRight}");
  expect(second).toHaveFocus();
  expect(second).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("tabpanel")).toHaveTextContent("Panel drugi");
  await user.keyboard("{ArrowRight}");
  expect(first).toHaveFocus();
  await user.keyboard("{End}");
  expect(second).toHaveFocus();
  await user.keyboard("{Home}");
  expect(first).toHaveFocus();
  await user.keyboard("{ArrowLeft}");
  expect(second).toHaveFocus();
  expect(second.getAttribute("aria-controls")).toBe(
    screen.getByRole("tabpanel").id,
  );
});
it("delegates a controlled selection to its owner", async () => {
  const user = userEvent.setup(),
    change = vi.fn();
  const view = render(<TabExample value="one" onValueChange={change} />);
  await user.click(screen.getByRole("tab", { name: "Druga" }));
  expect(change).toHaveBeenCalledWith("two");
  expect(screen.getByRole("tab", { name: "Pierwsza" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  view.rerender(<TabExample value="two" onValueChange={change} />);
  expect(screen.getByRole("tabpanel")).toHaveTextContent("Panel drugi");
});
