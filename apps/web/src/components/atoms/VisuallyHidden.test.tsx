import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VisuallyHidden } from "./VisuallyHidden";
describe("VisuallyHidden", () => {
  it("keeps hidden text accessible", () => {
    render(
      <button>
        <VisuallyHidden>Zamknij</VisuallyHidden>
      </button>,
    );
    expect(screen.getByRole("button", { name: "Zamknij" })).toBeInTheDocument();
    expect(screen.getByText("Zamknij")).toHaveClass("sr-only");
  });
});
