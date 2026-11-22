import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { HelpText } from "./HelpText";
const meta = {
  title: "Atoms/HelpText",
  component: HelpText,
  tags: ["autodocs"],
} satisfies Meta<typeof HelpText>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: { children: "Wprowadź sygnaturę widoczną w dokumencie." },
};
