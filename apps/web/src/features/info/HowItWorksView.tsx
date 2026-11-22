import { Card } from "@/components/atoms/Card";
import Link from "next/link";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import type { DocumentStatus } from "@/lib/api/schemas";
import { SystemInfoCard } from "./SystemInfoCard";

const steps = [
  [
    "Odczyt tekstu z PDF",
    "Warstwa tekstowa PDF razem z geometrią słów. Trwały zapis surowego odczytu pozwala przeliczyć kolejne etapy bez powtarzania OCR.",
  ],
  [
    "Diagnoza stron, OCR według potrzeby",
    "Dla każdej strony: źródło tekstu (PDF, OCR, mieszane), pokrycie i orientacja. Skany trafiają do OCR; brak OCR oznacza stronę nieprzetworzoną, nie dokument obcy.",
  ],
  [
    "Rozpoznanie rodzaju dokumentu",
    "Rodzaj rozpoznajemy po treści, nie po nazwie pliku. Potwierdzony dokument spoza zakresu daje pusty wynik {}.",
  ],
  [
    "Role i kandydaci pól z dowodami",
    "Wzorce odczytują formaty (np. NIP, rachunek), model językowy znaczenie i role. Każda wartość ma cytat ze strony i współrzędne.",
  ],
  [
    "Normalizacja i walidacja",
    "Typy, daty, numery jako tekst albo null, słowniki. Braki są jawne: brak, nie dotyczy, nieczytelne, sprzeczne, nieprzetworzone.",
  ],
  [
    "Zapis JSON, dowodów i raportu",
    "Oceniany JSON zawiera tylko klucze organizatora. Dowody, diagnozy i raport braków są osobno. Zapis atomowy.",
  ],
];
const statuses: [DocumentStatus, string][] = [
  ["full", "Wynik kompletny i zgodny z kontraktem; eksport po walidacji."],
  [
    "partial",
    "Wynik ma ograniczenia. Eksport możliwy wyłącznie, gdy nadal spełnia kontrakt; niedozwolony null go blokuje.",
  ],
  [
    "foreign",
    "Treść potwierdzona jako spoza aktywnych klas. Eksport dokładnie {} pod nazwą bazową PDF.",
  ],
  ["error", "Awaria techniczna: brak wyniku ekstrakcji i brak zastępczego {}."],
  ["running", "Analiza trwa. Eksport będzie oceniony po zakończeniu."],
  ["ambiguous", "Nie ustalono jednoznacznie klasy; eksport zablokowany."],
  [
    "multi",
    "Wykryto wiele dokumentów w jednym PDF; eksport zablokowany do ustalenia kontraktu.",
  ],
];

