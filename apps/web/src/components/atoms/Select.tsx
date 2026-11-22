import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  invalid?: boolean;
};
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  function Select({ invalid, className, ...props }, ref) {
    return (
      <select
        {...props}
        ref={ref}
        aria-invalid={invalid || props["aria-invalid"]}
        className={cn(
          "min-h-11 md:min-h-10 w-full rounded-md border border-control bg-surface px-3 py-2 text-sm text-fg disabled:cursor-not-allowed disabled:opacity-50",
          invalid && "border-[var(--error-fg)]",
          className,
        )}
      />
    );
  },
);
