import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { VisuallyHidden } from "./VisuallyHidden";
const meta = {
  title: "Atoms/VisuallyHidden",
  component: VisuallyHidden,
  tags: ["autodocs"],
} satisfies Meta<typeof VisuallyHidden>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { children: "Tekst dla czytnika ekranu" },
};
