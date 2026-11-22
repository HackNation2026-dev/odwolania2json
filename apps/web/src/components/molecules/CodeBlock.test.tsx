import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, NoWrap, Blocked, Empty } from "./CodeBlock.stories";
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
describe("CodeBlock", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders nowrap state", () => {
    render(<NoWrap.render />);
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
});

import userEvent from "@testing-library/user-event";
import { CodeBlock } from "./CodeBlock";
it("copies the exact code and announces success", async () => {
  const user = userEvent.setup();
  const write = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
  render(<CodeBlock code={'{"a":null}'} copyLabel="Kopiuj JSON" />);
  await user.click(screen.getByRole("button", { name: "Kopiuj JSON" }));
  expect(write).toHaveBeenCalledWith('{"a":null}');
  expect(screen.getByRole("status")).toHaveTextContent("Skopiowano.");
});
it("announces a clipboard failure", async () => {
  const user = userEvent.setup();
  vi.spyOn(navigator.clipboard, "writeText").mockRejectedValue(
    new Error("Denied"),
  );
  render(<CodeBlock code="{}" />);
  await user.click(screen.getByRole("button", { name: "Kopiuj kod" }));
  expect(screen.getByRole("status")).toHaveTextContent(
    "Nie udało się skopiować",
  );
});
