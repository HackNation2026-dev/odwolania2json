import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { OcrReadinessBanner } from "./OcrReadinessBanner";
it("announces unavailable OCR without implying a foreign document", () => {
  render(
    <OcrReadinessBanner
      mode="unavailable"
      name="OCR"
      version={null}
      detail="Brak usługi"
    />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("OCR niedostępny");
  expect(screen.getByRole("alert")).toHaveTextContent(
    "nie zostanie uznany za obcy",
  );
});
