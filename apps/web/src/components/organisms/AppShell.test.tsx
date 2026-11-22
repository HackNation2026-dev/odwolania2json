import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default } from "./AppShell.stories";
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
describe("AppShell", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("main")).toBeInTheDocument();
  });
});
vi.mock("next/navigation", () => ({ usePathname: () => "/dokumenty" }));
