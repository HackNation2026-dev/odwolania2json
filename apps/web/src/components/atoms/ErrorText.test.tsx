import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ErrorText } from "./ErrorText";
describe("ErrorText", () => {
  it("provides an error description without an alert", () => {
    render(
      <>
        <input aria-label="Sygnatura" aria-invalid aria-describedby="error" />
        <ErrorText id="error">Wymagane</ErrorText>
      </>,
    );
    expect(screen.getByRole("textbox")).toHaveAccessibleDescription("Wymagane");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
