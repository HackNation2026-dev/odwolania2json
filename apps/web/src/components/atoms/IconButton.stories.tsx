import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { IconButton } from "./IconButton";
const meta = {
  title: "Atoms/IconButton",
  component: IconButton,
  tags: ["autodocs"],
} satisfies Meta<typeof IconButton>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { label: "Dodaj dokument", icon: "plus" },
};
export const Secondary: Story = {
  args: { label: "Dodaj dokument", icon: "plus", variant: "secondary" },
};
export const Ghost: Story = {
  args: { label: "Dodaj dokument", icon: "plus", variant: "ghost" },
};
export const Danger: Story = {
  args: { label: "Dodaj dokument", icon: "plus", variant: "danger" },
};
export const Small: Story = {
  args: { label: "Dodaj dokument", icon: "plus", size: "sm" },
};
export const Large: Story = {
  args: { label: "Dodaj dokument", icon: "plus", size: "lg" },
};
export const Disabled: Story = {
  args: { label: "Dodaj dokument", icon: "plus", disabled: true },
};
export const Loading: Story = {
  args: { label: "Dodaj dokument", icon: "plus", loading: true },
};
