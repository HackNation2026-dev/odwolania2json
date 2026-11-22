"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { SiteHeader } from "./SiteHeader";
import { SideNav } from "./SideNav";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() ?? "/";
  // Ekrany klucza i logowania (F62-F64) są bez menu bocznego, jak na makietach.
  const bare = pathname.startsWith("/klucz") || pathname.startsWith("/login");
  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:p-3">
        Przejdź do treści
      </a>
      <SiteHeader />
      <div
        role="note"
        className="flex items-center justify-center gap-2 border-b border-border bg-[var(--partial-bg)] px-4 py-1.5 text-center text-xs text-[var(--partial-fg)]"
      >
        <span aria-hidden>▲</span>
        Tryb demonstracyjny. Tylko dane syntetyczne. Bez logowania.
      </div>
      <div className="flex flex-1 flex-col md:flex-row">
        {!bare && <SideNav pathname={pathname} />}
        <main
          id="main"
          tabIndex={-1}
          className="min-w-0 flex-1 p-4 outline-none md:p-8"
        >
          {children}
        </main>
      </div>
      <footer className="border-t border-border px-4 py-3 text-xs text-muted md:px-8">
        Dane syntetyczne · wersja demonstracyjna
      </footer>
    </div>
  );
}
