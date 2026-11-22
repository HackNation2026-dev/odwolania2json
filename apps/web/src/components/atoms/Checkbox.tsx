import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cn";
export type CheckboxProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type"
> & { label: ReactNode; invalid?: boolean };
export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  function Checkbox({ label, invalid, className, ...props }, ref) {
    return (
      <label
        className={cn(
          "inline-flex min-h-11 md:min-h-10 items-center gap-2 text-sm",
          props.disabled && "cursor-not-allowed opacity-50",
          className,
        )}
      >
        <input
          {...props}
          ref={ref}
          type="checkbox"
          aria-invalid={invalid || props["aria-invalid"]}
          className={cn(
            "h-5 w-5 accent-primary",
            invalid && "outline outline-[var(--error-fg)]",
          )}
        />
        {label}
      </label>
    );
  },
);
