import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Active } from "./NavItem.stories";
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
describe("NavItem", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("link", { name: "Dokumenty" })).toHaveAttribute(
      "href",
      "/dokumenty",
    );
  });
  it("renders active state", () => {
    render(<Active.render />);
    expect(screen.getByRole("link", { name: "Dokumenty" })).toHaveAttribute(
      "href",
      "/dokumenty",
    );
  });
});
