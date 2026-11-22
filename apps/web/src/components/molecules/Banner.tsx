import type { ReactNode } from "react";
import { Icon } from "@/components/atoms";
export type BannerTone = "info" | "success" | "warning" | "error" | "neutral";
export type BannerProps = {
  tone: BannerTone;
  title?: string;
  children?: ReactNode;
  actions?: ReactNode;
  role?: "alert" | "status" | "note";
};
const tones = {
  info: "bg-[var(--running-bg)] text-[var(--running-fg)]",
  success: "bg-[var(--full-bg)] text-[var(--full-fg)]",
  warning: "bg-[var(--partial-bg)] text-[var(--partial-fg)]",
  error: "bg-[var(--error-bg)] text-[var(--error-fg)]",
  neutral: "bg-subtle text-fg",
};
export function Banner({ tone, title, children, actions, role }: BannerProps) {
  return (
    <div
      role={role ?? (tone === "error" ? "alert" : "status")}
      className={`flex min-w-0 items-start gap-3 rounded-lg p-4 ${tones[tone]}`}
    >
      <Icon
        name={
          tone === "success"
            ? "check"
            : tone === "error" || tone === "warning"
              ? "alert"
              : "info"
        }
      />
      <div className="min-w-0 flex-1 break-words">
        {title && <p className="font-semibold">{title}</p>}
        {children}
        {actions && <div className="mt-3 flex flex-wrap gap-2">{actions}</div>}
      </div>
    </div>
  );
}
