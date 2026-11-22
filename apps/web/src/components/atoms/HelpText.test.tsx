import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HelpText } from "./HelpText";
describe("HelpText", () => {
  it("provides a field description", () => {
    render(
      <>
        <input aria-label="Sygnatura" aria-describedby="help" />
        <HelpText id="help">Pomoc</HelpText>
      </>,
    );
    expect(screen.getByRole("textbox")).toHaveAccessibleDescription("Pomoc");
  });
});
