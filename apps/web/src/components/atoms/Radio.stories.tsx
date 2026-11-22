import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Radio } from "./Radio";
const meta = {
  title: "Atoms/Radio",
  component: Radio,
  tags: ["autodocs"],
} satisfies Meta<typeof Radio>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { label: "Odwołanie", name: "document-class" },
};
export const Checked: Story = {
  args: { label: "Odwołanie", name: "document-class", defaultChecked: true },
};
export const Disabled: Story = {
  args: { label: "Odwołanie", name: "document-class", disabled: true },
};
export const DisabledChecked: Story = {
  args: {
    label: "Odwołanie",
    name: "document-class",
    disabled: true,
    defaultChecked: true,
  },
};
export const Invalid: Story = {
  args: { label: "Odwołanie", name: "document-class", invalid: true },
};
