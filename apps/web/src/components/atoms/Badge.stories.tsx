import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Badge } from "./Badge";
const meta = {
  title: "Atoms/Badge",
  component: Badge,
  tags: ["autodocs"],
} satisfies Meta<typeof Badge>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Neutral: Story = {
  args: { tone: "neutral", children: "Dokument" },
};
export const Full: Story = { args: { tone: "full", children: "Pełny" } };
export const Partial: Story = {
  args: { tone: "partial", children: "Częściowy" },
};
export const Error: Story = { args: { tone: "error", children: "Błąd" } };
export const Running: Story = { args: { tone: "running", children: "W toku" } };
export const Ambiguous: Story = {
  args: { tone: "ambiguous", children: "Niejednoznaczny" },
};
export const Info: Story = { args: { tone: "info", children: "Informacja" } };
