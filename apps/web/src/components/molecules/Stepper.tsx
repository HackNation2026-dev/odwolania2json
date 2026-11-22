import { Icon } from "@/components/atoms";
export type Step = {
  id: string;
  label: string;
  status: "pending" | "running" | "ok" | "error";
  description?: string;
};
const statusText = {
  pending: "Oczekuje",
  running: "W toku",
  ok: "Gotowe",
  error: "Błąd",
};
export function Stepper({
  steps,
  label = "Etapy kontroli",
}: {
  steps: Step[];
  label?: string;
}) {
  return (
    <ol aria-label={label} aria-live="polite" className="space-y-3">
      {steps.map((step) => (
        <li
          key={step.id}
          aria-current={step.status === "running" ? "step" : undefined}
          className="flex items-start gap-3 rounded border border-border p-3"
        >
          <Icon
            name={
              step.status === "ok"
                ? "check"
                : step.status === "error"
                  ? "alert"
                  : step.status === "running"
                    ? "refresh"
                    : "minus"
            }
          />
          <div>
            <p className="font-medium">
              {step.label} · {statusText[step.status]}
            </p>
            {step.description && (
              <p className="text-sm text-muted">{step.description}</p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
