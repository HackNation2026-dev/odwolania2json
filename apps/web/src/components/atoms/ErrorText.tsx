import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export function ErrorText({
  className,
  ...props
}: HTMLAttributes<HTMLElement>) {
  return (
    <p {...props} className={cn("text-sm text-[var(--error-fg)]", className)} />
  );
}
