import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { ConfigurationFieldList } from "./ConfigurationFieldList";

const meta = {
  title: "Molecules/ConfigurationFieldList",
  component: ConfigurationFieldList,
  args: {
    fields: [
      {
        key: "data_operacji",
        label: "Data operacji",
        type: "data",
        description: "Data wykonania płatności.",
        required: true,
        nullable: false,
      },
      {
        key: "oznaczenie_sprawy",
        label: "Oznaczenie sprawy",
        type: "tekst",
        description: "Pole demonstracyjne.",
        required: false,
        nullable: true,
      },
    ],
  },
} satisfies Meta<typeof ConfigurationFieldList>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Rules: Story = {};
export const Empty: Story = { args: { fields: [] } };
