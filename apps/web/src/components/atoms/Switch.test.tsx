import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Switch } from "./Switch";
describe("Switch", () => {
  it("exposes checked state and supports keyboard activation", async () => {
    const change = vi.fn();
    const { rerender } = render(
      <Switch label="Powiadomienia" checked={false} onCheckedChange={change} />,
    );
    const control = screen.getByRole("switch", { name: "Powiadomienia" });
    expect(control).toHaveAttribute("aria-checked", "false");
    control.focus();
    await userEvent.keyboard(" ");
    expect(change).toHaveBeenCalledWith(true);
    rerender(
      <Switch
        label="Powiadomienia"
        checked
        disabled
        onCheckedChange={change}
      />,
    );
    expect(control).toHaveAttribute("aria-checked", "true");
    await userEvent.click(control);
    expect(change).toHaveBeenCalledOnce();
  });
});
