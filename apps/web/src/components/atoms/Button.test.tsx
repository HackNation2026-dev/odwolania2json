import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "./Button";

describe("Button", () => {
  it("wywołuje onClick", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Zapisz</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Zapisz" }));
    expect(onClick).toHaveBeenCalledOnce();
  });
  it("nie klika gdy nieaktywny", async () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Zapisz</Button>);
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });
});
