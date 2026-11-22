"use client";
import type { ComponentProps } from "react";
import { Button } from "@/components/atoms";
export type ToggleChipProps = Omit<
  ComponentProps<typeof Button>,
  "aria-pressed"
> & { pressed: boolean; count?: number };
export function ToggleChip({
  pressed,
  count,
  children,
  ...props
}: ToggleChipProps) {
  return (
    <Button
      {...props}
      variant={pressed ? "primary" : "secondary"}
      aria-pressed={pressed}
    >
      {children}
      {count !== undefined && <span> ({count})</span>}
    </Button>
  );
}
export const FilterChip = ToggleChip;
