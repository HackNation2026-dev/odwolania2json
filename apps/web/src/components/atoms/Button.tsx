import { cn } from "@/lib/cn";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Spinner } from "./Spinner";
export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  fullWidth?: boolean;
  /** Większy cel dotykowy w nowych widokach; domyślnie zachowuje wygląd referencyjny. */
  touch?: boolean;
};
export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  leadingIcon,
  trailingIcon,
  fullWidth,
  touch = false,
  disabled,
  children,
  className,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        size === "md"
          ? "inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
          : "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-primary text-on-primary hover:opacity-90",
        variant === "secondary" &&
          "border border-control bg-surface text-fg hover:bg-subtle",
        variant === "ghost" && "text-fg hover:bg-subtle",
        variant === "danger" &&
          "bg-[var(--error-fg)] text-[var(--error-bg)] hover:opacity-90",
        size === "sm" && "min-h-11 md:min-h-10 px-3 text-xs",
        size === "lg" && "min-h-12 md:min-h-12 px-6 text-base",
        touch && size === "md" && "min-h-11 md:min-h-10",
        fullWidth && "w-full",
        className,
      )}
      {...rest}
      disabled={disabled || loading}
      aria-busy={loading || rest["aria-busy"]}
    >
      {loading ? <Spinner label="Ładowanie" /> : leadingIcon}
      {children}
      {trailingIcon}
    </button>
  );
}
