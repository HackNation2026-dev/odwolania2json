import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Pressed, Disabled } from "./ToggleChip.stories";
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
describe("ToggleChip", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed");
  });
  it("renders pressed state", () => {
    render(<Pressed.render />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed");
  });
  it("renders disabled state", () => {
    render(<Disabled.render />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed");
  });
});
