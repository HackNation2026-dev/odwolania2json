import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { describe, expect, it } from "vitest";
import { Input } from "./Input";
describe("Input", () => {
  it("forwards refs, exposes invalid and disabled states, and accepts input", async () => {
    const ref = createRef<HTMLInputElement>();
    const { rerender } = render(<Input aria-label="Pole" ref={ref} />);
    const control = screen.getByRole("textbox", { name: "Pole" });
    expect(ref.current).toBe(control);
    await userEvent.type(control, "KIO");
    expect(control).toHaveValue("KIO");
    rerender(<Input aria-label="Pole" ref={ref} invalid disabled />);
    expect(control).toBeDisabled();
    expect(control).toHaveAttribute("aria-invalid", "true");
  });
});
