import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { IconButton } from "./IconButton";
describe("IconButton", () => {
  it("uses the required label and handles clicks", async () => {
    const click = vi.fn();
    const { rerender } = render(
      <IconButton label="Dodaj" icon="plus" onClick={click} />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Dodaj" }));
    expect(click).toHaveBeenCalledOnce();
    rerender(<IconButton label="Dodaj" icon="plus" disabled onClick={click} />);
    await userEvent.click(screen.getByRole("button"));
    expect(click).toHaveBeenCalledOnce();
  });
});
