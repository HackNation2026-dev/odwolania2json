"use client";
import { useId, type ComponentProps } from "react";
import { Icon, Input, IconButton } from "@/components/atoms";
export type SearchBoxProps = Omit<ComponentProps<typeof Input>, "type"> & {
  label?: string;
  onClear?: () => void;
};
export function SearchBox({
  label = "Szukaj",
  onClear,
  id,
  ...props
}: SearchBoxProps) {
  const generated = useId();
  const inputId = id ?? generated;
  return (
    <div className="flex min-w-0 items-center gap-2">
      <label htmlFor={inputId} className="sr-only">
        {label}
      </label>
      <Icon name="search" />
      <Input {...props} id={inputId} type="search" className={`min-w-0 ${props.className ?? ""}`} />
      {onClear && (
        <IconButton
          icon="x"
          label="Wyczyść wyszukiwanie"
          onClick={onClear}
          disabled={props.disabled}
        />
      )}
    </div>
  );
}
