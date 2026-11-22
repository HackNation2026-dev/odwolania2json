import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "./Button";

describe("Button", () => {
  it("calls onClick", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Zapisz</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Zapisz" }));
    expect(onClick).toHaveBeenCalledOnce();
  });
  it("does not click while disabled", async () => {
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        Zapisz
      </Button>,
    );
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });
});

it("renders loading state and preserves its accessible name", async () => {
  const onClick = vi.fn();
  render(
    <Button loading onClick={onClick}>
      Zapisz
    </Button>,
  );
  const button = screen.getByRole("button", { name: /Zapisz/ });
  expect(button).toHaveAttribute("aria-busy", "true");
  expect(button).toBeDisabled();
  await userEvent.click(button);
  expect(onClick).not.toHaveBeenCalled();
});
it("renders extended variants and icons", () => {
  render(
    <Button
      variant="danger"
      size="lg"
      fullWidth
      leadingIcon={<span>Przed</span>}
      trailingIcon={<span>Po</span>}
    >
      Usuń
    </Button>,
  );
  expect(screen.getByRole("button")).toHaveClass("w-full", "min-h-12");
  expect(screen.getByRole("button")).toHaveTextContent("PrzedUsuńPo");
});
