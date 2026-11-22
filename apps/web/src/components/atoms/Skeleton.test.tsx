import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Skeleton } from "./Skeleton";
describe("Skeleton", () => {
  it("hides decorative loading shapes", () => {
    const { container } = render(<Skeleton className="w-48" />);
    expect(container.firstChild).toHaveAttribute("aria-hidden", "true");
    expect(container.firstChild).toHaveClass("w-48");
  });
});
