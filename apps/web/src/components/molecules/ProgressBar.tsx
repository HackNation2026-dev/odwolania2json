import { useId } from "react";
export function ProgressBar({
  value,
  label,
}: {
  value: number;
  label: string;
}) {
  const id = useId();
  const normalized = Number.isFinite(value)
    ? Math.max(0, Math.min(100, value))
    : 0;
  return (
    <div className="space-y-2">
      <p id={id} aria-live="polite" className="text-sm">
        {label}: {Math.round(normalized)}%
      </p>
      <div
        role="progressbar"
        aria-labelledby={id}
        aria-valuenow={normalized}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 overflow-hidden rounded bg-subtle"
      >
        <div
          className="h-full bg-primary"
          style={{ width: `${normalized}%` }}
        />
      </div>
    </div>
  );
}
