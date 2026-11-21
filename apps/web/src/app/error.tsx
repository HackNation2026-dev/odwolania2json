"use client";

import Link from "next/link";
import { Button } from "@/components/atoms/Button";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <div role="alert" className="mx-auto max-w-xl space-y-4 py-12"><h1 className="text-2xl font-semibold">Nie udało się wyświetlić strony</h1><p>Wystąpił błąd techniczny. Spróbuj ponownie lub wróć do pulpitu.</p><div className="flex flex-wrap gap-3"><Button className="min-h-11" onClick={reset}>Spróbuj ponownie</Button><Link href="/" className="inline-flex min-h-11 items-center rounded-md border border-control px-4">Wróć do pulpitu</Link></div></div>;
}
