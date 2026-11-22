import { FilterBar } from "./FilterBar";
import { FilterChip } from "@/components/molecules/ToggleChip";
const meta = { title: "Organisms/FilterBar" };
export default meta;
export const Default = {
  render: () => (
    <FilterBar
      query=""
      onQueryChange={() => {}}
      shown={12}
      total={20}
      onReset={() => {}}
    >
      <FilterChip pressed={false} count={3}>
        Wymaga uwagi
      </FilterChip>
    </FilterBar>
  ),
};
