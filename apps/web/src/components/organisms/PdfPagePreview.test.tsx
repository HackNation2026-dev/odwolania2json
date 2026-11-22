import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Empty, MissingText } from "./PdfPagePreview.stories";
beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
});
describe("PdfPagePreview", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders empty state", () => {
    render(<Empty.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
  it("renders missingtext state", () => {
    render(<MissingText.render />);
    expect(document.body).toHaveTextContent(/.+/);
  });
});

import userEvent from "@testing-library/user-event";
import { PdfPagePreview } from "./PdfPagePreview";
it("changes pages with arrow keys and respects page boundaries", async () => {
  const user = userEvent.setup(),
    change = vi.fn();
  const view = render(
    <PdfPagePreview
      pages={2}
      page={1}
      onPageChange={change}
      pageText={["Pierwsza", "Druga"]}
    />,
  );
  const paper = screen.getByRole("region", { name: /Strona PDF/ });
  paper.focus();
  await user.keyboard("{ArrowLeft}");
  expect(change).toHaveBeenLastCalledWith(1);
  await user.keyboard("{ArrowRight}");
  expect(change).toHaveBeenLastCalledWith(2);
  view.rerender(
    <PdfPagePreview
      pages={2}
      page={2}
      onPageChange={change}
      pageText={["Pierwsza", "Druga"]}
    />,
  );
  expect(
    screen.getByRole("button", { name: "Następna strona" }),
  ).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Tekst strony" }));
  expect(screen.getByText("Strona 2 · Tekst PDF")).toBeInTheDocument();
});
