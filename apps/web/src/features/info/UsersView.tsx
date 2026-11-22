"use client";

import { useState } from "react";
import { Input } from "@/components/atoms/Input";
import { Card } from "@/components/atoms/Card";
import { FormField } from "@/components/molecules/FormField";
import { UserRoleDialog } from "./UserRoleDialog";
import type { UserRecord } from "@/lib/api/schemas";
import { Button } from "@/components/atoms/Button";
import { useUsers } from "@/lib/api/hooks";

const statuses = {
  active: "✓ Aktywny",
  invited: "◌ Zaproszony",
  blocked: "× Zablokowany",
};
const statusTones = {
  active: "text-[var(--full-fg)]",
  invited: "text-[var(--running-fg)]",
  blocked: "text-[var(--error-fg)]",
};

export function UsersView() {
  const users = useUsers();
  const [selected, setSelected] = useState<UserRecord | null>(null);
  const [search, setSearch] = useState("");
  const filtered =
    users.data?.filter((user) =>
      (user.name + user.email)
        .toLocaleLowerCase("pl")
        .includes(search.toLocaleLowerCase("pl")),
    ) ?? [];
  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Użytkownicy i role</h1>
        <Button disabled className="min-h-11">
          Dodaj użytkownika
        </Button>
      </header>
      <p className="rounded-lg bg-subtle p-4 text-sm">
        Po MVP / E3. Widok demonstracyjny, wyłącznie dane syntetyczne.
        Zarządzanie kontami, edycja ról i blokowanie użytkowników nie są
        dostępne w MVP bez logowania.
      </p>
      <FormField label="Szukaj po imieniu lub e-mailu">
        {(a11y) => (
          <Input
            {...a11y}
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        )}
      </FormField>
      {selected && (
        <UserRoleDialog
          key={selected.id}
          user={selected}
          onClose={() => setSelected(null)}
        />
      )}
      {users.isPending ? (
        <div
          role="status"
          className="h-40 animate-pulse rounded-lg bg-subtle p-4"
        >
          Wczytywanie użytkowników…
        </div>
      ) : users.isError ? (
        <div role="alert">
          <p>Nie udało się wczytać użytkowników.</p>
          <Button className="min-h-11" onClick={() => void users.refetch()}>
            Spróbuj ponownie
          </Button>
        </div>
      ) : filtered.length === 0 ? (
        <p role="status">Brak użytkowników.</p>
      ) : (
        <Card padding="none" className="overflow-x-auto">
          <table className="w-full text-left text-sm max-lg:block">
            <caption className="sr-only">
              Syntetyczni użytkownicy, uprawnienia i status
            </caption>
            <thead className="bg-subtle text-muted max-lg:sr-only">
              <tr>
                {[
                  "Imię i nazwisko",
                  "E-mail",
                  "Role",
                  "Dane osobowe",
                  "Status",
                  "Ostatnie logowanie",
                  "Działania",
                ].map((label) => (
                  <th scope="col" key={label} className="p-3 font-medium">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="max-lg:block">
              {filtered.map((user) => (
                <tr
                  key={user.id}
                  className="border-t border-border max-lg:block max-lg:p-3"
                >
                  <th
                    scope="row"
                    className="p-3 font-medium max-lg:block max-lg:p-1"
                  >
                    {user.name}
                  </th>
                  <td className="break-all p-3 max-lg:block max-lg:p-1">
                    <span className="lg:hidden">E-mail: </span>
                    {user.email}
                  </td>
                  <td className="p-3 max-lg:block max-lg:p-1">
                    <span className="lg:hidden">Rola: </span>
                    {user.role}
                  </td>
                  <td className="p-3 max-lg:block max-lg:p-1">
                    <span className="lg:hidden">Dane osobowe: </span>
                    {user.personalData ? "Tak" : "Nie"}
                  </td>
                  <td className="p-3 max-lg:block max-lg:p-1">
                    <span className="lg:hidden">Status: </span>
                    <span className={statusTones[user.status]}>
                      {statuses[user.status]}
                    </span>
                  </td>
                  <td className="p-3 max-lg:block max-lg:p-1">
                    <span className="lg:hidden">Ostatnie logowanie: </span>
                    {user.lastLogin
                      ? new Date(user.lastLogin).toLocaleString("pl-PL", {
                          timeZone: "Europe/Warsaw",
                          dateStyle: "short",
                          timeStyle: "short",
                        })
                      : "—"}
                  </td>
                  <td className="p-3 max-lg:block max-lg:p-1">
                    <div className="flex flex-wrap gap-1">
                      <Button
                        variant="ghost"
                        className="min-h-11 px-2"
                        aria-label={`Edytuj: ${user.name}`}
                        onClick={() => setSelected(user)}
                      >
                        Edytuj
                      </Button>
                      <Button
                        disabled
                        variant="ghost"
                        className="min-h-11 px-2"
                        aria-label={`${user.status === "blocked" ? "Odblokuj" : "Zablokuj"}: ${user.name}`}
                      >
                        {user.status === "blocked" ? "Odblokuj" : "Zablokuj"}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
