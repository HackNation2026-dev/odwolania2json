import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Card } from "./Card";
describe("Card", () => {
  it("renders semantic content and tone", () => {
    render(
      <Card as="section" aria-label="Dokument" tone="error" padding="lg">
        Treść
      </Card>,
    );
    expect(screen.getByRole("region", { name: "Dokument" })).toHaveTextContent(
      "Treść",
    );
    expect(screen.getByRole("region")).toHaveClass(
      "p-6",
      "bg-[var(--error-bg)]",
    );
  });
});
