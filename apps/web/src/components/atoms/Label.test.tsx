import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Label } from "./Label";
describe("Label", () => {
  it("associates a required label with its field", () => {
    render(
      <>
        <Label htmlFor="field" required>
          Sygnatura
        </Label>
        <input id="field" required />
      </>,
    );
    expect(
      screen.getByRole("textbox", { name: "Sygnatura (wymagane)" }),
    ).toBeRequired();
  });
});
