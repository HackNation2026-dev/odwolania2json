import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Error, Closed } from "./Dialog.stories";
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
describe("Dialog", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(
      screen.getByRole("dialog", { name: "Potwierdzenie" }),
    ).toHaveAttribute("aria-modal", "true");
  });
  it("renders error state", () => {
    render(<Error.render />);
    expect(
      screen.getByRole("dialog", { name: "Potwierdzenie" }),
    ).toHaveAttribute("aria-modal", "true");
  });
  it("renders closed state", () => {
    render(<Closed.render />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});

import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { Dialog } from "./Dialog";
import { axe } from "jest-axe";
function ModalExample() {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Otwórz
      </button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Zapis dokumentu"
      >
        <label>
          Nazwa
          <input />
        </label>
        {error && <p role="alert">Błąd zapisu</p>}
        <button type="button" onClick={() => setError(true)}>
          Zapisz
        </button>
      </Dialog>
    </>
  );
}
it("traps focus, closes on Escape and restores focus and scrolling", async () => {
  const user = userEvent.setup();
  document.body.style.overflow = "auto";
  render(<ModalExample />);
  const trigger = screen.getByRole("button", { name: "Otwórz" });
  await user.click(trigger);
  const close = screen.getByRole("button", { name: "Zamknij" }),
    save = screen.getByRole("button", { name: "Zapisz" });
  expect(close).toHaveFocus();
  expect(document.body.style.overflow).toBe("hidden");
  await user.tab({ shift: true });
  expect(save).toHaveFocus();
  await user.tab();
  expect(close).toHaveFocus();
  await user.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
  expect(document.body.style.overflow).toBe("auto");
  document.body.style.overflow = "";
});
it("retains the modal and form value when saving fails", async () => {
  const user = userEvent.setup();
  render(<ModalExample />);
  await user.click(screen.getByRole("button", { name: "Otwórz" }));
  await user.type(screen.getByRole("textbox", { name: "Nazwa" }), "Dokument");
  await user.click(screen.getByRole("button", { name: "Zapisz" }));
  expect(screen.getByRole("alert")).toHaveTextContent("Błąd zapisu");
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: "Nazwa" })).toHaveValue(
    "Dokument",
  );
});
it("has no serious or critical accessibility violations including the portal", async () => {
  const user = userEvent.setup();
  render(<ModalExample />);
  await user.click(screen.getByRole("button", { name: "Otwórz" }));
  const result = await axe(document.body);
  expect(
    result.violations.filter(
      (violation) =>
        violation.impact === "serious" || violation.impact === "critical",
    ),
  ).toEqual([]);
});
it("restores scrolling on unmount", () => {
  document.body.style.overflow = "scroll";
  const view = render(
    <Dialog open onClose={() => {}} title="Panel">
      Treść
    </Dialog>,
  );
  expect(document.body.style.overflow).toBe("hidden");
  view.unmount();
  expect(document.body.style.overflow).toBe("scroll");
  document.body.style.overflow = "";
});
