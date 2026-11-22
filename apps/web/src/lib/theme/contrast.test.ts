import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(join(process.cwd(), "src/styles/tokens.css"), "utf8");

function block(selector: string): Record<string, string> {
  const start = css.indexOf(selector);
  const body = css.slice(css.indexOf("{", start) + 1, css.indexOf("}", start));
  return Object.fromEntries([...body.matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1]!, m[2]!]));
}

function lum(hex: string) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
}
const ratio = (a: string, b: string) => {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x! + 0.05) / (y! + 0.05);
};

const themes = { light: { ...block(":root {") }, dark: { ...block(":root {"), ...block(':root[data-theme="dark"]') } };
const statuses = ["full", "partial", "error", "running", "ambiguous", "foreign"];

describe.each(Object.entries(themes))("kontrast WCAG AA (%s)", (_name, t) => {
  it("tekst na tle i powierzchni >= 4.5", () => {
    expect(ratio(t.text!, t.bg!)).toBeGreaterThanOrEqual(4.5);
    expect(ratio(t.text!, t.surface!)).toBeGreaterThanOrEqual(4.5);
    expect(ratio(t.muted!, t.surface!)).toBeGreaterThanOrEqual(4.5);
    expect(ratio(t["on-primary"]!, t.primary!)).toBeGreaterThanOrEqual(4.5);
  });
  it("ramka kontrolki i fokus >= 3 na tle", () => {
    expect(ratio(t["border-control"]!, t.bg!)).toBeGreaterThanOrEqual(3);
    expect(ratio(t.focus!, t.bg!)).toBeGreaterThanOrEqual(3);
  });
  it.each(statuses)("status %s >= 4.5", (s) => {
    expect(ratio(t[`${s}-fg`]!, t[`${s}-bg`]!)).toBeGreaterThanOrEqual(4.5);
  });
});
