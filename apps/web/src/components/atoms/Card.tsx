import type { ElementType, HTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export type CardProps = HTMLAttributes<HTMLElement> & {
  as?: ElementType;
  tone?:
    | "default"
    | "raised"
    | "subtle"
    | "full"
    | "partial"
    | "error"
    | "running"
    | "ambiguous";
  padding?: "none" | "sm" | "md" | "lg";
};
const tones = {
  default: "bg-surface",
  raised: "bg-raised shadow-[var(--shadow-1)]",
  subtle: "bg-subtle",
  full: "bg-[var(--full-bg)] text-[var(--full-fg)]",
  partial: "bg-[var(--partial-bg)] text-[var(--partial-fg)]",
  error: "bg-[var(--error-bg)] text-[var(--error-fg)]",
  running: "bg-[var(--running-bg)] text-[var(--running-fg)]",
  ambiguous: "bg-[var(--ambiguous-bg)] text-[var(--ambiguous-fg)]",
};
export function Card({
  as: Tag = "div",
  tone = "default",
  padding = "md",
  className,
  ...props
}: CardProps) {
  return (
    <Tag
      {...props}
      className={cn(
        "min-w-0 rounded-lg border border-border",
        tones[tone],
        { none: "p-0", sm: "p-3", md: "p-4", lg: "p-6" }[padding],
        className,
      )}
    />
  );
}
