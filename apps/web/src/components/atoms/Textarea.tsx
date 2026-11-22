import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean;
};
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  function Textarea({ invalid, className, ...props }, ref) {
    return (
      <textarea
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
