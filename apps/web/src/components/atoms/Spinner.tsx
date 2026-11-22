import { VisuallyHidden } from "./VisuallyHidden";
export function Spinner({ label = "Ładowanie" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2">
      <span
        aria-hidden
        className="h-4 w-4 rounded-full border-2 border-current border-t-transparent motion-safe:animate-spin motion-reduce:hidden"
      />
      <span className="hidden motion-reduce:inline">{label}</span>
      <VisuallyHidden className="motion-reduce:hidden">{label}</VisuallyHidden>
    </span>
  );
}
