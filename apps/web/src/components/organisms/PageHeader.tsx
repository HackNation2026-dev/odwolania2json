import type { ReactNode } from "react";
import {
  Breadcrumbs,
  type Breadcrumb,
} from "@/components/molecules/Breadcrumbs";
export type PageHeaderProps = {
  breadcrumbs?: Breadcrumb[];
  title: string;
  subtitle?: string;
  actions?: ReactNode;
};
export function PageHeader({
  breadcrumbs,
  title,
  subtitle,
  actions,
}: PageHeaderProps) {
  return (
    <header className="mb-6 space-y-2">
      {breadcrumbs && <Breadcrumbs items={breadcrumbs} />}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="break-words text-2xl font-semibold">{title}</h1>
          {subtitle && <p className="mt-2 text-sm text-muted">{subtitle}</p>}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
    </header>
  );
}
