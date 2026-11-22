import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Heading } from "./Heading";
const meta = {
  title: "Atoms/Heading",
  component: Heading,
  tags: ["autodocs"],
} satisfies Meta<typeof Heading>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Level1: Story = { args: { level: 1, children: "Dokumenty" } };
export const Level2: Story = { args: { level: 2, children: "Dokumenty" } };
export const Level3: Story = { args: { level: 3, children: "Dokumenty" } };
export const Level4: Story = { args: { level: 4, children: "Dokumenty" } };
export const Sm: Story = {
  args: { level: 2, size: "sm", children: "Dokumenty" },
};
export const Md: Story = {
  args: { level: 2, size: "md", children: "Dokumenty" },
};
export const Lg: Story = {
  args: { level: 2, size: "lg", children: "Dokumenty" },
};
export const Xl: Story = {
  args: { level: 2, size: "xl", children: "Dokumenty" },
};
export const CustomElement: Story = {
  args: { level: 2, as: "div", children: "Dokumenty" },
};
