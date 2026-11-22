import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { ErrorText } from "./ErrorText";
const meta = {
  title: "Atoms/ErrorText",
  component: ErrorText,
  tags: ["autodocs"],
} satisfies Meta<typeof ErrorText>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = { args: { children: "To pole jest wymagane." } };
