import { cn } from "@/lib/cn";
import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost"; };

export function Button({ variant = "primary", className, type = "button", ...rest }: Props) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-primary text-on-primary hover:opacity-90",
        variant === "secondary" && "border border-control bg-surface text-fg hover:bg-subtle",
        variant === "ghost" && "text-fg hover:bg-subtle",
        className,
      )}
      {...rest}
    />
  );
}
