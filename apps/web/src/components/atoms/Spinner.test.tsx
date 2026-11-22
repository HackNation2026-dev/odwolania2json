import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Spinner } from "./Spinner";
describe("Spinner", () => {
  it("announces progress and has a reduced motion alternative", () => {
    const { container } = render(<Spinner label="Wczytywanie" />);
    expect(screen.getByRole("status")).toHaveTextContent("Wczytywanie");
    expect(
      container.querySelector(".motion-reduce\\:inline"),
    ).toHaveTextContent("Wczytywanie");
  });
});
