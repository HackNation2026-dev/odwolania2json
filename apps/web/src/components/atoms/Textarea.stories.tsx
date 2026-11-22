import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Textarea } from "./Textarea";
const meta = {
  title: "Atoms/Textarea",
  component: Textarea,
  tags: ["autodocs"],
} satisfies Meta<typeof Textarea>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { "aria-label": "Uwagi", placeholder: "Wpisz uwagi" },
};
export const Filled: Story = {
  args: { "aria-label": "Uwagi", defaultValue: "Uwagi do dokumentu" },
};
export const Disabled: Story = {
  args: { "aria-label": "Uwagi", disabled: true },
};
export const Invalid: Story = {
  args: { "aria-label": "Uwagi", invalid: true },
};
export const ReadOnly: Story = {
  args: { "aria-label": "Uwagi", readOnly: true, defaultValue: "Uwagi" },
};
