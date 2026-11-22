import type { ReactNode } from "react";
export function CenteredCard({
  children,
  title,
}: {
  children: ReactNode;
  title?: string;
}) {
  return (
    <div className="flex min-h-[60dvh] min-w-0 items-center justify-center">
      <section className="w-full max-w-[480px] space-y-4 rounded-lg border border-border bg-surface p-6">
        {title && <h1 className="text-xl font-semibold">{title}</h1>}
        {children}
      </section>
    </div>
  );
}
