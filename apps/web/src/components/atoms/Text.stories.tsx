import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Text } from "./Text";
const meta = {
  title: "Atoms/Text",
  component: Text,
  tags: ["autodocs"],
} satisfies Meta<typeof Text>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { children: "Dokument oczekuje na weryfikację." },
};
export const Small: Story = {
  args: { children: "Dokument oczekuje na weryfikację.", size: "sm" },
};
export const Muted: Story = {
  args: { children: "Dokument oczekuje na weryfikację.", tone: "muted" },
};
export const Inline: Story = {
  args: { children: "Dokument oczekuje na weryfikację.", as: "span" },
};
