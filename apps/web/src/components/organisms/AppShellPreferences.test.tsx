import { act, render } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { AppShellPreferences } from "./AppShellPreferences";

afterEach(() => localStorage.clear());
it("applies persisted preferences and responds to changes", () => {
  localStorage.setItem(
    "o2j-preferences",
    JSON.stringify({ dense: true, reducedMotion: true, noShortcuts: true }),
  );
  const { container } = render(<AppShellPreferences />);
  expect(container.querySelector("style")).toHaveTextContent(
    "animation-duration",
  );
  expect(container.querySelector("style")).toHaveTextContent("padding-block");
  expect(document.documentElement.dataset.singleKeyShortcuts).toBe("off");
  act(() => {
    localStorage.setItem("o2j-preferences", "{}");
    window.dispatchEvent(new Event("o2j-preferences"));
  });
  expect(container.querySelector("style")).toBeNull();
  expect(document.documentElement.dataset.singleKeyShortcuts).toBe("on");
});
