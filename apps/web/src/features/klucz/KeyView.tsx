"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { useKeyStatus, useSaveKey } from "@/lib/api/hooks";

export const keyLink = "inline-flex min-h-11 items-center justify-center rounded-md border border-control px-4 text-sm hover:bg-subtle";
export const keyInput = "min-h-11 w-full min-w-0 rounded-md border border-control bg-surface px-3 text-fg disabled:opacity-60";

export function KeyView() {
  const status = useKeyStatus();
  const save = useSaveKey();
  const [value, setValue] = useState("");
  const [visible, setVisible] = useState(false);
  const [persist, setPersist] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const request = useRef<{ value: string; persist: boolean } | null>(null);
  useEffect(() => () => { if (request.current) request.current.value = ""; }, []);
  const configured = saved || status.data?.configured;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!value.trim()) { setError("Podaj klucz API."); return; }
    setError("");
    const input = { value, persist };
    request.current = input;
    setValue("");
    setVisible(false);
    save.mutate(input, {
      onSuccess: () => { input.value = ""; setSaved(true); setEditing(false); save.reset(); },
      onError: () => { input.value = ""; setError("Nie udało się zapisać klucza. Wpisz go ponownie i spróbuj jeszcze raz."); save.reset(); },
    });
  }

  return <section aria-labelledby="key-title" className="mx-auto my-6 max-w-[600px] space-y-5 rounded-md border border-border bg-surface p-5 sm:my-8 sm:p-8">
    {!configured && <p className="rounded-md border border-control bg-[var(--partial-bg)] p-3 text-sm text-[var(--partial-fg)]">▲ Analiza dokumentów jest zablokowana do czasu podania klucza.</p>}
    <h1 id="key-title" className="text-2xl font-semibold">{configured && !editing ? "Klucz API skonfigurowany" : "Brak klucza API modelu"}</h1>
    {status.isPending ? <div role="status" className="space-y-3"><p>Wczytywanie konfiguracji…</p><div aria-hidden="true" className="h-11 animate-pulse rounded-md bg-subtle" /></div> : status.isError ? <div role="alert"><p>Nie udało się odczytać konfiguracji.</p><Button variant="secondary" className="mt-3 min-h-11" onClick={() => void status.refetch()}>Spróbuj ponownie</Button></div> : configured && !editing ? <div className="space-y-4">
      <p role="status">✓ Klucz: skonfigurowany</p>
      <p className="text-sm text-muted">Wartość klucza nie jest wyświetlana. {status.data.persisted ? "Wyrażono zgodę na zapis na serwerze." : "Zapis na dysku jest wyłączony."}</p>
      <div className="flex flex-wrap gap-3"><Link className={keyLink} href="/klucz/kontrola">Sprawdź połączenie</Link><Button variant="secondary" className="min-h-11" onClick={() => { setEditing(true); setSaved(false); }}>Zmień klucz</Button></div>
    </div> : <>
      <p className="text-sm text-muted">Nie znaleziono klucza w konfiguracji serwera (zmienna LLM_API_KEY). Podaj go tutaj, a sprawdzimy połączenie, zanim przejdziesz dalej.</p>
      <form noValidate onSubmit={submit} className="space-y-4">
        <div className="space-y-2"><label htmlFor="api-key" className="block text-sm">Klucz API</label><div className="flex rounded-md border border-control bg-surface"><input id="api-key" name="api-key" type={visible ? "text" : "password"} autoComplete="off" spellCheck={false} placeholder="Wklej klucz API" className="min-h-11 min-w-0 flex-1 rounded-md bg-surface px-3 text-fg disabled:opacity-60" value={value} onChange={(e) => { setValue(e.target.value); setError(""); }} aria-invalid={!!error} aria-describedby={error ? "key-error key-help" : "key-help"} disabled={save.isPending} /><button type="button" aria-label={visible ? "Ukryj klucz" : "Pokaż klucz"} aria-pressed={visible} aria-controls="api-key" disabled={save.isPending} onClick={() => setVisible((current) => !current)} className="min-h-11 shrink-0 rounded-md px-3 text-xs text-muted hover:bg-subtle">{visible ? "Ukryj" : "Pokaż"}</button></div>
          <p id="key-help" className="text-xs text-muted">Klucz nie jest zapisywany w przeglądarce ani w repozytorium. Domyślnie trafia tylko do pamięci serwera i znika po jego restarcie.</p></div>
        <label className="flex min-h-11 items-start gap-3 rounded-md bg-subtle p-3 text-sm"><input type="checkbox" checked={persist} onChange={(e) => setPersist(e.target.checked)} className="mt-1 size-5 shrink-0" disabled={save.isPending} /><span>Zapamiętaj klucz na tym serwerze (plik z ograniczonymi uprawnieniami). Wymaga Twojej zgody; domyślnie wyłączone.</span></label>
        {error && <p id="key-error" role="alert" className="text-sm text-[var(--error-fg)]">{error}</p>}
        <div className="flex flex-wrap gap-3"><Button type="submit" className="min-h-11" disabled={save.isPending}>{save.isPending ? "Zapisywanie…" : "Sprawdź i zapisz"}</Button><Link href="/" className={keyLink}>Wróć</Link></div>
      </form>
      <p className="text-xs text-muted">Po zapisie uruchom kontrolę: połączenie, autoryzacja, dostępność i zgodność modelu, region usługi, gotowość OCR. Możesz też ustawić zmienną LLM_API_KEY i uruchomić serwer ponownie.</p>
    </>}
    <p className="text-xs text-muted">Prototyp: konfigurację symuluje mock. Do testów używaj wyłącznie fikcyjnego klucza.</p>
  </section>;
}
