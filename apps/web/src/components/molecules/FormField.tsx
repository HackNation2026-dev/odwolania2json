"use client";
import { useId, type ReactNode } from "react";
import { Label, HelpText, ErrorText } from "@/components/atoms";
export type FieldAccessibility = {
  id: string;
  "aria-describedby"?: string;
  "aria-invalid": boolean;
  required: boolean;
};
export type FormFieldProps = {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: (a11y: FieldAccessibility) => ReactNode;
};
export function FormField({
  label,
  hint,
  error,
  required = false,
  children,
}: FormFieldProps) {
  const id = useId();
  const described =
    [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") ||
    undefined;
  return (
    <div className="min-w-0 space-y-1">
      <Label htmlFor={id}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </Label>
      {children({
        id,
        "aria-describedby": described,
        "aria-invalid": !!error,
        required,
      })}
      {hint && <HelpText id={`${id}-hint`}>{hint}</HelpText>}
      {error && <ErrorText id={`${id}-error`}>{error}</ErrorText>}
    </div>
  );
}
