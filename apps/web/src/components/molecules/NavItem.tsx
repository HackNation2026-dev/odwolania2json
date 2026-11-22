import type { ReactNode } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";
export type NavItemProps = {
  href: string;
  label: string;
  icon?: ReactNode;
  active?: boolean;
};
export function NavItem({ href, label, icon, active = false }: NavItemProps) {
  return (
    <Link
      href={href as never}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex min-h-11 items-center gap-2 whitespace-nowrap rounded-md border px-3 text-sm md:min-h-10",
        active
          ? "border-border bg-raised font-medium shadow-[var(--shadow-1)]"
          : "border-transparent hover:bg-subtle",
      )}
    >
      <span aria-hidden="true" className="w-4 text-center text-muted">
        {icon}
      </span>
      {label}
    </Link>
  );
}
