"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";

export default function NotFound() {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, []);
  return <div className="mx-auto max-w-xl space-y-4 py-12"><p className="text-muted">404</p><h1 ref={heading} tabIndex={-1} className="text-2xl font-semibold">Nie znaleziono strony</h1><p>Sprawdź adres lub przejdź do pulpitu, aby rozpocząć pracę.</p><Link href="/" className="inline-flex min-h-11 items-center rounded-md bg-primary px-4 text-on-primary">Wróć do pulpitu</Link><Link href="/dodaj" className="flex min-h-11 items-center underline">Przejdź do nowej analizy</Link></div>;
}
