import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Filled, Disabled } from "./SearchBox.stories";
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
describe("SearchBox", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("searchbox")).toHaveAccessibleName();
  });
  it("renders filled state", () => {
    render(<Filled.render />);
    expect(screen.getByRole("searchbox")).toHaveAccessibleName();
  });
  it("renders disabled state", () => {
    render(<Disabled.render />);
    expect(screen.getByRole("searchbox")).toHaveAccessibleName();
  });
});
