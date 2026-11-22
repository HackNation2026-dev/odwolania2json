"use client";
import { useSyncExternalStore } from "react";

const query = "(min-width: 769px)";
function subscribe(listener: () => void) {
  if (typeof window.matchMedia !== "function") return () => {};
  const media = window.matchMedia(query);
  media.addEventListener("change", listener);
  return () => media.removeEventListener("change", listener);
}
function desktop() {
  return (
    typeof window.matchMedia !== "function" || window.matchMedia(query).matches
  );
}
export function useDesktopLayout() {
  return useSyncExternalStore(subscribe, desktop, () => true);
}
