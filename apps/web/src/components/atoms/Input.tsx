import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  invalid?: boolean;
};
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { invalid, className, ...props },
  ref,
) {
  return (
    <input
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
});
