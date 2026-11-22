import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";
import { Default } from "./AppShellMobileMenu.stories";

it("focuses the menu close action and restores focus after Escape", async () => {
  render(<Default.render />);
  const trigger = screen.getByRole("button", { name: "Otwórz menu" });
  await userEvent.click(trigger);
  expect(screen.getByRole("button", { name: "× Zamknij menu" })).toHaveFocus();
  expect(
    screen.getByRole("link", { name: "Deklaracja dostępności" }),
  ).toHaveAttribute("href", "/dostepnosc");
  await userEvent.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});
