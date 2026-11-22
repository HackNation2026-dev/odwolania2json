import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Ocr } from "./EvidenceQuote.stories";
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
describe("EvidenceQuote", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders ocr state", () => {
    render(<Ocr.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
});
