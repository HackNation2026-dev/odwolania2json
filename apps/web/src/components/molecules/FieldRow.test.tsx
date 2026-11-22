import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Missing, Computed, Corrected } from "./FieldRow.stories";
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
describe("FieldRow", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders missing state", () => {
    render(<Missing.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders computed state", () => {
    render(<Computed.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders corrected state", () => {
    render(<Corrected.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
});
