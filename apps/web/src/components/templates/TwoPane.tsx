"use client";
import type { ReactNode } from "react";
import { useDesktopLayout } from "@/components/useDesktopLayout";
import { Tabs, TabList, Tab, TabPanel } from "@/components/molecules/Tabs";
export type TwoPaneProps = {
  left: ReactNode;
  right: ReactNode;
  ratio?: "50/50" | "60/40";
  mobileTabs?: [string, string];
};
export function TwoPane({
  left,
  right,
  ratio = "50/50",
  mobileTabs = ["Dokument", "Dane"],
}: TwoPaneProps) {
  const wide = useDesktopLayout();
  if (wide)
    return (
      <div
        className={`grid min-w-0 gap-4 ${ratio === "60/40" ? "grid-cols-[minmax(0,3fr)_minmax(0,2fr)]" : "grid-cols-2"}`}
      >
        <div className="min-w-0">{left}</div>
        <div className="min-w-0">{right}</div>
      </div>
    );
  return (
    <div className="min-w-0">
      <Tabs defaultValue="left">
        <TabList aria-label="Panele dokumentu">
          <Tab value="left">{mobileTabs[0]}</Tab>
          <Tab value="right">{mobileTabs[1]}</Tab>
        </TabList>
        <TabPanel value="left">{left}</TabPanel>
        <TabPanel value="right">{right}</TabPanel>
      </Tabs>
    </div>
  );
}
