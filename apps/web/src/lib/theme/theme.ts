export type ThemePreference = "light" | "dark" | "system";
export const THEME_KEY = "o2j-theme";

export function resolveTheme(pref: ThemePreference, systemDark: boolean): "light" | "dark" {
  return pref === "system" ? (systemDark ? "dark" : "light") : pref;
}

/** Skrypt wstawiany w <head>: ustawia motyw przed pierwszym malowaniem (bez błysku). */
export const themeInitScript = `(function(){try{var p=localStorage.getItem('${THEME_KEY}')||'system';var d=window.matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.dataset.theme=p==='system'?(d?'dark':'light'):p;}catch(e){}})();`;
