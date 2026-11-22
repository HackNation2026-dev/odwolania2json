import type { ReactNode } from "react";
export function AppPage({
  header,
  children,
}: {
  header: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="mx-auto w-full min-w-0 max-w-7xl">
      {header}
      <div className="min-w-0 space-y-6">{children}</div>
    </div>
  );
}
