import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export function HelpText({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <p {...props} className={cn("text-sm text-muted", className)} />;
}
