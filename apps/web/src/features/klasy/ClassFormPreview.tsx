import { Card, Input } from "@/components/atoms";
import { FormField } from "@/components/molecules/FormField";
import { CodeBlock } from "@/components/molecules/CodeBlock";
import { EmptyState } from "@/components/molecules/EmptyState";
import type { ClassDetail } from "@/lib/api/schemas";

export function ClassFormPreview({ definition }: { definition: ClassDetail }) {
  return (
    <Card className="space-y-4">
      <h2 className="text-lg font-semibold">Podgląd formularza</h2>
      <p className="text-sm text-muted">
        Formularz z aktywnej konfiguracji. Przykładowe wartości, bez modelu.
      </p>
      {!definition.fields.length && (
        <EmptyState title="Brak pól w konfiguracji" />
      )}
      {definition.fields.map((field) => (
        <FormField key={field.key} label={field.label} hint={field.key}>
          {(a11y) => (
            <Input
              {...a11y}
              readOnly
              value={
                field.key === "kwota"
                  ? "200.00"
                  : field.key === "data_operacji"
                    ? "2026-10-12"
                    : "Przykład syntetyczny"
              }
            />
          )}
        </FormField>
      ))}
      <CodeBlock
        label="Podgląd struktury JSON, bez wyniku ekstrakcji"
        code={JSON.stringify(
          Object.fromEntries(
            definition.fields.map((field) => [field.key, null]),
          ),
          null,
          2,
        )}
      />
    </Card>
  );
}
