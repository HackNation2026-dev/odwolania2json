import type { LabelHTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export function Label({
  required,
  children,
  className,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement> & { required?: boolean }) {
  return (
    <label {...props} className={cn("text-sm font-medium", className)}>
      {children}
      {required && <> (wymagane)</>}
    </label>
  );
}
