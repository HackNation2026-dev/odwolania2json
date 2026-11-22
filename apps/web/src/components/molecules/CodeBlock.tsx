"use client";
import { useState } from "react";
import { Button } from "@/components/atoms";
export type CodeBlockProps = {
  code: string;
  wrap?: boolean;
  copyLabel?: string;
  copyDisabled?: boolean;
  label?: string;
};
export function CodeBlock({
  code,
  wrap = true,
  copyLabel = "Kopiuj kod",
  copyDisabled = false,
  label = "Kod",
}: CodeBlockProps) {
  const [message, setMessage] = useState("");
  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setMessage("Skopiowano.");
    } catch {
      setMessage("Nie udało się skopiować. Zaznacz tekst ręcznie.");
    }
  }
  return (
    <div className="min-w-0 space-y-2">
      <Button variant="secondary" disabled={copyDisabled} onClick={copy}>
        {copyLabel}
      </Button>
      <pre
        tabIndex={code ? 0 : undefined}
        role={code ? "region" : undefined}
        aria-label={code ? label : undefined}
        className={`max-w-full overflow-auto rounded-lg border border-border bg-subtle p-4 text-sm ${wrap ? "whitespace-pre-wrap break-words" : "whitespace-pre"}`}
      >
        <code>{code}</code>
      </pre>
      <p role="status" className="text-sm">
        {message}
      </p>
    </div>
  );
}