export function HowItWorksView() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Jak to działa</h1>
      <ol className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {steps.map(([title, text], i) => (
          <li
            key={title}
            className="rounded-lg border border-border bg-surface p-4"
          >
            <h2 className="font-semibold">
              {i + 1}. {title}
            </h2>
            <p className="mt-2 text-sm text-muted">{text}</p>
          </li>
        ))}
      </ol>
      <section
        className="rounded-lg bg-subtle p-4"
        aria-labelledby="principles-title"
      >
        <h2 id="principles-title" className="font-semibold">
          Czego nie robimy
        </h2>
        <ul className="mt-2 list-inside list-disc space-y-2 text-sm">
          <li>
            Braki opisujemy osobno. W JSON stosujemy null wyłącznie zgodnie z
            kontraktem.
          </li>
          <li>
            Przy awarii modelu pokazujemy błąd techniczny; stary wynik z pamięci
            nie zastępuje bieżącej analizy.
          </li>
          <li>
            Każdy dokument przetwarzamy niezależnie; nie uzupełniamy danych z
            innych plików.
          </li>
        </ul>
      </section>
      <section aria-labelledby="export-title" className="space-y-2">
        <h2 id="export-title" className="text-xl font-semibold">
          Wariant A eksportu — ścisła walidacja
        </h2>
        <p>
          JSON można pobrać wyłącznie po pozytywnej decyzji walidacji.
          Niedozwolony null, błąd techniczny, niejednoznaczność i wiele
          dokumentów blokują eksport. Powód blokady jest widoczny przy wyniku.
          Jedyny pusty wynik <code>{"{}"}</code> dotyczy potwierdzonego
          dokumentu obcego.
        </p>
      </section>
      <section aria-labelledby="statuses-title" className="space-y-3">
        <h2 id="statuses-title" className="text-xl font-semibold">
          Statusy dokumentów
        </h2>
        <dl className="grid gap-3 md:grid-cols-2">
          {statuses.map(([status, text]) => (
            <Card key={status}>
              <dt>
                <StatusBadge status={status} />
              </dt>
              <dd className="mt-2 text-sm">{text}</dd>
            </Card>
          ))}
        </dl>
      </section>
      <section
        aria-labelledby="readiness-title"
        className="space-y-4 rounded-lg border border-border bg-surface p-4"
      >
        <h2 id="readiness-title" className="text-xl font-semibold">
          Gotowość i modele
        </h2>
        <p className="text-muted">
          Stan usług używanych przez analizę oraz dane o modelach, licencjach i
          lokalizacji wymagają zweryfikowanej konfiguracji. Samo połączenie HTTP
          nie potwierdza zgodności.
        </p>
        <h3 className="font-semibold">Gotowość usług i kontrola klucza</h3>
        <p>
          Kontrola obejmuje połączenie, autoryzację, model, region i licencję
          oraz gotowość OCR. Przy 401 lub 403 nie ponawiamy prób w pętli. Po
          poprawieniu konfiguracji uruchom kontrolę ponownie w ustawieniach; nie
          uruchamia ona analizy PDF.
        </p>
        <Link
          href="/ustawienia"
          className="inline-flex min-h-11 items-center rounded-md border border-control px-4 text-sm underline"
        >
          Sprawdź konfigurację w ustawieniach
        </Link>
        <p>
          Klucza nie pokazujemy w podsumowaniu ani nie zapisujemy w localStorage
          lub logach. Po zapisaniu widoczny jest tylko stan „skonfigurowany”.
        </p>
      </section>
      <Card as="section" className="space-y-3">
        <h2 className="text-xl font-semibold">Co oznaczają stany pól</h2>
        <p>
          Pokrycie pokazuje, które strony i regiony zostały odczytane. Diagnoza
          rozróżnia tekst PDF, OCR oraz strony nieprzetworzone.
        </p>
        <dl className="space-y-2 text-sm">
          <div>
            <dt className="font-semibold">Brak</dt>
            <dd>Nie znaleziono wartości w dokumencie.</dd>
          </div>
          <div>
            <dt className="font-semibold">Nie dotyczy</dt>
            <dd>Pole nie odnosi się do treści dokumentu.</dd>
          </div>
          <div>
            <dt className="font-semibold">Nieczytelne</dt>
            <dd>Treści nie można wiarygodnie odczytać.</dd>
          </div>
          <div>
            <dt className="font-semibold">Sprzeczne</dt>
            <dd>Źródło zawiera niezgodne wartości.</dd>
          </div>
          <div>
            <dt className="font-semibold">Nieprzetworzone</dt>
            <dd>Odczyt strony lub regionu nie został ukończony.</dd>
          </div>
        </dl>
      </Card>
      <SystemInfoCard />
      <section aria-labelledby="demo-title" className="space-y-2">
        <h2 id="demo-title" className="text-xl font-semibold">
          Tylko dane syntetyczne
        </h2>
        <p>
          To tryb demonstracyjny bez logowania i backendu. Lista klas i wyniki
          pochodzą z mocka; nie potwierdzają wykonania ekstrakcji ani gotowości
          modelu. Korzystaj wyłącznie z syntetycznych PDF.
        </p>
      </section>
    </div>
  );
}
