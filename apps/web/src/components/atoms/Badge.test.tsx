import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "./Badge";
describe("Badge", () => {
  it("renders text independently of color", () => {
    render(<Badge tone="partial">Częściowy</Badge>);
    expect(screen.getByText("Częściowy")).toHaveClass("bg-[var(--partial-bg)]");
  });
});
