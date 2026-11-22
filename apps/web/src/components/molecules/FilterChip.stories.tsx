import { FilterChip } from "./ToggleChip";

const meta = { title: "Molecules/FilterChip" };
export default meta;
export const Default = {
  render: () => (
    <FilterChip pressed={false} count={5}>
      OCR
    </FilterChip>
  ),
};
export const Pressed = {
  render: () => (
    <FilterChip pressed count={0}>
      OCR
    </FilterChip>
  ),
};
