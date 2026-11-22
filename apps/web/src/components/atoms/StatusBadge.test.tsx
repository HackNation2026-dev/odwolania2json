import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { documentStatus } from "@/lib/api/schemas";
import { StatusBadge, statusMeta } from "./StatusBadge";

describe("StatusBadge", () => {
  it.each(documentStatus.options)("pokazuje tekst statusu %s", (s) => {
    render(<StatusBadge status={s} />);
    expect(screen.getByText(statusMeta[s].label)).toBeInTheDocument();
  });
  it("keeps the reference glyph by default and supports optional SVG", () => {
    const { container, rerender } = render(<StatusBadge status="full" />);
    expect(screen.getByText(statusMeta.full.icon)).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelector("svg")).not.toBeInTheDocument();
    rerender(<StatusBadge status="full" iconVariant="svg" />);
    expect(container.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
    expect(screen.getByText(statusMeta.full.label)).toBeInTheDocument();
  });
});
