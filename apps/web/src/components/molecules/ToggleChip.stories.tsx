import { ToggleChip } from "./ToggleChip";

const meta = { title: "Molecules/ToggleChip" };
export default meta;
export const Default = {
  render: () => (
    <ToggleChip pressed={false} count={12}>
      Wymaga uwagi
    </ToggleChip>
  ),
};
export const Pressed = {
  render: () => (
    <ToggleChip pressed count={4}>
      Wymaga uwagi
    </ToggleChip>
  ),
};
export const Disabled = {
  render: () => (
    <ToggleChip pressed={false} disabled>
      Wymaga uwagi
    </ToggleChip>
  ),
};
