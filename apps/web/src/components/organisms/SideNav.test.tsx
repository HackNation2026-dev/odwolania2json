import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Administration } from "./SideNav.stories";
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
describe("SideNav", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(
      screen.getByRole("navigation", { name: "Główna" }),
    ).toBeInTheDocument();
  });
  it("renders administration state", () => {
    render(<Administration.render />);
    expect(
      screen.getByRole("navigation", { name: "Główna" }),
    ).toBeInTheDocument();
  });
});
