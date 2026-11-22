"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { FormField } from "@/components/molecules/FormField";
import { ErrorState } from "@/components/molecules/ErrorState";
import { LoadingState } from "@/components/molecules/LoadingState";
import { Dialog } from "@/components/organisms/Dialog";
import { useRetentionSettings, useSaveRetention } from "@/lib/api/hooks";

export function RetentionForm() {
  const settings = useRetentionSettings();
  const save = useSaveRetention();
  const [draft, setDraft] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  if (settings.isPending) return <LoadingState label="Wczytywanie retencji…" />;
  if (settings.isError)
    return (
      <ErrorState
        description="Nie udało się wczytać retencji."
        onRetry={() => void settings.refetch()}
      />
    );
  const data = settings.data;
  const days = draft ?? String(data.days);
  const valid =
    days.trim() !== "" &&
    Number.isInteger(Number(days)) &&
    Number(days) >= data.minDays &&
    Number(days) <= data.maxDays;
  function validate() {
    if (!valid) {
      setError(`Podaj liczbę dni z zakresu ${data.minDays}–${data.maxDays}.`);
      input.current?.focus();
    } else {
      setError("");
      setConfirm(true);
    }
  }
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted">
        E3 · Symulacja. Ustawienie nie usuwa plików i nie jest trwałe po
        restarcie demonstracji.
      </p>
      <FormField
        label="Usuń sprawy po (liczba dni)"
        error={error || undefined}
        hint={`Zakres: ${data.minDays}–${data.maxDays} dni. Zmiana obejmie także istniejące sprawy.`}
      >
        {(a11y) => (
          <Input
            {...a11y}
            ref={input}
            type="number"
            min={data.minDays}
            max={data.maxDays}
            step={1}
            value={days}
            onChange={(event) => {
              setDraft(event.target.value);
              setError("");
              save.reset();
            }}
          />
        )}
      </FormField>
      <Button className="min-h-11" onClick={validate}>
        Zapisz retencję
      </Button>
      {save.isSuccess && <p role="status">Zapisano retencję w demonstracji.</p>}
      <Dialog
        open={confirm}
        onClose={() => {
          if (!save.isPending) setConfirm(false);
        }}
        title="Potwierdź zmianę retencji"
        actions={
          <>
            <Button
              variant="secondary"
              disabled={save.isPending}
              onClick={() => setConfirm(false)}
            >
              Anuluj
            </Button>
            <Button
              disabled={save.isPending}
              onClick={() =>
                save.mutate(Number(days), {
                  onSuccess: () => {
                    setDraft(null);
                    setConfirm(false);
                  },
                })
              }
            >
              {save.isPending ? "Zapisywanie…" : "Zapisz"}
            </Button>
          </>
        }
      >
        <p>
          Nowa retencja: {days} dni. Do usunięcia przy najbliższym cyklu:{" "}
          {data.affectedCases} spraw (symulacja).
        </p>
        {save.isError && <p role="alert">Nie zapisano. Ponów zapis.</p>}
      </Dialog>
    </div>
  );
}
