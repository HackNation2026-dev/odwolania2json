"use client";
import { useId } from "react";
import { Radio } from "@/components/atoms";
export type SegmentedControlProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string; disabled?: boolean }[];
};
export function SegmentedControl({
  label,
  value,
  onChange,
  options,
}: SegmentedControlProps) {
  const name = useId();
  return (
    <fieldset className="min-w-0">
      <legend className="mb-1 text-sm">{label}</legend>
      <div className="flex flex-wrap gap-1 rounded-md bg-subtle p-1">
        {options.map((option) => (
          <Radio
            key={option.value}
            className={`flex min-h-11 cursor-pointer items-center gap-2 rounded px-3 text-sm ${value === option.value ? "bg-surface font-semibold" : ""}`}
            label={option.label}
            name={name}
            value={option.value}
            checked={value === option.value}
            disabled={option.disabled}
            onChange={() => onChange(option.value)}
          />
        ))}
      </div>
    </fieldset>
  );
}
