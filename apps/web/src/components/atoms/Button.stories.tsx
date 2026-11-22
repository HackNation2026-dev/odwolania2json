import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Button } from "./Button";
import { Icon } from "./Icon";
const meta = {
  title: "Atoms/Button",
  component: Button,
  tags: ["autodocs"],
} satisfies Meta<typeof Button>;
export default meta;
type Story = StoryObj<typeof meta>;
export const ReferenceDefault: Story = {
  name: "Domyślny — referencja 7529512",
  args: { children: "Zapisz" },
};
export const ReferenceMedium: Story = {
  name: "Rozmiar md — referencja 7529512",
  args: { children: "Zapisz", size: "md" },
};
export const Touch: Story = {
  name: "Opcjonalny cel dotykowy 44 px",
  args: { children: "Zapisz", touch: true },
};
export const Primary: Story = {
  args: { children: "Zapisz", variant: "primary" },
};
export const Secondary: Story = {
  args: { children: "Zapisz", variant: "secondary" },
};
export const Ghost: Story = { args: { children: "Zapisz", variant: "ghost" } };
export const Danger: Story = {
  args: { children: "Zapisz", variant: "danger" },
};
export const Small: Story = { args: { children: "Zapisz", size: "sm" } };
export const Large: Story = { args: { children: "Zapisz", size: "lg" } };
export const Disabled: Story = { args: { children: "Zapisz", disabled: true } };
export const Loading: Story = { args: { children: "Zapisz", loading: true } };
export const FullWidth: Story = {
  args: { children: "Zapisz", fullWidth: true },
};
export const Icons: Story = {
  args: {
    children: "Zapisz",
    leadingIcon: <Icon name="check" />,
    trailingIcon: <Icon name="chevron-right" />,
  },
};
