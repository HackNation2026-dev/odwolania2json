"use client";

import type { UseQueryResult } from "@tanstack/react-query";
import type { SystemInfo } from "@/lib/api/schemas";
import { Card } from "@/components/atoms/Card";
import { Button } from "@/components/atoms/Button";
import { useKeyStatus, useRunSelfCheck, useSystemInfo } from "@/lib/api/hooks";

export function SystemInfoCard() {
  const info = useSystemInfo();
  return <SystemInfoContent info={info} />;
}

export function SystemInfoContent({
  info,
}: {
  info: UseQueryResult<SystemInfo, Error>;
}) {
  const key = useKeyStatus();
  const check = useRunSelfCheck();
  if (info.isPending)
    return (
      <div
        role="status"
        className="h-36 animate-pulse rounded-lg bg-subtle p-4"
      >
        Wczytywanie modeli i gotowości…
      </div>
    );
  if (info.isError)
    return (
      <div
        role="alert"
        className="space-y-3 rounded-lg border border-control p-4"
      >
        <p>Nie udało się wczytać modeli i gotowości.</p>
        <Button className="min-h-11" onClick={() => void info.refetch()}>
          Spróbuj ponownie
        </Button>
      </div>
    );
  const data = info.data;
  const unknown = (value: string | number | null) =>
    value ?? "Nie podano w konfiguracji";
  return (
    <section aria-labelledby="system-info-title" className="space-y-4">
      <h2 id="system-info-title" className="text-xl font-semibold">
        Karta modeli i gotowości
      </h2>
      <p className="text-sm text-muted">
        Konfiguracja demonstracyjna z API mocka. Kontrola jest symulacją; nie
        potwierdza działania usług ani ich zgodności.
      </p>
      <Card className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-semibold">Gotowość usług</h3>
          <Button
            variant="secondary"
            className="min-h-11"
            disabled={check.isPending}
            onClick={() => check.mutate(() => {})}
          >
            {check.isPending ? "Sprawdzanie…" : "Sprawdź ponownie"}
          </Button>
        </div>
        <div aria-live="polite">
          <p>
            {check.isPending
              ? "Kontrola demonstracyjna w toku…"
              : check.isSuccess
                ? "Kontrola demonstracyjna zakończona. Rzeczywiste usługi pozostają niezweryfikowane."
                : "Nie sprawdzono gotowości"}
          </p>
          {check.data && (
            <ul>
              {check.data.map((step) => (
                <li key={step.id}>
                  {step.label}:{" "}
                  {step.state === "ok"
                    ? "✓ Poprawnie (mock)"
                    : step.state === "error"
                      ? "! Błąd"
                      : "Oczekuje"}
                  {step.detail ? ` — ${step.detail}` : ""}
                </li>
              ))}
            </ul>
          )}
        </div>
        {check.isError && (
          <p role="alert">
            Nie udało się przeprowadzić kontroli. Spróbuj ponownie po
            poprawieniu konfiguracji.
          </p>
        )}
        <p className="text-sm">
          Ostatnie sprawdzenie:{" "}
          {check.isSuccess
            ? new Date(check.submittedAt).toLocaleString("pl-PL")
            : "Nie wykonano"}
        </p>
        <p>
          {key.isPending
            ? "Wczytywanie stanu klucza…"
            : key.isError
              ? "Nie udało się odczytać stanu klucza."
              : key.data.configured
                ? "Klucz: skonfigurowany"
                : "Brak klucza API modelu. Skonfiguruj klucz po stronie serwera zgodnie z instrukcją uruchomienia."}
        </p>
        <p className="rounded-md bg-[var(--partial-bg)] p-3 text-sm text-[var(--partial-fg)]">
          ▲ Model, licencja lub lokalizacja niepotwierdzone. Wywołania
          zablokowane.
        </p>
        <p
          className={`rounded-md p-3 text-sm ${data.ocr.mode === "unavailable" ? "bg-[var(--error-bg)] text-[var(--error-fg)]" : "bg-[var(--partial-bg)] text-[var(--partial-fg)]"}`}
        >
          {data.ocr.mode === "unavailable"
            ? "× OCR niedostępny. Strony wymagające OCR pozostaną nieprzetworzone. Upload i analiza PDF z warstwą tekstową są dostępne. Nie oznaczamy dokumentu jako obcego z powodu braku OCR."
            : data.ocr.mode === "shim"
              ? `▲ OCR tymczasowy (shim): ${data.ocr.name}. Docelowy własny model OCR nie jest podłączony. Gotowość zamiennika wymaga kontroli; dane mocka jej nie potwierdzają.`
              : `OCR docelowy: ${data.ocr.name}. Gotowość wymaga kontroli usługi.`}
        </p>
        <p className="rounded-md bg-subtle p-3 text-sm">
          Zestaw klas (YAML): {data.versions.classes} · Limit pliku:{" "}
          {data.limits.fileMb === null
            ? "Nie pobrano"
            : `${data.limits.fileMb} MB`}
        </p>
        <details>
          <summary className="min-h-11 cursor-pointer py-3">
            Komunikaty przy awarii
          </summary>
          <ul className="list-inside list-disc space-y-2 text-sm">
            <li>
              API odrzuciło uwierzytelnienie (401) / API odmówiło dostępu (403).
              Sprawdź uprawnienia klucza na serwerze.
            </li>
            <li>
              Osiągnięto limit zapytań. Ponów po czasie wskazanym przez API. /
              Brak dostępnych środków API.
            </li>
            <li>
              Nie można połączyć z API modelu. / Endpoint modelu niedostępny. /
              Przekroczono czas odpowiedzi modelu.
            </li>
          </ul>
        </details>
      </Card>
      <Card className="space-y-3">
        <h3 className="font-semibold">Modele i role</h3>
        {data.models.length === 0 && <p>Brak skonfigurowanych modeli.</p>}
        {data.models.map((model) => (
          <article
            key={model.id}
            className="space-y-2 rounded-lg bg-subtle p-4 text-sm"
          >
            <h4 className="break-words font-semibold">{model.name}</h4>
            <p>
              Stan:{" "}
              {model.state === "configured"
                ? "Skonfigurowany"
                : model.state === "used"
                  ? "Użyty"
                  : "Wyłączony"}{" "}
              · Rola: {model.role}
            </p>
            <p>
              Wersja: {unknown(model.version)} · Parametry:{" "}
              {unknown(model.parameters)}
            </p>
            <p>Licencja: {unknown(model.license)}</p>
            <p>Wagi: {unknown(model.weights)}</p>
            <p>Instalacja lokalna: {unknown(model.localInstallation)}</p>
            <p className="break-words">
              Dostawca API: {unknown(model.provider)}
            </p>
            <p>Region endpointu: {unknown(model.region)}</p>
            <p>
              Kraj firmy: {unknown(model.companyCountry)} · Kraj serwera:{" "}
              {unknown(model.serverCountry)}
            </p>
            <p>{model.confirmation}</p>
          </article>
        ))}
        <article className="space-y-2 rounded-lg bg-subtle p-4 text-sm">
          <h4 className="font-semibold">
            {data.ocr.name} —{" "}
            {data.ocr.mode === "shim"
              ? "OCR tymczasowy (shim)"
              : data.ocr.mode === "target"
                ? "OCR docelowy"
                : "OCR niedostępny"}
          </h4>
          <p>Rola: OCR stron wymagających odczytu obrazu</p>
          <p>{data.ocr.execution}</p>
          <p>
            Wersja: {unknown(data.ocr.version)} · Licencja:{" "}
            {unknown(data.ocr.license)} · Parametry:{" "}
            {unknown(data.ocr.parameters)}
          </p>
          <p>{data.ocr.detail}</p>
        </article>
        <p className="rounded-md bg-[var(--partial-bg)] p-3 text-sm text-[var(--partial-fg)]">
          ▲ Największy model systemu:{" "}
          {data.largestModel ?? "Nie ustalono największego modelu"}. OCR
          pokazano osobno; jego udział w punktacji pozostaje pytaniem do
          mentora.
        </p>
      </Card>
      <Card className="space-y-2 text-sm">
        <h3 className="font-semibold">Wersje i zasoby</h3>
        <p>
          Aplikacja: {data.versions.application} · Silnik:{" "}
          {unknown(data.versions.engine)} · Zestaw klas YAML:{" "}
          {data.versions.classes}
        </p>
        <p>Rewizja kontraktu: {unknown(data.versions.contract)}</p>
        <p>
          Limit pliku:{" "}
          {data.limits.fileMb === null
            ? "Nie pobrano"
            : `${data.limits.fileMb} MB`}{" "}
          · Limit partii: {unknown(data.limits.batch)} · Równoległość:{" "}
          {unknown(data.limits.concurrency)}
        </p>
        <p>Wykaz licencji komponentów: {unknown(data.licenses)}</p>
      </Card>
    </section>
  );
}
