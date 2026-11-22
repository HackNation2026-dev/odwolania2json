import type { ElementType, HTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export function Text({
  as: Tag = "p",
  size = "md",
  tone = "default",
  className,
  ...props
}: HTMLAttributes<HTMLElement> & {
  as?: ElementType;
  size?: "sm" | "md";
  tone?: "default" | "muted";
}) {
  return (
    <Tag
      {...props}
      className={cn(
        size === "sm" ? "text-sm" : "text-base",
        tone === "muted" ? "text-muted" : "text-fg",
        className,
      )}
    />
  );
}
