"use client";
import {
  Children,
  isValidElement,
  createContext,
  useContext,
  useId,
  useState,
  type ReactNode,
  type HTMLAttributes,
  type ButtonHTMLAttributes,
  type KeyboardEvent,
} from "react";
type TabsContextValue = {
  value: string;
  select: (value: string) => void;
  id: string;
};
const TabsContext = createContext<TabsContextValue | null>(null);
function useTabs() {
  const value = useContext(TabsContext);
  if (!value) throw new Error("Zakładki wymagają komponentu Tabs.");
  return value;
}
const suffix = (value: string) => encodeURIComponent(value);
export type TabsProps = {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children: ReactNode;
};
function firstTab(children: ReactNode): string | undefined {
  for (const child of Children.toArray(children)) {
    if (
      !isValidElement<{
        value?: string;
        disabled?: boolean;
        children?: ReactNode;
      }>(child)
    )
      continue;
    if (child.type === Tab && !child.props.disabled) return child.props.value;
    const nested = firstTab(child.props.children);
    if (nested) return nested;
  }
  return undefined;
}
export function Tabs({
  value,
  defaultValue,
  onValueChange,
  children,
}: TabsProps) {
  const [internal, setInternal] = useState(
    () => defaultValue ?? firstTab(children) ?? "",
  );
  const id = useId();
  return (
    <TabsContext
      value={{
        value: value ?? internal,
        id,
        select(next) {
          if (value === undefined) setInternal(next);
          onValueChange?.(next);
        },
      }}
    >
      {children}
    </TabsContext>
  );
}
export function TabList({
  children,
  "aria-label": label = "Zakładki",
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  function keydown(event: KeyboardEvent<HTMLDivElement>) {
    const tabs = Array.from(
      event.currentTarget.querySelectorAll<HTMLButtonElement>(
        '[role="tab"]:not(:disabled)',
      ),
    );
    const current = tabs.indexOf(document.activeElement as HTMLButtonElement);
    let next = current;
    if (event.key === "ArrowRight") next = (current + 1) % tabs.length;
    else if (event.key === "ArrowLeft")
      next = (current - 1 + tabs.length) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault();
    tabs[next]?.focus();
    tabs[next]?.click();
  }
  return (
    <div
      {...props}
      role="tablist"
      aria-label={label}
      onKeyDown={keydown}
      className="flex flex-wrap gap-1 border-b border-border"
    >
      {children}
    </div>
  );
}
export function Tab({
  value,
  children,
  ...props
}: Omit<ButtonHTMLAttributes<HTMLButtonElement>, "value"> & { value: string }) {
  const tabs = useTabs();
  const selected = tabs.value === value;
  return (
    <button
      {...props}
      type="button"
      role="tab"
      id={`${tabs.id}-tab-${suffix(value)}`}
      aria-controls={`${tabs.id}-panel-${suffix(value)}`}
      aria-selected={selected}
      tabIndex={selected ? 0 : -1}
      onClick={() => tabs.select(value)}
      className={`min-h-11 rounded-t-md border-b-2 px-4 text-sm ${selected ? "border-primary font-semibold" : "border-transparent text-muted"}`}
    >
      {children}
    </button>
  );
}
export function TabPanel({
  value,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { value: string }) {
  const tabs = useTabs();
  return (
    <div
      {...props}
      id={`${tabs.id}-panel-${suffix(value)}`}
      role="tabpanel"
      aria-labelledby={`${tabs.id}-tab-${suffix(value)}`}
      hidden={tabs.value !== value}
      tabIndex={0}
      className="min-w-0 py-4"
    >
      {children}
    </div>
  );
}
