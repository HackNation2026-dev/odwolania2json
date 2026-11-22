"use client";
import { useId, useState } from "react";
import { Checkbox } from "@/components/atoms";
import { Banner } from "@/components/molecules/Banner";
import { CodeBlock } from "@/components/molecules/CodeBlock";
import { EmptyState } from "@/components/molecules/EmptyState";
export type JsonViewerProps = {
  json: string | null;
  blocked?: boolean;
  blockReason?: string;
};
export function JsonViewer({
  json,
  blocked = false,
  blockReason,
}: JsonViewerProps) {
  const [wrap, setWrap] = useState(true);
  const id = useId();
  if (json === null)
    return (
      <EmptyState
        title="Brak ocenianego JSON"
        description="Rozwiąż przyczynę blokady eksportu."
      />
    );
  return (
    <section aria-label="JSON dokumentu" className="min-w-0 space-y-3">
      {blocked && (
        <Banner tone="warning" title="Podgląd diagnostyczny">
          {blockReason ??
            "Wynik nie przechodzi walidacji. Pobranie i kopiowanie zablokowane."}
        </Banner>
      )}
      <Checkbox
        id={id}
        label="Zawijaj linie"
        checked={wrap}
        onChange={(event) => setWrap(event.target.checked)}
      />
      <CodeBlock
        code={json}
        wrap={wrap}
        copyLabel="Kopiuj JSON"
        copyDisabled={blocked}
        label="Treść JSON"
      />
      <p className="text-xs text-muted">
        Zapisany wynik. Dowody są osobno. Wartości null oznaczają brak
        informacji.
      </p>
    </section>
  );
}
