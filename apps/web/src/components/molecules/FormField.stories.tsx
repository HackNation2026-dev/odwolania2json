import { FormField } from "./FormField";
import { Input } from "@/components/atoms";
const meta = { title: "Molecules/FormField" };
export default meta;
export const Default = {
  render: () => (
    <FormField label="Nazwa" hint="Nazwa dokumentu" required>
      {(a11y) => <Input {...a11y} />}
    </FormField>
  ),
};
export const Error = {
  render: () => (
    <FormField
      label="Nazwa"
      hint="Nazwa dokumentu"
      error="Uzupełnij nazwę"
      required
    >
      {(a11y) => <Input {...a11y} />}
    </FormField>
  ),
};
export const Optional = {
  render: () => (
    <FormField label="Opis">{(a11y) => <Input {...a11y} />}</FormField>
  ),
};
