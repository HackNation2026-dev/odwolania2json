import type { DocumentStatus } from "@/lib/api/schemas";
import { cn } from "@/lib/cn";

export const statusMeta: Record<DocumentStatus, { label: string; icon: string; tone: string }> = {
  full: { label: "Pełny", icon: "✓", tone: "bg-[var(--full-bg)] text-[var(--full-fg)]" },
  partial: { label: "Częściowy", icon: "◐", tone: "bg-[var(--partial-bg)] text-[var(--partial-fg)]" },
  foreign: { label: "Obcy", icon: "∅", tone: "bg-[var(--foreign-bg)] text-[var(--foreign-fg)]" },
  error: { label: "Błąd techniczny", icon: "!", tone: "bg-[var(--error-bg)] text-[var(--error-fg)]" },
  running: { label: "W toku", icon: "…", tone: "bg-[var(--running-bg)] text-[var(--running-fg)]" },
  ambiguous: { label: "Niejednoznaczny", icon: "?", tone: "bg-[var(--ambiguous-bg)] text-[var(--ambiguous-fg)]" },
  multi: { label: "Wiele dokumentów", icon: "⧉", tone: "bg-[var(--ambiguous-bg)] text-[var(--ambiguous-fg)]" },
};

/** Status zawsze jako ikona + tekst (nie sam kolor). */
export function StatusBadge({ status, className }: { status: DocumentStatus; className?: string }) {
  const m = statusMeta[status];
  return (
    <span data-status={status} className={cn("inline-flex items-center gap-1 rounded-sm px-2 py-0.5 text-xs font-medium", m.tone, className)}>
      <span aria-hidden>{m.icon}</span>
      {m.label}
    </span>
  );
}
