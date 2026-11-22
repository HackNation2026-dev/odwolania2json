import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Loading, Complete } from "./LoadMore.stories";
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
describe("LoadMore", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders loading state", () => {
    render(<Loading.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders complete state", () => {
    render(<Complete.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
});
