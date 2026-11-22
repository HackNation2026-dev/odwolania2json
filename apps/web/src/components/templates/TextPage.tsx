import type { ReactNode } from "react";
export function TextPage({
  children,
  title,
  intro,
}: {
  children: ReactNode;
  title: string;
  intro?: string;
}) {
  return (
    <article className="mx-auto min-w-0 max-w-3xl space-y-6 break-words">
      <header>
        <h1 className="text-2xl font-semibold">{title}</h1>
        {intro && <p className="mt-3 text-muted">{intro}</p>}
      </header>
      {children}
    </article>
  );
}
