import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default } from "./TabPanel.stories";
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
describe("TabPanel", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("tablist")).toHaveAccessibleName();
    expect(screen.getByRole("tabpanel")).toHaveAccessibleName();
  });
});
