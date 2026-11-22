export default function Loading() {
  return <div role="status" aria-live="polite" aria-label="Wczytywanie strony" className="space-y-4"><p>Wczytywanie…</p><div aria-hidden className="h-8 w-2/3 animate-pulse rounded-md bg-subtle" /><div aria-hidden className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((id) => <div key={id} className="h-40 animate-pulse rounded-lg bg-subtle" />)}</div></div>;
}
