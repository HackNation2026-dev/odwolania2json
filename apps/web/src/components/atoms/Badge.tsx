import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export type BadgeTone =
  "neutral" | "full" | "partial" | "error" | "running" | "ambiguous" | "info";
const tones: Record<BadgeTone, string> = {
  neutral: "bg-subtle text-fg",
  full: "bg-[var(--full-bg)] text-[var(--full-fg)]",
  partial: "bg-[var(--partial-bg)] text-[var(--partial-fg)]",
  error: "bg-[var(--error-bg)] text-[var(--error-fg)]",
  running: "bg-[var(--running-bg)] text-[var(--running-fg)]",
  ambiguous: "bg-[var(--ambiguous-bg)] text-[var(--ambiguous-fg)]",
  info: "bg-[var(--running-bg)] text-[var(--running-fg)]",
};
export function Badge({
  tone,
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone: BadgeTone }) {
  return (
    <span
      {...props}
      className={cn(
        "inline-flex items-center gap-1 rounded-sm px-2 py-0.5 text-xs font-medium",
        tones[tone],
        className,
      )}
    />
  );
}
