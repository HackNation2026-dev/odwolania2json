"use client";
import { Card } from "@/components/atoms/Card";
import { Button } from "@/components/atoms/Button";
import { useChooseClass, useClasses, useRetryDocument } from "@/lib/api/hooks";
import type { DocumentRecord } from "@/lib/api/schemas";
import { partialReasons } from "./format";
import s from "./dokument.module.css";

export function DocumentException({ doc }: { doc: DocumentRecord }) {
  const retry = useRetryDocument();
  const choose = useChooseClass();
  const classes = useClasses();
  return (
    <>
      {doc.status === "error" && (
        <>
          <div
            role="alert"
            className={`${s.card} bg-[var(--error-bg)] text-[var(--error-fg)]`}
          >
            <h2 className="font-semibold">
              × Nie udało się przetworzyć dokumentu
            </h2>
            <p>
              Wynik ekstrakcji nie został zapisany. Nie jest to pusty wynik ani
              dokument spoza zakresu. Nie użyto starego wyniku z pamięci
              podręcznej.
            </p>
          </div>
          <Card as="section" className={s.card}>
            <h3 className="font-semibold">Szczegóły błędu</h3>
            <p>Kod: {doc.errorCode ?? "Nieznany błąd techniczny"}</p>
            <p>Odczytano stron: {doc.pages}</p>
            <p>Nie zapisano pliku wynikowego. Eksport JSON jest zablokowany.</p>
            <Button
              className="mt-3 min-h-11"
              disabled={retry.isPending}
              onClick={() => retry.mutate(doc.id)}
            >
              {retry.isPending ? "Ponawianie…" : "Ponów"}
            </Button>
            {retry.error && (
              <p role="alert">
                Nie udało się ponowić analizy. {retry.error.message}
              </p>
            )}
          </Card>
        </>
      )}
      {doc.status === "foreign" && (
        <>
          <div className={s.notice}>
            <h2 className="font-semibold">∅ Dokument spoza zakresu</h2>
            <p>
              Dokument nie należy do aktywnych klas. To nie jest błąd
              techniczny. Wynik to dokładnie {"{}"}, pod nazwą bazową pliku
              wejściowego.
            </p>
          </div>
          <Card as="section" className={s.card}>
            <h3 className="font-semibold">Klasy aktywnego zestawu</h3>
            {classes.data
              ?.filter((c) => c.id !== "obcy")
              .map((c) => (
                <p key={c.id}>• {c.name} — nie rozpoznano</p>
              ))}
          </Card>
          <Card as="section" className={s.card}>
            <h3 className="font-semibold">Przesłanki decyzji</h3>
            <p>
              Silnik oznaczył dokument jako obcy. Przesłanki routera są dostępne
              w sekcji Przebieg przetwarzania. O klasie rozstrzyga treść, nie
              nazwa pliku.
            </p>
          </Card>
          <pre className={s.notice}>{"{}"}</pre>
        </>
      )}
      {doc.status === "ambiguous" && (
        <>
          <div
            className={`${s.card} bg-[var(--ambiguous-bg)] text-[var(--ambiguous-fg)]`}
          >
            <h2 className="font-semibold">
              ? Nie ustalono jednoznacznie klasy dokumentu
            </h2>
            <p>
              Wymaga przeglądu. To nie jest dokument spoza zakresu ani błąd
              techniczny.
            </p>
          </div>
          <Card as="section" className={s.card}>
            <h3 className="font-semibold">Diagnoza i kandydaci</h3>
            <p>
              Wybierz klasę po sprawdzeniu treści. Eksport pozostaje zablokowany
              do rozstrzygnięcia i uzupełnienia wymaganych pól.
            </p>
            {classes.isPending && <p role="status">Wczytywanie kandydatów…</p>}
            {classes.isError && (
              <>
                <p role="alert">Nie udało się wczytać klas.</p>
                <Button className="min-h-11" onClick={() => classes.refetch()}>
                  Wczytaj klasy ponownie
                </Button>
              </>
            )}
            {doc.candidates.map((name) => {
              const candidate = classes.data?.find((c) => c.name === name);
              return (
                <div key={name} className="mt-3">
                  <p>{name}</p>
                  <Button
                    className="mt-1 min-h-11"
                    variant="secondary"
                    disabled={!candidate || choose.isPending}
                    onClick={() =>
                      candidate &&
                      choose.mutate({ id: doc.id, classId: candidate.id })
                    }
                  >
                    Wybierz: {name}
                  </Button>
                </div>
              );
            })}
            {choose.error && (
              <p role="alert">
                Nie udało się wybrać klasy. {choose.error.message}
              </p>
            )}
          </Card>
        </>
      )}
      {doc.status === "multi" && (
        <>
          <div
            className={`${s.card} bg-[var(--running-bg)] text-[var(--running-fg)]`}
          >
            <h2 className="font-semibold">▤ Wiele dokumentów</h2>
            <p>
              Wykryto wiele dokumentów w jednym PDF. Rozdziel plik na osobne
              dokumenty i dodaj je ponownie.
            </p>
          </div>
          <Card as="section" className={s.card}>
            <h3 className="font-semibold">
              Zakresy stron przekazane przez silnik
            </h3>
            <p>
              Plik ma {doc.pages} stron. Granice segmentów nie zostały
              przekazane.
            </p>
          </Card>
          <p className={s.notice}>
            Kontrakt eksportu wielu dokumentów nieustalony. Jeden PDF daje
            najwyżej jeden oceniany JSON; eksport zablokowany do decyzji.
          </p>
        </>
      )}
      {doc.status === "partial" && (
        <section
          className={`${s.partialBanner} bg-[var(--partial-bg)] text-[var(--partial-fg)]`}
        >
          <h2>
            ◐ Wynik częściowy. Sprawdź listę braków ({doc.reasons.length}).
          </h2>
          <p>Braków nie uzupełniamy z innych dokumentów.</p>
          <div className={s.reasonLabels}>
            {doc.reasons.map((reason) => (
              <strong key={reason}>{partialReasons[reason].label}:</strong>
            ))}
          </div>
          <details>
            <summary>Opis powodów braków</summary>
            <ul className="list-disc space-y-1 pl-5">
              {doc.reasons.map((reason) => (
                <li key={reason}>{partialReasons[reason].description}</li>
              ))}
            </ul>
            {!doc.reasons.length && (
              <p>Silnik nie przekazał szczegółowych powodów braków.</p>
            )}
          </details>
        </section>
      )}
      {doc.status === "running" && (
        <section className={s.notice}>
          <h2 className="font-semibold">Analiza w toku</h2>
          <p aria-live="polite">Postęp analizy: {doc.progress ?? 0}%</p>
          <progress
            aria-label="Postęp analizy"
            max={100}
            value={doc.progress ?? 0}
            className="w-full"
          />
          <p>
            Wynik i eksport będą dostępne po zakończeniu analizy i walidacji.
          </p>
        </section>
      )}
    </>
  );
}
