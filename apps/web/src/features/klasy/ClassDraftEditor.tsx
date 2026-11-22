import { Badge, Button, Card, Textarea } from "@/components/atoms";
import { CodeBlock, FormField } from "@/components/molecules";

type Props = {
  id: string;
  code: string;
  busy: boolean;
  valid: boolean;
  onChange: (code: string) => void;
  onSave: () => void;
};

export function ClassDraftEditor({
  id,
  code,
  busy,
  valid,
  onChange,
  onSave,
}: Props) {
  return (
    <Card className="space-y-4">
      <Badge tone="partial">Demonstracja · wersja robocza v2</Badge>
      <FormField
        label={`${id}.yaml · edycja demonstracyjna`}
        hint="Zmiana unieważnia poprzedni test. Aktywacja wymaga ponownej walidacji."
      >
        {(a11y) => (
          <Textarea
            {...a11y}
            rows={16}
            className="font-mono"
            disabled={busy}
            value={code}
            onChange={(event) => onChange(event.target.value)}
          />
        )}
      </FormField>
      <CodeBlock code={code} label="YAML wersji roboczej" />
      <Button
        touch
        variant="secondary"
        disabled={!valid || busy}
        onClick={onSave}
      >
        Zapisz i aktywuj wersję 2
      </Button>
    </Card>
  );
}
