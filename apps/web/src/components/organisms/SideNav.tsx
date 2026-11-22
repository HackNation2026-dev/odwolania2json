"use client";
import { NavItem as NavigationItem } from "@/components/molecules/NavItem";
type NavItem = {
  href: string;
  label: string;
  icon: string;
  match: (p: string) => boolean;
};

const main: NavItem[] = [
  { href: "/", label: "Pulpit", icon: "▤", match: (p) => p === "/" },
  {
    href: "/dodaj",
    label: "Nowa analiza",
    icon: "＋",
    match: (p) => p.startsWith("/dodaj"),
  },
  {
    href: "/dokumenty",
    label: "Sprawy",
    icon: "▦",
    match: (p) => p.startsWith("/dokumenty"),
  },
  {
    href: "/klasy",
    label: "Klasy dokumentów",
    icon: "▣",
    match: (p) => p.startsWith("/klasy"),
  },
  {
    href: "/jak-to-dziala",
    label: "Jak to działa",
    icon: "ⓘ",
    match: (p) => p.startsWith("/jak-to-dziala"),
  },
];
const admin: NavItem[] = [
  {
    href: "/uzytkownicy",
    label: "Użytkownicy i role",
    icon: "☺",
    match: (p) => p.startsWith("/uzytkownicy"),
  },
  {
    href: "/dziennik",
    label: "Dziennik zdarzeń",
    icon: "≣",
    match: (p) => p.startsWith("/dziennik"),
  },
  {
    href: "/ustawienia",
    label: "Ustawienia",
    icon: "⚙",
    match: (p) => p.startsWith("/ustawienia") || p.startsWith("/klucz"),
  },
];

function NavList({
  items,
  pathname,
  mobile,
}: {
  items: NavItem[];
  pathname: string;
  mobile?: boolean;
}) {
  return (
    <ul className={mobile ? "flex flex-col gap-1" : "flex gap-1 md:flex-col"}>
      {items.map((n) => {
        const active = n.match(pathname);
        return (
          <li key={n.href}>
            <NavigationItem
              href={n.href}
              label={n.label}
              icon={n.icon}
              active={active}
            />
          </li>
        );
      })}
    </ul>
  );
}

export function SideNav({
  pathname,
  mobile = false,
}: {
  pathname: string;
  mobile?: boolean;
}) {
  return (
    <nav
      aria-label="Główna"
      className={
        mobile
          ? "bg-subtle"
          : "hidden border-b border-border bg-subtle md:block md:w-60 md:shrink-0 md:border-r md:border-b-0"
      }
    >
      <div className="flex flex-col gap-3 overflow-x-auto p-2 md:p-3">
        <NavList items={main} pathname={pathname} mobile={mobile} />
        <div className={mobile ? "block" : "hidden md:block"}>
          <p className="px-3 pb-1 text-xs font-medium tracking-wide text-muted">
            ADMINISTRACJA
          </p>
        </div>
        <NavList items={admin} pathname={pathname} mobile={mobile} />
      </div>
    </nav>
  );
}
