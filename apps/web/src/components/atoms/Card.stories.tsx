import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Card } from "./Card";
const meta = {
  title: "Atoms/Card",
  component: Card,
  tags: ["autodocs"],
} satisfies Meta<typeof Card>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { children: "Dokument sprawy", tone: "default" },
};
export const Raised: Story = {
  args: { children: "Dokument sprawy", tone: "raised" },
};
export const Subtle: Story = {
  args: { children: "Dokument sprawy", tone: "subtle" },
};
export const Full: Story = {
  args: { children: "Dokument sprawy", tone: "full" },
};
export const Partial: Story = {
  args: { children: "Dokument sprawy", tone: "partial" },
};
export const Error: Story = {
  args: { children: "Dokument sprawy", tone: "error" },
};
export const Running: Story = {
  args: { children: "Dokument sprawy", tone: "running" },
};
export const Ambiguous: Story = {
  args: { children: "Dokument sprawy", tone: "ambiguous" },
};
export const NonePadding: Story = {
  args: { children: "Dokument sprawy", padding: "none" },
};
export const SmPadding: Story = {
  args: { children: "Dokument sprawy", padding: "sm" },
};
export const MdPadding: Story = {
  args: { children: "Dokument sprawy", padding: "md" },
};
export const LgPadding: Story = {
  args: { children: "Dokument sprawy", padding: "lg" },
};
