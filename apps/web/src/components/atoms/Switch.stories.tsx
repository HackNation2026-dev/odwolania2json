import { useState } from "react";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Switch } from "./Switch";
const meta = {
  title: "Atoms/Switch",
  component: Switch,
  tags: ["autodocs"],
} satisfies Meta<typeof Switch>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { label: "Powiadomienia", checked: false, onCheckedChange: () => {} },
};
export const Checked: Story = {
  args: { label: "Powiadomienia", checked: true, onCheckedChange: () => {} },
};
export const Disabled: Story = {
  args: {
    label: "Powiadomienia",
    checked: false,
    onCheckedChange: () => {},
    disabled: true,
  },
};
export const Interactive: Story = {
  args: { label: "Powiadomienia", checked: false, onCheckedChange: () => {} },
  render: function Example(args) {
    const [checked, setChecked] = useState(args.checked);
    return <Switch {...args} checked={checked} onCheckedChange={setChecked} />;
  },
};
