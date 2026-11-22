import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Icon } from "./Icon";
describe("Icon", () => {
  it("renders accessible and decorative icons", () => {
    const { rerender, container } = render(
      <Icon name="check" label="Gotowe" size={24} />,
    );
    expect(screen.getByRole("img", { name: "Gotowe" })).toHaveAttribute(
      "width",
      "24",
    );
    rerender(<Icon name="check" />);
    expect(container.querySelector("svg")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
  });
});
