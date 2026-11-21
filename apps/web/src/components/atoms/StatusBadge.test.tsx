import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { documentStatus } from "@/lib/api/schemas";
import { StatusBadge, statusMeta } from "./StatusBadge";

describe("StatusBadge", () => {
  it.each(documentStatus.options)("pokazuje tekst statusu %s", (s) => {
    render(<StatusBadge status={s} />);
    expect(screen.getByText(statusMeta[s].label)).toBeInTheDocument();
  });
});
