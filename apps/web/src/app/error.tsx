"use client";

import Link from "next/link";
import { Button } from "@/components/atoms/Button";
import { useEffect, useRef } from "react";

export default function ErrorPage({
  error,
  retry,
  reset,
}: {
  error: unknown;
  retry?: () => void;
  reset?: () => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  const digest =
    error instanceof Error &&
    "digest" in error &&
    typeof error.digest === "string" &&
    /^[a-zA-Z0-9-]{1,80}$/.test(error.digest)
      ? error.digest
      : "Niedostępny — podaj czas wystąpienia błędu";
  return (
    <div role="alert" className="mx-auto max-w-xl space-y-4 py-20 text-center">
      <p aria-hidden className="text-6xl font-semibold text-muted">
        500
      </p>
      <h1 ref={heading} tabIndex={-1} className="text-2xl font-semibold">
        Nie udało się wyświetlić strony.
      </h1>
      <p>
        Wystąpił błąd po stronie aplikacji. Dane dokumentu nie są tu pokazywane.
        Ponowienie odczytu strony nie uruchamia ponownie analizy ani zapisu.
      </p>
      <div className="flex flex-col justify-center gap-3 sm:flex-row">
        <Button className="min-h-11" onClick={() => (retry ?? reset)?.()}>
          Spróbuj ponownie
        </Button>
        <Link
          href="/dodaj"
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-control px-4"
        >
          Przejdź do nowej analizy
        </Link>
      </div>
      <p className="break-words text-sm text-muted">
        Identyfikator zdarzenia: {digest}
      </p>
    </div>
  );
}
