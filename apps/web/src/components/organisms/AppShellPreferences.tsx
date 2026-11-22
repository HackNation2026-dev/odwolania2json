"use client";

import { useEffect, useSyncExternalStore } from "react";

const preferenceKey = "o2j-preferences";
function subscribe(callback: () => void) {
  window.addEventListener(preferenceKey, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(preferenceKey, callback);
    window.removeEventListener("storage", callback);
  };
}
function read() {
  try {
    return localStorage.getItem(preferenceKey) ?? "";
  } catch {
    return "";
  }
}
export function AppShellPreferences() {
  const raw = useSyncExternalStore(subscribe, read, () => "");
  let preferences: {
    dense?: boolean;
    reducedMotion?: boolean;
    noShortcuts?: boolean;
  } = {};
  try {
    preferences = JSON.parse(raw || "{}");
  } catch {
    /* Niepoprawny zapis nie blokuje interfejsu. */
  }
  const noShortcuts = !!preferences.noShortcuts;
  useEffect(() => {
    document.documentElement.dataset.singleKeyShortcuts = noShortcuts
      ? "off"
      : "on";
    function keydown(event: KeyboardEvent) {
      if (!noShortcuts || event.ctrlKey || event.metaKey || event.altKey)
        return;
      if (
        (event.target as HTMLElement).closest(
          "input,textarea,select,[contenteditable=true]",
        )
      )
        return;
      if (event.key === "?") event.stopImmediatePropagation();
    }
    document.addEventListener("keydown", keydown, true);
    return () => {
      delete document.documentElement.dataset.singleKeyShortcuts;
      document.removeEventListener("keydown", keydown, true);
    };
  }, [noShortcuts]);
  const styles = [
    preferences.dense
      ? "@media(min-width:769px){#main table th,#main table td{padding-block:0.5rem}}"
      : "",
    preferences.reducedMotion
      ? "*,*::before,*::after{animation-duration:0.01ms!important;transition-duration:0.01ms!important;scroll-behavior:auto!important}"
      : "",
  ].join("");
  return styles ? <style>{styles}</style> : null;
}
