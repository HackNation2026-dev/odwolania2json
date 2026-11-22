"use client";
import Link from "next/link";
import { ThemeToggle } from "@/components/molecules/ThemeToggle";
import { Button } from "@/components/atoms/Button";

export function SiteHeader({ onOpenMenu }: { onOpenMenu?: () => void }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2 md:px-8">
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          className="min-h-11 md:hidden"
          aria-label="Otwórz menu"
          onClick={onOpenMenu}
        >
          ☰
        </Button>
        <Link
          href="/"
          className="flex items-center gap-3 text-sm font-semibold md:text-lg"
        >
          <span
            aria-hidden
            className="hidden size-8 md:grid place-items-center rounded-md bg-primary font-mono text-xs text-on-primary"
          >
            {"{ }"}
          </span>
          Odwołania2JSON
        </Link>
      </div>
      <Link
        href="/dodaj"
        aria-label="Nowa analiza"
        className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md bg-primary text-xl text-on-primary md:hidden"
      >
        ＋
      </Link>
      <div className="hidden flex-wrap items-center gap-2 md:flex">
        <ThemeToggle />
        <Link
          href={{ pathname: "/gotowosc" }}
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
