"use client";

import Link from "next/link";
import { Button } from "@/components/atoms/Button";
import { ThemeToggle } from "@/components/molecules/ThemeToggle";
import { useKeyStatus } from "@/lib/api/hooks";
import { keyLink } from "@/features/klucz/KeyView";

export function SettingsView() {
  const status = useKeyStatus();
  return <section className="max-w-3xl space-y-6"><h1 className="text-3xl font-semibold">Ustawienia</h1>
    <section className="space-y-4 rounded-md border border-border bg-surface p-6 [&_select]:min-h-11"><h2 className="text-xl font-semibold">Wygląd</h2><p className="text-sm text-muted">Wybierz motyw jasny, ciemny lub zgodny z ustawieniami systemu.</p><ThemeToggle /></section>
    <section className="space-y-4 rounded-md border border-border bg-surface p-6"><h2 className="text-xl font-semibold">Klucz API i połączenie</h2>{status.isPending ? <div role="status" className="space-y-3"><p>Wczytywanie konfiguracji…</p><div aria-hidden="true" className="h-12 animate-pulse rounded-md bg-subtle" /></div> : status.isError ? <div role="alert"><p>Nie udało się odczytać stanu klucza.</p><Button variant="secondary" className="mt-3 min-h-11" onClick={() => void status.refetch()}>Spróbuj ponownie</Button></div> : <><p role="status">{status.data.configured ? "✓ Klucz: skonfigurowany" : "! Brak klucza API modelu"}</p><p className="text-sm text-muted">{status.data.lastCheck === "ok" ? "Ostatnia kontrola: powodzenie (symulacja)." : status.data.lastCheck === "error" ? "Ostatnia kontrola: błąd. Popraw konfigurację klucza." : "Nie sprawdzono gotowości."}</p><div className="flex flex-wrap gap-3"><Link href="/klucz" className={keyLink}>{status.data.configured ? "Zmień klucz" : "Skonfiguruj klucz"}</Link><Link href="/klucz/kontrola" className={keyLink}>Kontrola połączenia</Link></div></>}
    </section>
  </section>;
}
