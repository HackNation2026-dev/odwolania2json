import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { TextLink } from "./TextLink";
const meta = {
  title: "Atoms/TextLink",
  component: TextLink,
  tags: ["autodocs"],
} satisfies Meta<typeof TextLink>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { href: "/dokumenty", children: "Dokumenty" },
};
export const External: Story = {
  args: { href: "https://www.gov.pl", children: "Serwis gov.pl" },
};
