import { SideNav } from "./SideNav";

const meta = { title: "Organisms/SideNav" };
export default meta;
export const Default = { render: () => <SideNav pathname="/dokumenty" /> };
export const Administration = {
  render: () => <SideNav pathname="/ustawienia" />,
};
