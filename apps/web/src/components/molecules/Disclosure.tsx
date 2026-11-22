import type { DetailsHTMLAttributes, ReactNode } from "react";
import { Icon } from "@/components/atoms";
export function Disclosure({
  title,
  children,
  ...props
}: Omit<DetailsHTMLAttributes<HTMLDetailsElement>, "title"> & {
  title: ReactNode;
}) {
  return (
    <details
      {...props}
      className="group rounded-lg border border-border bg-surface p-3"
    >
      <summary className="flex min-h-11 cursor-pointer items-center gap-2 font-medium">
        <Icon name="chevron-right" className="group-open:rotate-90" />
        {title}
      </summary>
      <div className="pt-3">{children}</div>
    </details>
  );
}
