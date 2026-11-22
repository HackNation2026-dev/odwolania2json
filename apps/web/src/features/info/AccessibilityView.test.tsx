import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { AccessibilityView } from "./AccessibilityView";
it("renders an honest accessibility statement without requiring an API provider", () => {
  render(<AccessibilityView />);
  expect(screen.getByRole("heading", { name: "Dostępność" })).toBeVisible();
  expect(screen.getByText("Nie przeprowadzono audytu.")).toBeVisible();
  expect(screen.getByText("Kontakt nie został skonfigurowany.")).toBeVisible();
  expect(screen.getByRole("link", { name: "Wróć do analizy" })).toHaveAttribute(
    "href",
    "/dodaj",
  );
});
