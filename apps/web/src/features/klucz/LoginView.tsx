"use client";

import Link from "next/link";
import { Button } from "@/components/atoms/Button";
import { keyInput, keyLink } from "./KeyView";

export function LoginView() {
  return <section className="-m-4 grid min-h-[calc(100dvh-160px)] overflow-hidden bg-surface md:-m-8 md:grid-cols-[43%_57%]">
    <div className="flex flex-col justify-center gap-5 bg-primary p-8 text-on-primary md:p-12"><span aria-hidden="true" className="flex size-14 items-center justify-center rounded-md bg-surface font-mono text-xl text-primary">{"{ }"}</span><p className="break-words text-3xl font-semibold">Odwołania2JSON</p><p>Z dokumentu PDF do JSON, z dowodem przy każdym polu.</p><p className="text-xs">Prototyp przygotowany na hackathon HackNation 2026. Nie jest serwisem żadnej instytucji publicznej.</p></div>
    <div className="mx-auto flex w-full max-w-[496px] flex-col justify-center gap-5 p-6 sm:p-12"><div aria-label="Język interfejsu" className="flex justify-end gap-2 text-sm text-muted"><span className="inline-flex min-h-11 items-center" lang="pl">PL</span><span aria-hidden="true" className="inline-flex min-h-11 items-center">|</span><button type="button" disabled title="Wersja angielska po MVP" className="min-h-11 px-2" lang="en">EN</button></div><h1 className="text-2xl font-semibold">Zaloguj się</h1><p id="login-info" className="rounded-md bg-subtle p-3 text-sm">Logowanie po MVP. Wersja demonstracyjna działa bez logowania. Mechanizm uwierzytelniania (np. SSO) jest pytaniem otwartym.</p>
      <form aria-describedby="login-info" className="space-y-4"><div><label htmlFor="email" className="mb-2 block text-sm">E-mail</label><input id="email" type="email" disabled className={keyInput} /></div><div><label htmlFor="password" className="mb-2 block text-sm">Hasło</label><div className="flex rounded-md border border-control"><input id="password" type="password" disabled className="min-h-11 min-w-0 flex-1 rounded-md bg-surface px-3" /><button type="button" disabled className="min-h-11 shrink-0 px-2 text-xs text-muted">Pokaż hasło</button></div></div><Button type="submit" disabled className="min-h-11 w-full">Zaloguj</Button></form>
      <p className="text-sm text-muted">Nie masz konta? Poproś administratora.</p><Link className={keyLink} href="/">Przejdź do pulpitu</Link>
    </div>
  </section>;
}
