import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default } from "./PageHeader.stories";
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
describe("PageHeader", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
});
