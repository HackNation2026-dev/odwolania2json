"use client";

import Link from "next/link";
import { useRef } from "react";
import { Button } from "@/components/atoms/Button";
import { ThemeToggle } from "@/components/molecules/ThemeToggle";
import { Drawer } from "./Drawer";
import { SideNav } from "./SideNav";

export function AppShellMobileMenu({
  open,
  onClose,
  pathname,
}: {
  open: boolean;
  onClose: () => void;
  pathname: string;
}) {
  const close = useRef<HTMLButtonElement>(null);
  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="Odwołania2JSON"
      initialFocusRef={close}
    >
      <div
        ref={(node) => {
          close.current = node?.querySelector("button") ?? null;
        }}
      >
        <Button
          variant="secondary"
          className="mb-3 min-h-11 w-full"
          onClick={onClose}
        >
          × Zamknij menu
        </Button>
      </div>
      <div
        onClick={(event) => {
          if ((event.target as HTMLElement).closest("a")) onClose();
        }}
      >
        <SideNav pathname={pathname} mobile />
        <div className="mt-8 space-y-4 border-t border-border pt-4">
          <Link
            href={{ pathname: "/dostepnosc" }}
            className="flex min-h-11 items-center text-sm underline"
          >
            Deklaracja dostępności
          </Link>
          <Link
            href={{ pathname: "/gotowosc" }}
            className="flex min-h-11 items-center text-sm underline"
          >
            Gotowość i modele
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </Drawer>
  );
}
