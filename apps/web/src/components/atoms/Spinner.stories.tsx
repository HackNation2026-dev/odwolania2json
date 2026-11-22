import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Spinner } from "./Spinner";
const meta = {
  title: "Atoms/Spinner",
  component: Spinner,
  tags: ["autodocs"],
} satisfies Meta<typeof Spinner>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = { args: {} };
export const CustomLabel: Story = { args: { label: "Wczytywanie dokumentu" } };
