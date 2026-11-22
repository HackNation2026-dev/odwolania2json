import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Kbd } from "./Kbd";
describe("Kbd", () => {
  it("renders a keyboard shortcut", () => {
    render(<Kbd>Ctrl + K</Kbd>);
    expect(screen.getByText("Ctrl + K").tagName).toBe("KBD");
  });
});
