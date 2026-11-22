import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Blocked, Empty, Foreign } from "./JsonViewer.stories";
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
describe("JsonViewer", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders blocked state", () => {
    render(<Blocked.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders empty state", () => {
    render(<Empty.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders foreign state", () => {
    render(<Foreign.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
});

import userEvent from "@testing-library/user-event";
import { JsonViewer } from "./JsonViewer";
it("prevents copying a blocked diagnostic result", async () => {
  const user = userEvent.setup();
  const write = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
  render(<JsonViewer json="{}" blocked />);
  const button = screen.getByRole("button", { name: "Kopiuj JSON" });
  expect(button).toBeDisabled();
  await user.click(button);
  expect(write).not.toHaveBeenCalled();
  expect(
    screen.getByText("Podgląd diagnostyczny").closest("[role=status]")
      ?.textContent,
  ).toContain("Podgląd diagnostyczny");
});
it("does not replace a missing result with empty JSON", () => {
  render(<JsonViewer json={null} />);
  expect(
    screen.queryByRole("button", { name: "Kopiuj JSON" }),
  ).not.toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent("Brak ocenianego JSON");
});
