"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { useKeyStatus, useRunSelfCheck } from "@/lib/api/hooks";
import type { CheckStep } from "@/lib/api/schemas";
import { keyLink } from "./KeyView";

const initialSteps: CheckStep[] = [
  { id: "connection", label: "Połączenie z endpointem", state: "pending", detail: null },
  { id: "authorization", label: "Autoryzacja klucza", state: "pending", detail: null },
  { id: "model", label: "Dostępność i zgodność modelu z konfiguracją", state: "pending", detail: null },
  { id: "region", label: "Region usługi i licencja", state: "pending", detail: null },
  { id: "ocr", label: "Gotowość OCR", state: "pending", detail: null },
];
const states = { pending: "Oczekuje", running: "W toku", ok: "Powodzenie", error: "Błąd" };
const icons = { pending: "·", running: "◌", ok: "✓", error: "×" };

export function SelfCheckView() {
  const status = useKeyStatus();
  const check = useRunSelfCheck();
  const [steps, setSteps] = useState(initialSteps);
  const failed = steps.some((step) => step.state === "error") || check.isError || status.data?.lastCheck === "error";
  const success = steps.every((step) => step.state === "ok") || (!check.isPending && !failed && status.data?.lastCheck === "ok");
  const blocked = failed && status.data?.lastCheck !== "never";
  const completed = steps.filter((step) => step.state === "ok").length;
  const visibleSteps = success ? steps.map((step) => ({ ...step, state: "ok" as const })) : steps;
  function run() { setSteps(initialSteps); check.mutate(setSteps); }

  return <section className="space-y-5">
    <h1 className="text-2xl font-semibold">Kontrola połączenia (self-check) po podaniu klucza</h1>
    <p className="text-sm text-muted">401 i 403 nie uruchamiają pętli ponowień. Ekran nie pokazuje klucza po wysłaniu.</p>
    {status.isPending ? <div role="status" className="space-y-3"><p>Wczytywanie konfiguracji…</p><div aria-hidden="true" className="h-32 animate-pulse rounded-md bg-subtle" /></div> : status.isError ? <div role="alert"><p>Nie udało się odczytać konfiguracji.</p><Button variant="secondary" className="mt-3 min-h-11" onClick={() => void status.refetch()}>Spróbuj ponownie</Button></div> : !status.data.configured ? <div className="space-y-4 rounded-md border border-border bg-surface p-6"><h2 className="font-semibold">Brak klucza API modelu</h2><p>Podaj klucz przed uruchomieniem kontroli.</p><Link href="/klucz" className={keyLink}>Wpisz klucz API</Link></div> : <div className={`max-w-[440px] space-y-5 rounded-md border bg-surface p-6 ${failed ? "border-[var(--error-fg)]" : success ? "border-[var(--full-fg)]" : "border-border"}`} aria-busy={check.isPending}>
      <StatusBadge status={failed ? "error" : success ? "full" : "running"} />
      <h2 className={`text-xl font-semibold ${failed ? "text-[var(--error-fg)]" : success ? "text-[var(--full-fg)]" : "text-fg"}`}>{failed ? steps.some((step) => step.detail?.includes("401")) ? "API odrzuciło uwierzytelnienie (401)" : "Kontrola zakończona błędem" : success ? "Klucz przyjęty" : check.isPending ? `Sprawdzanie klucza… ${Math.min(completed + 1, 5)} z 5` : "Sprawdź gotowość usług"}</h2>
      <ol aria-label="Kroki kontroli" aria-live="polite" className="space-y-3 text-sm">{visibleSteps.map((step) => <li key={step.id} className="flex gap-3"><span aria-hidden="true">{icons[step.state]}</span><div><span>{initialSteps.find((item) => item.id === step.id)?.label}: {failed && step.state === "pending" ? "Pominięto" : states[step.state]}</span>{step.detail && <p className="mt-1 text-muted">{step.detail}</p>}</div></li>)}</ol>
      {failed && <div role="alert" className="space-y-2 text-sm text-[var(--error-fg)]"><p>{check.isError ? "Nie udało się ukończyć kontroli. Sprawdź konfigurację i połączenie." : "Sprawdź klucz po stronie dostawcy i uprawnienia. Nie ponawiamy automatycznie. Kod: llm_authorization."}</p><p>Popraw konfigurację przed kolejną kontrolą.</p></div>}
      {success && <div role="status" className="space-y-2 text-sm"><p>✓ Wszystkie 5 kontroli zakończone powodzeniem (symulacja).</p><p>Klucz jest skonfigurowany. {status.data.persisted ? "Zapis na serwerze: włączony za zgodą." : "Zapis w pliku: wyłączony."}</p></div>}
      <p className="text-xs text-muted">Tryb demonstracyjny: wyniki mocka nie potwierdzają rzeczywistej licencji, lokalizacji modelu ani gotowości OCR. OCR tymczasowy (shim): docelowy model nie jest podłączony.</p>
      <div className="flex flex-wrap gap-3">{success ? <Link href="/" className={`${keyLink} bg-primary text-on-primary hover:bg-primary`}>Przejdź do pulpitu</Link> : blocked ? <Link href="/klucz" className={`${keyLink} bg-primary text-on-primary hover:bg-primary`}>Wpisz klucz ponownie</Link> : <Button className="min-h-11" disabled={check.isPending} onClick={run}>{check.isPending ? "Kontrola w toku…" : "Sprawdź ponownie"}</Button>}<Link href="/jak-to-dziala" className={keyLink}>Gotowość i modele</Link></div>
    </div>}
  </section>;
}
