import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import ErrorPage from "@/app/error";
import Forbidden from "@/app/forbidden";
it("shows an incident identifier and retries without exposing the error", async () => {
  const retry = vi.fn();
  render(
    <ErrorPage
      error={Object.assign(new Error("secret-stack"), { digest: "ZD-123" })}
      retry={retry}
    />,
  );
  expect(screen.getByText(/Identyfikator zdarzenia: ZD-123/)).toBeVisible();
  expect(screen.queryByText(/secret-stack/)).not.toBeInTheDocument();
  await userEvent.click(
    screen.getByRole("button", { name: "Spróbuj ponownie" }),
  );
  expect(retry).toHaveBeenCalledOnce();
});
it("renders denial without object details", () => {
  render(<Forbidden />);
  expect(screen.getByRole("heading", { name: "Brak dostępu" })).toBeVisible();
  expect(screen.getByRole("link", { name: "Wróć do spraw" })).toHaveAttribute(
    "href",
    "/dokumenty",
  );
});
