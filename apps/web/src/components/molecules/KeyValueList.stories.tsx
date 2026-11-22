import { KeyValueList } from "./KeyValueList";

const meta = { title: "Molecules/KeyValueList" };
export default meta;
export const Default = {
  render: () => (
    <KeyValueList
      items={[
        { key: "name", label: "Nazwa", value: "Odwołanie.pdf" },
        { key: "date", label: "Data", value: null },
      ]}
    />
  ),
};
export const Empty = { render: () => <KeyValueList items={[]} /> };
