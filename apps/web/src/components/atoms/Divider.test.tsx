import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Divider } from "./Divider";
describe("Divider", () => {
  it("renders a semantic separator", () => {
    render(<Divider />);
    expect(screen.getByRole("separator")).toBeInTheDocument();
  });
});
