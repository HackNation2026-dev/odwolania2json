import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Success, Warning, Error, Neutral } from "./Banner.stories";
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
describe("Banner", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("status")).toHaveTextContent(/.+/);
  });
  it("renders success state", () => {
    render(<Success.render />);
    expect(screen.getByRole("status")).toHaveTextContent(/.+/);
  });
  it("renders warning state", () => {
    render(<Warning.render />);
    expect(screen.getByRole("status")).toHaveTextContent(/.+/);
  });
  it("renders error state", () => {
    render(<Error.render />);
    expect(screen.getByRole("alert")).toHaveTextContent(/.+/);
  });
  it("renders neutral state", () => {
    render(<Neutral.render />);
    expect(screen.getByRole("status")).toHaveTextContent(/.+/);
  });
});
