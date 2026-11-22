"use client";

import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { Checkbox } from "@/components/atoms/Checkbox";
import { Select } from "@/components/atoms/Select";
import { FormField } from "@/components/molecules/FormField";
import { Banner } from "@/components/molecules/Banner";
import { Dialog } from "@/components/organisms/Dialog";
import type { UserRecord } from "@/lib/api/schemas";

const roles = [
  "Administrator",
  "Operator",
  "Weryfikator",
  "Obserwator",
  "Konfigurator",
];
export function UserRoleDialog({
  user,
  onClose,
}: {
  user: UserRecord;
  onClose: () => void;
}) {
  const [role, setRole] = useState<string>(user.role);
  const [personalData, setPersonalData] = useState(user.personalData);
  const [scope, setScope] = useState("assigned");
  return (
    <Dialog
      open
      onClose={onClose}
      title={`Role i zakres spraw: ${user.name}`}
      actions={
        <>
          <Button variant="secondary" onClick={onClose}>
            Zamknij
          </Button>
          <Button disabled>Zapisz (po MVP)</Button>
        </>
      }
    >
      <div className="space-y-4">
        <Banner tone="info">
          E3 · Podgląd uprawnień. Zmiany w tym oknie nie zmieniają dostępu do
          danych. Wymagany backend kontroli uprawnień.
        </Banner>
        <FormField label="Rola">
          {(a11y) => (
            <Select
              {...a11y}
              value={role}
              onChange={(event) => setRole(event.target.value)}
            >
              {roles.map((value) => (
                <option key={value}>{value}</option>
              ))}
            </Select>
          )}
        </FormField>
        <FormField label="Zakres spraw">
          {(a11y) => (
            <Select
              {...a11y}
              value={scope}
              onChange={(event) => setScope(event.target.value)}
            >
              <option value="assigned">Przypisane sprawy</option>
              <option value="all">Wszystkie sprawy</option>
            </Select>
          )}
        </FormField>
        <Checkbox
          label="Uprawnienie »Dane osobowe«"
          checked={personalData}
          onChange={(event) => setPersonalData(event.target.checked)}
        />
        <p className="text-sm text-muted">
          Pozwala odsłaniać PESEL i pełne numery rachunków. Każde odsłonięcie
          jest zapisywane bez wartości w dzienniku.
        </p>
      </div>
    </Dialog>
  );
}
