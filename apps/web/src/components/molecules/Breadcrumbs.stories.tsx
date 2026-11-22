import { Breadcrumbs } from "./Breadcrumbs";

const meta = { title: "Molecules/Breadcrumbs" };
export default meta;
export const Default = {
  render: () => (
    <Breadcrumbs
      items={[
        { label: "Pulpit", href: "/" },
        { label: "Dokumenty", href: "/dokumenty" },
        { label: "Odwołanie.pdf" },
      ]}
    />
  ),
};
