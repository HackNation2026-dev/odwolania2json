import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { StatusBadge } from "./StatusBadge";
const meta = {
  title: "Atoms/StatusBadge",
  component: StatusBadge,
  tags: ["autodocs"],
} satisfies Meta<typeof StatusBadge>;
export default meta;
type Story = StoryObj<typeof meta>;
export const ReferenceDefault: Story = {
  name: "Domyślny — referencja 7529512",
  args: { status: "full" },
};
export const SvgIcon: Story = {
  name: "Opcjonalna ikona SVG",
  args: { status: "full", iconVariant: "svg" },
};
export const Full: Story = { args: { status: "full" } };
export const Partial: Story = { args: { status: "partial" } };
export const Foreign: Story = { args: { status: "foreign" } };
export const Error: Story = { args: { status: "error" } };
export const Running: Story = { args: { status: "running" } };
export const Ambiguous: Story = { args: { status: "ambiguous" } };
export const Multi: Story = { args: { status: "multi" } };
