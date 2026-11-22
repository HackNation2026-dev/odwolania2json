"use client";

import { Button } from "@/components/atoms/Button";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { Card } from "@/components/atoms/Card";
import Link from "next/link";
import { ConfigurationFieldList } from "@/components/molecules/ConfigurationFieldList";
import { Banner } from "@/components/molecules/Banner";
import {
  ConfigurationError,
  useClassConfiguration,
} from "./ConfigurationGuard";
import { useClasses, useSystemInfo } from "@/lib/api/hooks";

export function ClassesView() {
  const query = useClasses();
  const system = useSystemInfo();
  const configuration = useClassConfiguration();
  const activeVersion = configuration.data?.find(
    (version) => version.active,
  )?.version;
  if (
    query.isSuccess &&
    (!query.data.filter((cls) => cls.id !== "obcy").length ||
      (configuration.isSuccess && configuration.blocked))
  ) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Klasy dokumentów</h1>
        <ConfigurationError />
      </div>
    );
  }
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">Klasy dokumentów</h1>
          <Button disabled variant="secondary" className="min-h-11">
            Nowa klasa (po MVP)
          </Button>
        </div>
        <p className="max-w-4xl text-muted">
          Każdy rodzaj dokumentu jest opisany jednym plikiem YAML: sygnały
          rozpoznania, pola, typy, formaty i reguły. Dodanie klasy lub pola
          korzystającego z istniejących mechanizmów nie wymaga zmiany kodu. Nowy
          mechanizm wymaga rozszerzenia silnika.
        </p>
      </header>
      {activeVersion === "v2" && (
        <Banner tone="info" title="Aktywny zestaw: v2 · demonstracja">
          Lista przedstawia bazowe kontrakty v1. Dodatkowe pole demonstracyjne
          przelewu jest widoczne w szczegółach klasy i podsumowaniu zestawu.
        </Banner>
      )}
      {query.isPending || configuration.isPending ? (
        <div role="status" aria-live="polite" className="space-y-3">
          <p>Wczytywanie klas…</p>
          <div
            aria-hidden
            className="h-36 animate-pulse rounded-lg bg-subtle"
          />
        </div>
      ) : query.isError || configuration.isError ? (
        <div
          role="alert"
          className="space-y-3 rounded-lg border border-control bg-surface p-4"
        >
          <p>
            Nie udało się wczytać klas. Sprawdź połączenie i spróbuj ponownie.
          </p>
          <Button
            className="min-h-11"
            onClick={() => {
              void query.refetch();
              void configuration.refetch();
            }}
          >
            Spróbuj ponownie
          </Button>
        </div>
      ) : query.data.length === 0 ? (
        <ConfigurationError />
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          {query.data
            .filter((c) => c.id !== "obcy")
            .map((cls) => (
              <Card as="article" key={cls.id} className="space-y-3">
                <h2 className="text-lg font-semibold">{cls.name}</h2>
                <p className="break-all font-mono text-sm text-muted">
                  {cls.id}
                </p>
                <p className="inline-flex rounded-sm bg-[var(--full-bg)] px-2 py-1 text-xs text-[var(--full-fg)]">
                  {activeVersion === "v2"
                    ? "v1 · kontrakt"
                    : `${activeVersion ?? system.data?.versions.classes ?? "Wersja niepobrana"} · aktywna`}
                </p>
                <p className="text-sm text-muted">{cls.description}</p>
                <p className="text-sm">Liczba pól: {cls.fields.length}</p>
                <Link
                  href={{ pathname: `/klasy/${cls.id}` }}
                  className="inline-flex min-h-11 items-center text-sm underline"
                >
                  Szczegóły
                </Link>
                <details>
                  <summary className="min-h-11 cursor-pointer py-3 text-sm underline">
                    Szczegóły pól — {cls.name}
                  </summary>
                  <ConfigurationFieldList
                    fields={[...cls.containers, ...cls.fields]}
                  />
                </details>
              </Card>
            ))}
        </div>
      )}
      <section
        className="rounded-lg border border-control bg-subtle p-4"
        aria-labelledby="foreign-title"
      >
        <h2 id="foreign-title" className="font-semibold">
          ∅ Dokument spoza zakresu
        </h2>
        <p>
          Wynik: pusty JSON <code>{"{}"}</code>. Nie jest konfigurowaną klasą.
          Wymaga potwierdzenia na podstawie odczytanej treści.
        </p>
      </section>
      <section className="space-y-4" aria-labelledby="yaml-title">
        <h2 id="yaml-title" className="text-xl font-semibold">
          Dodanie klasy i pola bez edytora w GUI (P0): pokaz rozbudowy
          konfiguracją
        </h2>
        <p className="text-muted">
          Rozbudowa odbywa się przez YAML poza GUI. Poniższy przebieg jest
          instrukcją demonstracji na danych syntetycznych, poza kontraktami
          konkursowymi.
        </p>
        <ol className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {[
            [
              "Dopisz klasę w YAML",
              "W osobnym zestawie dodaj klasę Nota testowa i pole numer_noty. Oryginały organizatora pozostaw bez zmian.",
            ],
            [
              "Przeładuj konfigurację",
              "Uruchom ponownie serwer z kompletnym zestawem. Odświeżenie GUI jedynie odczytuje konfigurację.",
            ],
            [
              "Analizuj syntetyczny PDF",
              "Nowa analiza powinna rozpoznać Notę testową i odczytać numer_noty, np. NT-2026-001.",
            ],
            [
              "Sprawdź nowe pole",
              "Porównaj formularz, JSON i dowód: stronę, cytat oraz współrzędne. Sam formularz nie potwierdza ekstrakcji.",
            ],
            [
              "Dodaj drugie pole",
              "Dopisz oznaczenie_sprawy, np. DEMO-42. Przeładuj, przeanalizuj ponownie i sprawdź JSON oraz osobne dowody. Przywróć oficjalny zestaw.",
            ],
          ].map(([title, text], i) => (
            <Card as="li" key={title} className="space-y-3">
              <h3 className="font-medium">
                {i + 1}. {title}
              </h3>
              <p className="text-sm text-muted">{text}</p>
              {i === 0 && (
                <>
                  <pre className="whitespace-pre-wrap break-all rounded-md bg-subtle p-2 text-xs">
                    {
                      "klasa: nota_testowa\npola:\n  - klucz: numer_noty\n    typ: tekst\n    etykieta: Numer noty"
                    }
                  </pre>
                  <p className="text-xs text-muted">
                    Schemat poglądowy; format YAML według konfiguracji silnika.
                  </p>
                </>
              )}
              {i === 1 && (
                <>
                  <p className="rounded-md bg-subtle p-2 text-xs">
                    Zestaw klas (YAML):{" "}
                    {activeVersion ?? system.data?.versions.classes ?? "Nie pobrano"}
                  </p>
                  <p className="text-xs text-[var(--error-fg)]">
                    Przy błędzie YAML: „Błąd konfiguracji. Brak poprawnego
                    zestawu klas. Analiza zablokowana.”
                  </p>
                </>
              )}
              {i === 2 && (
                <div className="space-y-2 rounded-md bg-subtle p-2 text-xs">
                  <p>Przykład po analizie: nota-testowa.pdf</p>
                  <StatusBadge status="full" />
                </div>
              )}
              {i === 3 && (
                <div className="space-y-2 rounded-md bg-subtle p-2 text-xs">
                  <p className="font-medium">Numer noty · numer_noty</p>
                  <p>NT-2026-001</p>
                  <p>
                    Przykładowy dowód: str. 1, „Nota nr NT-2026-001”; źródło:
                    tekst.
                  </p>
                </div>
              )}
              {i === 4 && (
                <>
                  <pre className="whitespace-pre-wrap break-all rounded-md bg-subtle p-2 text-xs">
                    {
                      '{\n  "numer_noty": "NT-2026-001",\n  "oznaczenie_sprawy": "DEMO-42"\n}'
                    }
                  </pre>
                  <p className="break-all text-xs text-muted">
                    Dowody osobno: evidence/nota-testowa.json
                  </p>
                </>
              )}
            </Card>
          ))}
        </ol>
        <p className="rounded-lg bg-subtle p-4 text-sm">
          Zestaw klas aktywuje się atomowo. Częściowo wczytany nowy zestaw nie
          zmienia aktywnego. Niepoprawny YAML pozostawia poprzedni poprawny
          zestaw, jeśli jest dostępny; w przeciwnym razie analiza jest
          zablokowana. Historyczne wyniki zachowują swój zestaw.
        </p>
        <p className="text-sm text-muted">
          Wersja zestawu: {activeVersion ?? system.data?.versions.classes ?? "Nie pobrano"}.
          Liczba pól wyliczonych: niedostępna w demonstracyjnym API.
        </p>
      </section>
    </div>
  );
}
