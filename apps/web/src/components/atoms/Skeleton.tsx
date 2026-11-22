import { cn } from "@/lib/cn";
export function Skeleton({ className }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={cn(
        "block h-4 rounded-md bg-subtle motion-safe:animate-pulse",
        className,
      )}
    />
  );
}
