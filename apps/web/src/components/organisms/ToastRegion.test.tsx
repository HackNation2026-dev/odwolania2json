import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default } from "./ToastRegion.stories";
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
describe("ToastRegion", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(
      screen.getByRole("region", { name: "Powiadomienia" }),
    ).toHaveAttribute("aria-live", "polite");
  });
});

import userEvent from "@testing-library/user-event";
import { ToastRegion, useToast } from "./ToastRegion";
function Trigger() {
  const { toast } = useToast();
  return (
    <button onClick={() => toast({ title: "Zapisano", tone: "success" })}>
      Zapisz
    </button>
  );
}
it("announces and dismisses a notification", async () => {
  const user = userEvent.setup();
  render(
    <ToastRegion>
      <Trigger />
    </ToastRegion>,
  );
  await user.click(screen.getByRole("button", { name: "Zapisz" }));
  expect(
    screen.getByRole("region", { name: "Powiadomienia" }),
  ).toHaveTextContent("Zapisano");
  await user.click(
    screen.getByRole("button", { name: "Zamknij powiadomienie: Zapisano" }),
  );
  expect(screen.queryByText("Zapisano")).not.toBeInTheDocument();
});
