import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { describe, expect, it } from "vitest";
import { Textarea } from "./Textarea";
describe("Textarea", () => {
  it("forwards refs, exposes invalid and disabled states, and accepts input", async () => {
    const ref = createRef<HTMLTextAreaElement>();
    const { rerender } = render(<Textarea aria-label="Pole" ref={ref} />);
    const control = screen.getByRole("textbox", { name: "Pole" });
    expect(ref.current).toBe(control);
    await userEvent.type(control, "KIO");
    expect(control).toHaveValue("KIO");
    rerender(<Textarea aria-label="Pole" ref={ref} invalid disabled />);
    expect(control).toBeDisabled();
    expect(control).toHaveAttribute("aria-invalid", "true");
  });
});
