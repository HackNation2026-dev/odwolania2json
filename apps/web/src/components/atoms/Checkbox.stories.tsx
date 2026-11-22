import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Checkbox } from "./Checkbox";
const meta = {
  title: "Atoms/Checkbox",
  component: Checkbox,
  tags: ["autodocs"],
} satisfies Meta<typeof Checkbox>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = { args: { label: "Akceptuję" } };
export const Checked: Story = {
  args: { label: "Akceptuję", defaultChecked: true },
};
export const Disabled: Story = { args: { label: "Akceptuję", disabled: true } };
export const DisabledChecked: Story = {
  args: { label: "Akceptuję", disabled: true, defaultChecked: true },
};
export const Invalid: Story = { args: { label: "Akceptuję", invalid: true } };
