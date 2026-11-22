import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, WithoutRetry } from "./ErrorState.stories";
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
describe("ErrorState", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("alert")).toHaveTextContent(/.+/);
  });
  it("renders withoutretry state", () => {
    render(<WithoutRetry.render />);
    expect(screen.getByRole("alert")).toHaveTextContent(/.+/);
  });
});
