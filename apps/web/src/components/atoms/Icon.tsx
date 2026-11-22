import type { SVGProps } from "react";
export const iconPaths = {
  check: "m5 12 4 4L19 6",
  alert: "m12 3 10 18H2L12 3m0 5v6m0 3v1",
  info: "M12 10v7m0-11v1M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20",
  x: "m6 6 12 12M6 18 18 6",
  plus: "M12 4v16M4 12h16",
  minus: "M4 12h16",
  search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14m5 12 6 6",
  "chevron-down": "m5 9 7 7 7-7",
  "chevron-right": "m9 5 7 7-7 7",
  "chevron-left": "m15 5-7 7 7 7",
  external: "M14 3h7v7m0-7L10 14M10 3H3v18h18v-7",
  download: "M12 3v12m-5-5 5 5 5-5M3 16v5h18v-5",
  copy: "M8 8h13v13H8V8M16 8V3H3v13h5",
  upload: "M12 16V3m-5 5 5-5 5 5M3 16v5h18v-5",
  file: "M4 2h10l6 6v14H4V2m10 0v6h6",
  trash: "M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7",
  refresh: "M20 7a9 9 0 1 0 1 9M20 2v5h-5",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12m10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
  "eye-off": "m3 3 18 18M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12",
  settings:
    "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v4m0 12v4M2 12h4m12 0h4M5 5l3 3m8 8 3 3M5 19l3-3m8-8 3-3",
  users:
    "M8 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8M1 21v-3a7 7 0 0 1 14 0v3m1-17a4 4 0 0 1 0 8m2 3a5 5 0 0 1 5 5v1",
  list: "M8 5h14M8 12h14M8 19h14M2 5h1m-1 7h1m-1 7h1",
  grid: "M3 3h7v7H3V3m11 0h7v7h-7V3M3 14h7v7H3v-7m11 0h7v7h-7v-7",
  help: "M9 8a3 3 0 1 1 5 2l-2 2v2m0 3v1M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20",
  doc: "M4 2h16v20H4V2m4 5h8m-8 5h8m-8 5h5",
  log: "M4 3h16v18H4V3m4 4h8m-8 5h8m-8 5h8",
  menu: "M3 5h18M3 12h18M3 19h18",
  lock: "M5 10h14v12H5V10m3 0V6a4 4 0 0 1 8 0v4m-4 5v3",
  filter: "M3 3h18l-7 8v9l-4-2v-7L3 3",
} as const;
export type IconName = keyof typeof iconPaths;
export type IconProps = Omit<SVGProps<SVGSVGElement>, "name"> & {
  name: IconName;
  size?: 16 | 20 | 24;
  label?: string;
};
export function Icon({ name, size = 20, label, ...props }: IconProps) {
  return (
    <svg
      {...props}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <path d={iconPaths[name]} />
    </svg>
  );
}
