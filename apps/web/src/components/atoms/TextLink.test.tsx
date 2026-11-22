import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { TextLink } from "./TextLink";
describe("TextLink", () => {
  it("renders a named keyboard focusable link", async () => {
    render(<TextLink href="/dokumenty">Dokumenty</TextLink>);
    const link = screen.getByRole("link", { name: "Dokumenty" });
    expect(link).toHaveAttribute("href", "/dokumenty");
    await userEvent.tab();
    expect(link).toHaveFocus();
  });
});
