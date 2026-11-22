import { SearchBox } from "./SearchBox";

const meta = { title: "Molecules/SearchBox" };
export default meta;
export const Default = { render: () => <SearchBox label="Szukaj dokumentu" /> };
export const Filled = {
  render: () => (
    <SearchBox
      label="Szukaj dokumentu"
      value="Odwołanie"
      onChange={() => {}}
      onClear={() => {}}
    />
  ),
};
export const Disabled = { render: () => <SearchBox disabled /> };
