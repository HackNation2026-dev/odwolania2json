import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Empty } from "./SkeletonBlock.stories";
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
describe("SkeletonBlock", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.querySelector("[aria-hidden=true]")).toBeInTheDocument();
  });
  it("renders empty state", () => {
    render(<Empty.render />);
    expect(document.querySelector("[aria-hidden=true]")).toBeInTheDocument();
  });
});
