"use client";

import { useEffect, useState } from "react";
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

export function ThemeToggle() {
  const [pref, setPref] = useState<ThemePreference>("system");
  useEffect(() => {
    try {
      setPref((localStorage.getItem(THEME_KEY) as ThemePreference | null) ?? "system");
    } catch {}
  }, []);
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-muted">Motyw</span>
      <select
        aria-label="Motyw"
        value={pref}
        className="min-h-10 rounded-md border border-control bg-surface px-2"
        onChange={(e) => {
          const next = e.target.value as ThemePreference;
          setPref(next);
          try {
            localStorage.setItem(THEME_KEY, next);
          } catch {}
          apply(next);
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
