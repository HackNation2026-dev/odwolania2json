import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Default, Error, Optional } from "./FormField.stories";
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
describe("FormField", () => {
  it("renders default state", () => {
    render(<Default.render />);
    expect(screen.getByRole("textbox")).toHaveAccessibleName();
  });
  it("renders error state", () => {
    render(<Error.render />);
    expect(screen.getByRole("textbox")).toHaveAccessibleName();
  });
  it("renders optional state", () => {
    render(<Optional.render />);
    expect(screen.getByRole("textbox")).toHaveAccessibleName();
  });
});

import { FormField } from "./FormField";
import { Input } from "@/components/atoms";
it("associates a unique label, hint and error with the input", () => {
  render(
    <>
      <FormField label="Tytuł" required hint="Nazwa dokumentu" error="Wymagane">
        {(a11y) => <Input {...a11y} />}
      </FormField>
      <FormField label="Opis">{(a11y) => <Input {...a11y} />}</FormField>
    </>,
  );
  const input = screen.getByRole("textbox", { name: "Tytuł" });
  expect(input).toBeRequired();
  expect(input).toBeInvalid();
  expect(input).toHaveAccessibleDescription("Nazwa dokumentu Wymagane");
  expect(input.id).not.toBe(screen.getByRole("textbox", { name: "Opis" }).id);
});
