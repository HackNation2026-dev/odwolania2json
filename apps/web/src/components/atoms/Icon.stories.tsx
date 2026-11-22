import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Icon, iconPaths, type IconName } from "./Icon";
const meta = {
  title: "Atoms/Icon",
  component: Icon,
  tags: ["autodocs"],
} satisfies Meta<typeof Icon>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = { args: { name: "check", label: "Gotowe" } };
export const Decorative: Story = { args: { name: "info" } };
export const Small: Story = {
  args: { name: "search", size: 16, label: "Szukaj" },
};
export const Large: Story = { args: { name: "menu", size: 24, label: "Menu" } };

export const AllIcons: Story = {
  args: { name: "check" },
  render: () => (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
      {(Object.keys(iconPaths) as IconName[]).map((name) => (
        <div key={name} className="flex items-center gap-2">
          <Icon name={name} />
          <span>{name}</span>
        </div>
      ))}
    </div>
  ),
};
