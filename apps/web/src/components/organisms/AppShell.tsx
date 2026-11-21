"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { ThemeToggle } from "@/components/molecules/ThemeToggle";
import { cn } from "@/lib/cn";

type NavItem = { href: string; label: string; icon: string; match: (p: string) => boolean };

const main: NavItem[] = [
  { href: "/", label: "Pulpit", icon: "▤", match: (p) => p === "/" },
  { href: "/dodaj", label: "Nowa analiza", icon: "＋", match: (p) => p.startsWith("/dodaj") },
  { href: "/dokumenty", label: "Sprawy", icon: "▦", match: (p) => p.startsWith("/dokumenty") },
  { href: "/klasy", label: "Klasy dokumentów", icon: "▣", match: (p) => p.startsWith("/klasy") },
  { href: "/jak-to-dziala", label: "Jak to działa", icon: "ⓘ", match: (p) => p.startsWith("/jak-to-dziala") },
];
const admin: NavItem[] = [
  { href: "/uzytkownicy", label: "Użytkownicy i role", icon: "☺", match: (p) => p.startsWith("/uzytkownicy") },
  { href: "/dziennik", label: "Dziennik zdarzeń", icon: "≣", match: (p) => p.startsWith("/dziennik") },
  { href: "/ustawienia", label: "Ustawienia", icon: "⚙", match: (p) => p.startsWith("/ustawienia") || p.startsWith("/klucz") },
];

function NavList({ items, pathname }: { items: NavItem[]; pathname: string }) {
  return (
    <ul className="flex gap-1 md:flex-col">
      {items.map((n) => {
        const active = n.match(pathname);
        return (
          <li key={n.href}>
            <Link
              href={n.href as never}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-11 items-center gap-2 whitespace-nowrap rounded-md border px-3 text-sm md:min-h-10",
                active ? "border-border bg-raised font-medium shadow-[var(--shadow-1)]" : "border-transparent hover:bg-subtle",
              )}
            >
              <span aria-hidden className="w-4 text-center text-muted">
                {n.icon}
              </span>
              {n.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() ?? "/";
  // Ekrany klucza i logowania (F62-F64) są bez menu bocznego, jak na makietach.
  const bare = pathname.startsWith("/klucz") || pathname.startsWith("/login");
  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:p-3">
        Przejdź do treści
      </a>
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2 md:px-8">
        <Link href="/" className="flex items-center gap-3 text-lg font-semibold">
          <span aria-hidden className="grid size-8 place-items-center rounded-md bg-primary font-mono text-xs text-on-primary">
            {"{ }"}
          </span>
          Odwołania2JSON
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <ThemeToggle />
          <Link
            href="/jak-to-dziala"
            className="inline-flex min-h-10 items-center gap-2 rounded-md border border-control bg-surface px-3 text-sm hover:bg-subtle"
          >
            <span aria-hidden className="size-2 rounded-full bg-[var(--full-fg)]" />
            Gotowość i modele
          </Link>
          <Link href="/dodaj" className="inline-flex min-h-10 items-center gap-2 rounded-md bg-primary px-3 text-sm font-medium text-on-primary hover:opacity-90">
            <span aria-hidden>＋</span> Nowa analiza
          </Link>
        </div>
      </header>
      <div role="note" className="flex items-center justify-center gap-2 border-b border-border bg-[var(--partial-bg)] px-4 py-1.5 text-center text-xs text-[var(--partial-fg)]">
        <span aria-hidden>▲</span>
        Tryb demonstracyjny. Tylko dane syntetyczne. Bez logowania.
      </div>
      <div className="flex flex-1 flex-col md:flex-row">
        {!bare && (
        <nav aria-label="Główna" className="border-b border-border bg-subtle md:w-60 md:shrink-0 md:border-r md:border-b-0">
          <div className="flex flex-col gap-3 overflow-x-auto p-2 md:p-3">
            <NavList items={main} pathname={pathname} />
            <div className="hidden md:block">
              <p className="px-3 pb-1 text-xs font-medium tracking-wide text-muted">ADMINISTRACJA</p>
            </div>
            <NavList items={admin} pathname={pathname} />
          </div>
        </nav>
        )}
        <main id="main" tabIndex={-1} className="min-w-0 flex-1 p-4 outline-none md:p-8">
          {children}
        </main>
      </div>
      <footer className="border-t border-border px-4 py-3 text-xs text-muted md:px-8">Dane syntetyczne · wersja demonstracyjna</footer>
    </div>
  );
}
