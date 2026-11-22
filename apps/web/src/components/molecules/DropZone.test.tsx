import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Disabled } from "./DropZone.stories";
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
describe("DropZone", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(
      screen.getByRole("button", { name: "Wybierz pliki" }),
    ).toBeInTheDocument();
  });
  it("renders disabled state", () => {
    render(<Disabled.render />);
    expect(
      screen.getByRole("button", { name: "Wybierz pliki" }),
    ).toBeInTheDocument();
  });
});
