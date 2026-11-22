"use client";
import { Button } from "@/components/atoms/Button";
import { useExportDecision } from "@/lib/api/hooks";
import type { DocumentRecord } from "@/lib/api/schemas";
import s from "./dokument.module.css";
export function DocumentExportPolicy({ doc }: { doc: DocumentRecord }) {
  const decision = useExportDecision(doc.id);
  const blockers = (
    <>
      {decision.isPending && (
        <p role="status">Sprawdzanie warunków eksportu…</p>
      )}
      {decision.isError && (
        <div role="alert">
          <p>
            Nie udało się sprawdzić eksportu. Pobranie pozostaje zablokowane.
          </p>
          <Button
            className="min-h-11"
            variant="secondary"
            onClick={() => decision.refetch()}
          >
            Sprawdź eksport ponownie
          </Button>
        </div>
      )}
      {decision.data && (
        <section aria-label="Decyzja eksportu" className={s.notice}>
          <h2 className="font-semibold">
            {decision.data.allowed
              ? "✓ Eksport dozwolony"
              : "! Eksport zablokowany"}
          </h2>
          <p className="text-sm">Wariant A — ścisła walidacja eksportu</p>
          {decision.data.blockers.length > 0 && (
            <ul className="mt-2 list-disc pl-5">
              {decision.data.blockers.map((b) => (
                <li key={`${b.code}-${b.message}`}>{b.message}</li>
              ))}
            </ul>
          )}
        </section>
      )}
    </>
  );
  return (
    <>
      <h2 className="mb-4 text-xl font-semibold">
        Eksport przy brakach i błędach: wariant A (wybrany)
      </h2>
      {blockers}
      <p className={s.card}>
        Brak lub nieczytelność z null niedozwolonym przez schemat blokuje
        pobranie. Błąd techniczny oznacza brak pliku wynikowego. Pełny lub
        częściowy wynik jest dostępny, gdy wszystkie wartości i null są
        dopuszczone.
      </p>
      <section className={s.card}>
        <h3 className="font-semibold">
          Wariant B — jawny eksport konkursowy mimo braków (odrzucony)
        </h3>
        <p>
          Nie jest dostępny w aplikacji. Wynik z brakami niezgodnymi ze
          schematem może zostać odrzucony przez ewaluator.
        </p>
        <Button className="my-3 min-h-11" variant="secondary" disabled>
          Pobierz JSON z brakami (niedostępny)
        </Button>
        <p>
          Błąd techniczny: brak pliku wynikowego. Niejednoznaczny lub wiele
          dokumentów: eksport zablokowany do rozstrzygnięcia.
        </p>
      </section>
      <ul className="list-disc space-y-2 pl-5">
        <li>Braków nie uzupełniamy fikcyjną wartością.</li>
        <li>Dowody i raport są zapisane osobno.</li>
        <li>
          Wynik dokumentu obcego to dokładnie {"{}"} pod nazwą bazową PDF.
        </li>
        <li>Nieprzetworzone strony pozostają jawne.</li>
      </ul>
      {doc.status === "foreign" && (
        <p className={s.notice}>Wynik to dokładnie {"{}"}.</p>
      )}
    </>
  );
}
