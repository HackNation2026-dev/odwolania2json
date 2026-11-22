import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default } from "./ThemeToggle.stories";
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
describe("ThemeToggle", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("combobox", { name: "Motyw" })).toBeInTheDocument();
  });
});
