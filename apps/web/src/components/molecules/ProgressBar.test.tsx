import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Pending, Complete } from "./ProgressBar.stories";
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
describe("ProgressBar", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(
      screen.getByRole("progressbar", { name: /Analiza/ }),
    ).toHaveAttribute("aria-valuenow");
  });
  it("renders pending state", () => {
    render(<Pending.render />);
    expect(
      screen.getByRole("progressbar", { name: /Analiza/ }),
    ).toHaveAttribute("aria-valuenow");
  });
  it("renders complete state", () => {
    render(<Complete.render />);
    expect(
      screen.getByRole("progressbar", { name: /Analiza/ }),
    ).toHaveAttribute("aria-valuenow");
  });
});

import { ProgressBar } from "./ProgressBar";
it.each([
  [-4, 0],
  [130, 100],
  [Number.NaN, 0],
])("clamps progress %s to %s", (value, expected) => {
  render(<ProgressBar label="Postęp" value={value} />);
  expect(screen.getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    String(expected),
  );
  expect(screen.getByText(`Postęp: ${expected}%`)).toHaveAttribute(
    "aria-live",
    "polite",
  );
});
