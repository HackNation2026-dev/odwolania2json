import { Spinner, Skeleton } from "@/components/atoms";
export function SkeletonBlock({ lines = 3 }: { lines?: number }) {
  return (
    <div aria-hidden="true" className="space-y-3">
      {Array.from({ length: Math.max(0, lines) }, (_, i) => (
        <Skeleton key={i} className="h-5 w-full" />
      ))}
    </div>
  );
}
export function LoadingState({ label = "Wczytywanie…" }: { label?: string }) {
  return (
    <div role="status" className="space-y-4 p-4">
      <div className="flex items-center gap-2">
        <Spinner />
        <span>{label}</span>
      </div>
      <SkeletonBlock />
    </div>
  );
}
