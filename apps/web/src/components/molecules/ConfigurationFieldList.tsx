import { EmptyState } from "./EmptyState";

export type ConfigurationField = {
  key: string;
  label: string;
  type: string;
  description: string;
  required: boolean;
  nullable: boolean;
};

export function ConfigurationFieldList({
  fields,
}: {
  fields: ConfigurationField[];
}) {
  if (!fields.length) return <EmptyState title="Brak pól w konfiguracji" />;
  return (
    <ul className="space-y-3">
      {fields.map((field) => (
        <li key={field.key} className="rounded-md bg-subtle p-3 text-sm">
          <h3 className="font-medium">{field.label}</h3>
          <code className="block break-all text-muted">{field.key}</code>
          <p>
            {field.type} · {field.description}
            <br />
            {field.required ? "Wymagane" : "Opcjonalne"} ·{" "}
            {field.nullable ? "Dopuszcza null" : "Null niedozwolony"}
          </p>
        </li>
      ))}
    </ul>
  );
}
