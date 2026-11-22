"use client";

import { useSyncExternalStore } from "react";
import { Checkbox } from "@/components/atoms/Checkbox";
import { Select } from "@/components/atoms/Select";
import { FormField } from "@/components/molecules/FormField";

const eventName = "o2j-preferences";
function subscribe(callback: () => void) {
  window.addEventListener(eventName, callback);
  return () => window.removeEventListener(eventName, callback);
}
function read() {
  try {
    return localStorage.getItem(eventName) ?? "";
  } catch {
    return "";
  }
}
export function Preferences() {
  const raw = useSyncExternalStore(subscribe, read, () => "");
  let prefs: {
    dense?: boolean;
    noShortcuts?: boolean;
    reducedMotion?: boolean;
  } = {};
  try {
    prefs = JSON.parse(raw || "{}");
  } catch {
    /* Uszkodzone preferencje przywracamy do wartości domyślnych. */
  }
  function update(value: typeof prefs) {
    try {
      localStorage.setItem(eventName, JSON.stringify({ ...prefs, ...value }));
      window.dispatchEvent(new Event(eventName));
    } catch {
      /* Blokada pamięci przeglądarki nie blokuje pozostałych ustawień. */
    }
  }
  return (
    <div className="space-y-3">
      <FormField label="Gęstość">
        {(a11y) => (
          <Select
            {...a11y}
            value={prefs.dense ? "compact" : "comfortable"}
            onChange={(event) =>
              update({ dense: event.target.value === "compact" })
            }
          >
            <option value="comfortable">Wygodna</option>
            <option value="compact">Zwarta</option>
          </Select>
        )}
      </FormField>
      <p className="text-sm text-muted">Język: Polski</p>
      <h3 className="font-semibold">Dostępność</h3>
      <Checkbox
        label="Wyłącz skróty jednoklawiszowe"
        checked={!!prefs.noShortcuts}
        onChange={(event) => update({ noShortcuts: event.target.checked })}
      />
      <Checkbox
        label="Ogranicz animacje"
        checked={!!prefs.reducedMotion}
        onChange={(event) => update({ reducedMotion: event.target.checked })}
      />
      <p role="status" className="text-sm text-muted">
        {raw
          ? "Preferencje zapisano na tym urządzeniu."
          : "Preferencje dotyczą tego urządzenia."}
      </p>
    </div>
  );
}
