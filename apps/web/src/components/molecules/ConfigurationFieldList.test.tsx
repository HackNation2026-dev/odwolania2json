import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConfigurationFieldList } from "./ConfigurationFieldList";

describe("ConfigurationFieldList", () => {
  it("distinguishes required rules from nullable values", () => {
    render(
      <ConfigurationFieldList
        fields={[
          {
            key: "kwota",
            label: "Kwota",
            type: "liczba",
            description: "Wartość płatności",
            required: true,
            nullable: true,
          },
          {
            key: "numer",
            label: "Numer",
            type: "tekst",
            description: "Numer dokumentu",
            required: false,
            nullable: false,
          },
        ]}
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(within(items[0]!).getByText("kwota")).toBeVisible();
    expect(items[0]).toHaveTextContent("Wymagane · Dopuszcza null");
    expect(items[1]).toHaveTextContent("Opcjonalne · Null niedozwolony");
  });

  it("renders an explicit empty state", () => {
    render(<ConfigurationFieldList fields={[]} />);
    expect(screen.getByText("Brak pól w konfiguracji")).toBeVisible();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });
});
