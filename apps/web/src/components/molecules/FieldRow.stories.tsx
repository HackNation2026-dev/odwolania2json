import { FieldRow } from "./FieldRow";

const meta = { title: "Molecules/FieldRow" };
export default meta;
export const Default = {
  render: () => (
    <FieldRow
      label="Sygnatura"
      fieldKey="sygnatura"
      value="KIO 123/26"
      state="ok"
      onSelect={() => {}}
      onEdit={() => {}}
    />
  ),
};
export const Missing = {
  render: () => (
    <FieldRow
      label="Sygnatura"
      fieldKey="sygnatura"
      value={null}
      state="missing"
      active={true}
    />
  ),
};
export const Computed = {
  render: () => (
    <FieldRow
      label="Sygnatura"
      fieldKey="sygnatura"
      value={"KIO 123/26"}
      state="computed"
      active={true}
    />
  ),
};
export const Corrected = {
  render: () => (
    <FieldRow
      label="Sygnatura"
      fieldKey="sygnatura"
      value={"KIO 123/26"}
      state="corrected"
      active={true}
    />
  ),
};
