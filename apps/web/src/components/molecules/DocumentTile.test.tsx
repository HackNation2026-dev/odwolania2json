import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  Default,
  Partial,
  Error,
  Running,
  Ambiguous,
  Multi,
  Foreign,
} from "./DocumentTile.stories";
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
describe("DocumentTile", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders partial state", () => {
    render(<Partial.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders error state", () => {
    render(<Error.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders running state", () => {
    render(<Running.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders ambiguous state", () => {
    render(<Ambiguous.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders multi state", () => {
    render(<Multi.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders foreign state", () => {
    render(<Foreign.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
});
