import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { describe, expect, it } from "vitest";
import { Select } from "./Select";
describe("Select", () => {
  it("forwards refs, exposes invalid and disabled states, and accepts input", async () => {
    const ref = createRef<HTMLSelectElement>();
    const { rerender } = render(
      <Select aria-label="Pole" ref={ref}>
        <option value="a">Odwołanie</option>
        <option value="b">Wyrok</option>
      </Select>,
    );
    const control = screen.getByRole("combobox", { name: "Pole" });
    expect(ref.current).toBe(control);
    await userEvent.selectOptions(control, "b");
    expect(control).toHaveValue("b");
    rerender(
      <Select aria-label="Pole" ref={ref} invalid disabled>
        <option value="a">Odwołanie</option>
        <option value="b">Wyrok</option>
      </Select>,
    );
    expect(control).toBeDisabled();
    expect(control).toHaveAttribute("aria-invalid", "true");
  });
});
