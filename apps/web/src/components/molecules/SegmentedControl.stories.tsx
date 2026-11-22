import { SegmentedControl } from "./SegmentedControl";

const meta = { title: "Molecules/SegmentedControl" };
export default meta;
export const Default = {
  render: () => (
    <SegmentedControl
      label="Widok"
      value="list"
      onChange={() => {}}
      options={[
        { value: "list", label: "Lista" },
        { value: "grid", label: "Kafelki" },
        { value: "other", label: "Inny", disabled: true },
      ]}
    />
  ),
};
