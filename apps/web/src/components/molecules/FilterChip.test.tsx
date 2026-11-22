import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Pressed } from "./FilterChip.stories";
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
describe("FilterChip", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed");
  });
  it("renders pressed state", () => {
    render(<Pressed.render />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed");
  });
});
