import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Select } from "./Select";
const meta = {
  title: "Atoms/Select",
  component: Select,
  tags: ["autodocs"],
} satisfies Meta<typeof Select>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {
  args: {
    "aria-label": "Klasa",
    children: (
      <>
        <option value="appeal">Odwołanie</option>
        <option value="decision">Wyrok</option>
      </>
    ),
  },
};
export const Disabled: Story = {
  args: {
    "aria-label": "Klasa",
    children: (
      <>
        <option value="appeal">Odwołanie</option>
        <option value="decision">Wyrok</option>
      </>
    ),
    disabled: true,
  },
};
export const Invalid: Story = {
  args: {
    "aria-label": "Klasa",
    children: (
      <>
        <option value="appeal">Odwołanie</option>
        <option value="decision">Wyrok</option>
      </>
    ),
    invalid: true,
  },
};
