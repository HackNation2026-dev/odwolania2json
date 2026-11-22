import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Input } from "./Input";
const meta = {
  title: "Atoms/Input",
  component: Input,
  tags: ["autodocs"],
} satisfies Meta<typeof Input>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { "aria-label": "Sygnatura", placeholder: "KIO 123/26" },
};
export const Filled: Story = {
  args: { "aria-label": "Sygnatura", defaultValue: "KIO 123/26" },
};
export const Disabled: Story = {
  args: { "aria-label": "Sygnatura", disabled: true },
};
export const Invalid: Story = {
  args: { "aria-label": "Sygnatura", invalid: true },
};
export const ReadOnly: Story = {
  args: {
    "aria-label": "Sygnatura",
    readOnly: true,
    defaultValue: "KIO 123/26",
  },
};
