import { NavItem } from "./NavItem";

const meta = { title: "Molecules/NavItem" };
export default meta;
export const Default = {
  render: () => <NavItem href="/dokumenty" label="Dokumenty" icon="▤" />,
};
export const Active = {
  render: () => <NavItem href="/dokumenty" label="Dokumenty" icon="▤" active />,
};
