import type { ReactNode, ComponentProps } from "react";
import { Icon } from "@/components/atoms";
export type EmptyStateProps = {
  icon?: ComponentProps<typeof Icon>["name"];
  title: string;
  description?: string;
  action?: ReactNode;
};
export function EmptyState({
  icon = "file",
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div
      role="status"
      className="space-y-3 rounded-lg border border-border bg-surface p-6 text-center"
    >
      <div className="flex justify-center">
        <Icon name={icon} />
      </div>
      <h2 className="text-lg font-semibold">{title}</h2>
      {description && <p className="text-sm text-muted">{description}</p>}
      {action}
    </div>
  );
}
