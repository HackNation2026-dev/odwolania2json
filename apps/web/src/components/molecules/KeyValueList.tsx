import type { ReactNode } from "react";
export function KeyValueList({
  items,
}: {
  items: { key: string; label: string; value: ReactNode }[];
}) {
  return (
    <dl className="divide-y divide-border">
      {items.map((item) => (
        <div key={item.key} className="grid min-w-0 gap-1 py-3 sm:grid-cols-2">
          <dt className="text-sm text-muted">{item.label}</dt>
          <dd className="min-w-0 break-words text-sm">
            {item.value ?? "Brak danych"}
          </dd>
        </div>
      ))}
    </dl>
  );
}
