"use client";
import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import s from "./dokument.module.css";
export function DocumentJson({ json, blocked }: { json: string | null; blocked: boolean }) {
  const [wrap, setWrap] = useState(true);
  const [message, setMessage] = useState("");
  if (json === null) return <p className={s.notice}>Brak ocenianego JSON. Rozwiąż przyczynę blokady eksportu.</p>;
  return <><div className="mb-4 flex flex-wrap items-center justify-between gap-3"><Button variant="secondary" className="min-h-11" disabled={blocked} onClick={async () => { try { await navigator.clipboard.writeText(json); setMessage("Skopiowano JSON."); } catch { setMessage("Nie udało się skopiować. Zaznacz tekst ręcznie."); } }}>Kopiuj JSON</Button><label className="flex min-h-11 items-center gap-2 text-sm"><input type="checkbox" checked={wrap} onChange={e => setWrap(e.target.checked)} />Zawijaj linie</label></div>
    {blocked && <p className={s.notice}>Podgląd diagnostyczny: wynik nie przechodzi walidacji. Pobranie i kopiowanie zablokowane.</p>}
    <pre tabIndex={0} aria-label="JSON dokumentu" className={`${s.json} ${wrap ? s.wrap : ""}`}><code>{json.split("\n").map((line, i) => <span key={i} className="flex"><span aria-hidden="true" className="mr-4 w-6 shrink-0 select-none text-right text-muted">{i + 1}</span><span className="min-w-0">{line || " "}</span></span>)}</code></pre>
    <p className="mt-3 text-xs text-muted">Zapisany wynik. Dowody są osobno. Wartości null oznaczają brak informacji; powody braków i dowody pozostają poza ocenianym JSON.</p><p role="status">{message}</p></>;
}
