import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Label } from "./Label";
const meta = {
  title: "Atoms/Label",
  component: Label,
  tags: ["autodocs"],
} satisfies Meta<typeof Label>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { htmlFor: "label-example", children: "Sygnatura" },
};
export const Required: Story = {
  args: { htmlFor: "label-example", required: true, children: "Sygnatura" },
};
