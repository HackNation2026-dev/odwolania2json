"use client";

import { useSyncExternalStore } from "react";
import { THEME_KEY, resolveTheme, type ThemePreference } from "@/lib/theme/theme";

const options: { value: ThemePreference; label: string }[] = [
  { value: "light", label: "Jasny" },
  { value: "dark", label: "Ciemny" },
  { value: "system", label: "Systemowy" },
];

function apply(pref: ThemePreference) {
  const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.theme = resolveTheme(pref, dark);
}

const listeners = new Set<() => void>();
const read = (): ThemePreference => {
  try {
    return (localStorage.getItem(THEME_KEY) as ThemePreference | null) ?? "system";
  } catch {
    return "system";
  }
};
const subscribe = (cb: () => void) => {
  listeners.add(cb);
  return () => void listeners.delete(cb);
};

export function ThemeToggle() {
  const pref = useSyncExternalStore(subscribe, read, () => "system" as ThemePreference);
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-muted">Motyw</span>
      <select
        aria-label="Motyw"
        value={pref}
        className="min-h-10 rounded-md border border-control bg-surface px-2"
        onChange={(e) => {
          const next = e.target.value as ThemePreference;
          try {
            localStorage.setItem(THEME_KEY, next);
          } catch {}
          apply(next);
          listeners.forEach((l) => l());
        }}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
