import Link from "next/link";
import type { ReactNode } from "react";
import { ThemeToggle } from "@/components/molecules/ThemeToggle";

const nav = [
  { href: "/", label: "Pulpit" },
  { href: "/dodaj", label: "Dodaj dokumenty" },
  { href: "/dokumenty", label: "Dokumenty" },
  { href: "/klasy", label: "Klasy" },
  { href: "/jak-to-dziala", label: "Jak to działa" },
  { href: "/ustawienia", label: "Ustawienia" },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:p-3">
        Przejdź do treści
      </a>
      <div role="note" className="bg-subtle px-4 py-1 text-center text-xs text-muted">
        Tryb demonstracyjny. Tylko dane syntetyczne. Bez logowania.
      </div>
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2 md:px-8">
        <Link href="/" className="text-lg font-semibold">
          Odwołania2JSON
        </Link>
        <ThemeToggle />
      </header>
      <div className="flex flex-1 flex-col md:flex-row">
        <nav aria-label="Główna" className="border-b border-border bg-surface md:w-60 md:border-r md:border-b-0">
          <ul className="flex gap-1 overflow-x-auto p-2 md:flex-col">
            {nav.map((n) => (
              <li key={n.href}>
                <Link href={n.href} className="flex min-h-10 items-center whitespace-nowrap rounded-md px-3 text-sm hover:bg-subtle">
                  {n.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <main id="main" className="min-w-0 flex-1 p-4 md:p-8">
          {children}
        </main>
      </div>
      <footer className="border-t border-border px-4 py-3 text-xs text-muted md:px-8">Dane syntetyczne · wersja demonstracyjna</footer>
    </div>
  );
}
