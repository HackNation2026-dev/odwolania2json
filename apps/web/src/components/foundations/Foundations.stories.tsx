/// <reference types="vite/client" />
import type { CSSProperties } from "react";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import css from "../../styles/tokens.css?raw";
import { Heading, Text, Icon, iconPaths, type IconName } from "../atoms";

const meta = {
  title: "Foundations/Podstawy",
  parameters: { layout: "fullscreen" },
} satisfies Meta;
export default meta;
type Story = StoryObj<typeof meta>;
function block(selector: string): Record<string, string> {
  const start = css.indexOf(selector);
  const body = css.slice(css.indexOf("{", start) + 1, css.indexOf("}", start));
  return Object.fromEntries(
    [...body.matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [
      m[1]!,
      m[2]!,
    ]),
  );
}
function luminance(hex: string) {
  const [r, g, b] = [1, 3, 5]
    .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
}
function contrast(a: string, b: string) {
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p);
  return (x! + 0.05) / (y! + 0.05);
}
const light = block(":root {");
const themes = {
  light,
  dark: { ...light, ...block(':root[data-theme="dark"]') },
};
const pairs: [string, string, number][] = [
  ["text", "bg", 4.5],
  ["text", "surface", 4.5],
  ["muted", "surface", 4.5],
  ["on-primary", "primary", 4.5],
  ["border-control", "bg", 3],
  ["focus", "bg", 3],
  ...["full", "partial", "error", "running", "ambiguous", "foreign"].map(
    (s) => [`${s}-fg`, `${s}-bg`, 4.5] as [string, string, number],
  ),
];
export const Kolory: Story = {
  render: () => (
    <div className="space-y-8 p-4">
      <Heading level={1}>Kolory i kontrast WCAG</Heading>
      <Text>
        Współczynniki obliczane z bieżących tokens.css według luminancji
        względnej WCAG. Próg tekstu: 4,5:1, kontrolek i fokusu: 3:1. Ciemna
        paleta pozostaje propozycją.
      </Text>
      {Object.entries(themes).map(([name, tokens]) => (
        <section
          key={name}
          style={
            Object.fromEntries(
              Object.entries(tokens).map(([key, value]) => [`--${key}`, value]),
            ) as CSSProperties
          }
          className="space-y-4 bg-bg p-4 text-fg"
        >
          <Heading level={2}>{name === "light" ? "Jasny" : "Ciemny"}</Heading>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {Object.keys(tokens).map((token) => (
              <div
                key={token}
                className="min-w-0 rounded-md border border-border bg-surface p-2"
              >
                <div
                  aria-hidden
                  className="mb-2 h-12 rounded-sm"
                  style={{ background: `var(--${token})` }}
                />
                <Text size="sm">{token}</Text>
              </div>
            ))}
          </div>
          <ul className="space-y-2">
            {pairs.map(([fg, bg, min]) => {
              const value = contrast(tokens[fg]!, tokens[bg]!);
              return (
                <li
                  key={`${fg}-${bg}`}
                  className="rounded-md p-2"
                  style={{ color: `var(--${fg})`, background: `var(--${bg})` }}
                >
                  {fg} / {bg}: {value.toFixed(2)}:1 —{" "}
                  {value >= min ? "spełnia" : "nie spełnia"} {min}:1
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  ),
};
export const Typografia: Story = {
  render: () => (
    <div className="space-y-4 p-4">
      <Heading level={1}>Typografia</Heading>
      {([1, 2, 3, 4] as const).map((level) => (
        <Heading key={level} level={level}>
          Nagłówek poziomu {level} — Dokumenty sprawy
        </Heading>
      ))}
      <Text>Tekst podstawowy 16 px / 1,5. Zażółć gęślą jaźń.</Text>
      <Text size="sm">Tekst pomocniczy 14 px. Sygnatura KIO 123/26.</Text>
      <Text tone="muted">Tekst wyciszony: dane oczekują na weryfikację.</Text>
      <p className="font-mono">Monospace: 0123456789</p>
    </div>
  ),
};
export const OdstepyPromienieCienie: Story = {
  render: () => (
    <div className="space-y-6 p-4">
      <Heading level={1}>Odstępy, promienie i cienie</Heading>
      <Text>
        Odstępy Tailwind: jednostka 4 px; komponenty korzystają z klas skali.
      </Text>
      <div className="space-y-2">
        {[1, 2, 3, 4, 6, 8, 12].map((n) => (
          <div key={n} className="flex items-center gap-4">
            <span className="w-24">{n} × 4 px</span>
            <span
              aria-hidden
              className="h-4 bg-primary"
              style={{ width: `calc(var(--spacing) * ${n})` }}
            />
          </div>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {["rounded-sm", "rounded-md", "rounded-lg"].map((c) => (
          <div key={c} className={`border border-control bg-surface p-6 ${c}`}>
            {c}
          </div>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="bg-raised p-6 shadow-[var(--shadow-1)]">shadow-1</div>
        <div className="bg-raised p-6 shadow-[var(--shadow-2)]">shadow-2</div>
      </div>
      <Text tone="muted">W motywie ciemnym tokeny wyłączają cienie.</Text>
    </div>
  ),
};
export const Ikony: Story = {
  render: () => (
    <div className="space-y-4 p-4">
      <Heading level={1}>Ikony</Heading>
      <Text>
        Inline SVG, currentColor, rozmiary 16 / 20 / 24 px. Bez etykiety ikona
        jest dekoracyjna.
      </Text>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        {(Object.keys(iconPaths) as IconName[]).map((name) => (
          <div
            key={name}
            className="flex min-w-0 flex-col gap-2 rounded-md border border-border bg-surface p-4"
          >
            <span>{name}</span>
            <div className="flex items-center gap-2">
              {([16, 20, 24] as const).map((size) => (
                <Icon key={size} name={name} size={size} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  ),
};
