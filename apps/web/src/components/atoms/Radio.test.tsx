import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { describe, expect, it, vi } from "vitest";
import { Radio } from "./Radio";
describe("Radio", () => {
  it("handles selection, validation and disabled state", async () => {
    const change = vi.fn();
    const ref = createRef<HTMLInputElement>();
    const { rerender } = render(
      <Radio ref={ref} label="Wybór" onChange={change} />,
    );
    const control = screen.getByRole("radio", { name: "Wybór" });
    expect(ref.current).toBe(control);
    await userEvent.click(control);
    expect(control).toBeChecked();
    expect(change).toHaveBeenCalledOnce();
    rerender(
      <Radio ref={ref} label="Wybór" onChange={change} invalid disabled />,
    );
    expect(control).toHaveAttribute("aria-invalid", "true");
    expect(control).toBeDisabled();
    await userEvent.click(control);
    expect(change).toHaveBeenCalledOnce();
  });
});
