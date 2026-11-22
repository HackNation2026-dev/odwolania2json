import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default } from "./SegmentedControl.stories";
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
describe("SegmentedControl", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("group", { name: "Widok" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Lista" })).toBeChecked();
  });
});
