import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Text } from "./Text";
describe("Text", () => {
  it("renders an inline muted text", () => {
    render(
      <Text as="span" size="sm" tone="muted">
        Opis
      </Text>,
    );
    expect(screen.getByText("Opis").tagName).toBe("SPAN");
    expect(screen.getByText("Opis")).toHaveClass("text-sm", "text-muted");
  });
});
