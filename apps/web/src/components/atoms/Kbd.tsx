import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export function Kbd({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return (
    <kbd
      {...props}
      className={cn(
        "rounded-sm border border-control bg-subtle px-1.5 py-0.5 font-mono text-sm",
        className,
      )}
    />
  );
}
