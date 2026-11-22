import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
export type SwitchProps = Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "onChange"
> & {
  label: ReactNode;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
};
export function Switch({
  label,
  checked,
  onCheckedChange,
  className,
  ...props
}: SwitchProps) {
  return (
    <button
      {...props}
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={(event) => {
        props.onClick?.(event);
        if (!event.defaultPrevented) onCheckedChange(!checked);
      }}
      className={cn(
        "inline-flex min-h-11 md:min-h-10 items-center gap-2 text-sm disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
    >
      <span
        aria-hidden
        className={cn(
          "inline-flex w-10 rounded-full border border-control p-1",
          checked ? "bg-primary justify-end" : "bg-subtle justify-start",
        )}
      >
        <span
          className={cn(
            "h-4 w-4 rounded-full",
            checked ? "bg-on-primary" : "bg-muted",
          )}
        />
      </span>
      {label}
    </button>
  );
}
