"use client";
import Link from "next/link";
import { ThemeToggle } from "@/components/molecules/ThemeToggle";
export function SiteHeader() {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2 md:px-8">
      <Link href="/" className="flex items-center gap-3 text-lg font-semibold">
        <span
          aria-hidden
          className="grid size-8 place-items-center rounded-md bg-primary font-mono text-xs text-on-primary"
        >
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
          <span
            aria-hidden
            className="size-2 rounded-full bg-[var(--full-fg)]"
          />
          Gotowość i modele
        </Link>
        <Link
          href="/dodaj"
          className="inline-flex min-h-10 items-center gap-2 rounded-md bg-primary px-3 text-sm font-medium text-on-primary hover:opacity-90"
        >
          <span aria-hidden>＋</span> Nowa analiza
        </Link>
      </div>
    </header>
  );
}
