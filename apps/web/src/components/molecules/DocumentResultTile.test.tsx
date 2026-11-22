import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { DocumentResultTile } from "./DocumentResultTile";
it("keeps the complete tile as a document link", () => {
  render(
    <DocumentResultTile
      document={{
        id: "test",
        fileName: "test.pdf",
        status: "full",
        className: "Odwołanie",
        pages: 2,
        uploadedAt: "2026-11-21T10:00:00Z",
      }}
      codes={[]}
    />,
  );
  expect(screen.getByRole("link")).toHaveAttribute("href", "/dokumenty/test");
  expect(screen.getByText("Plik wynikowy: test.json")).toBeVisible();
});
