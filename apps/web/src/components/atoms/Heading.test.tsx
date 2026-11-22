import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Heading } from "./Heading";
describe("Heading", () => {
  it.each([1, 2, 3, 4] as const)("renders heading level %s", (level) => {
    render(
      <Heading level={level} as="div">
        Dokumenty
      </Heading>,
    );
    expect(
      screen.getByRole("heading", { level, name: "Dokumenty" }),
    ).toBeInTheDocument();
  });
});
