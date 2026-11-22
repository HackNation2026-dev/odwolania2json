import type { View } from "./filters";
export const VIEW_STORAGE_KEY = "o2j-documents-view";
export function subscribeView(listener: () => void) {
  window.addEventListener("storage", listener);
  return () => window.removeEventListener("storage", listener);
}
export function readView(): View | undefined {
  try {
    const saved = localStorage.getItem(VIEW_STORAGE_KEY);
    return saved === "galeria" || saved === "tabela" ? saved : undefined;
  } catch {
    return undefined;
  }
}
export function subscribeFilters(listener: () => void) {
  window.addEventListener("popstate", listener);
  window.addEventListener("o2j-filters", listener);
  return () => {
    window.removeEventListener("popstate", listener);
    window.removeEventListener("o2j-filters", listener);
  };
}
