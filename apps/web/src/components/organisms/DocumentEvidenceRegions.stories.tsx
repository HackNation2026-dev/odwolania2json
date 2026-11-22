import type { Meta, StoryObj } from "@storybook/react";
import { DocumentEvidenceRegions } from "./DocumentEvidenceRegions";
const regions = [
  {
    id: "e1",
    page: 1,
    fieldKey: "nazwa",
    groupId: "G2",
    groupLabel: "Odwołujący",
    box: { x: 0.1, y: 0.2, w: 0.4, h: 0.03 },
  },
  {
    id: "e2",
    page: 2,
    fieldKey: "nazwa",
    groupId: "G2",
    groupLabel: "Odwołujący",
    box: { x: 0.1, y: 0.4, w: 0.4, h: 0.03 },
  },
];
const meta = {
  title: "Organisms/DocumentEvidenceRegions",
  component: DocumentEvidenceRegions,
  args: { regions, selected: "e1", onSelect: () => {} },
} satisfies Meta<typeof DocumentEvidenceRegions>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Multiple: Story = {};
export const Collision: Story = {
  args: {
    regions: [
      ...regions,
      {
        ...regions[0]!,
        id: "e3",
        fieldKey: "zamawiajacy",
        groupId: "G3",
        groupLabel: "Zamawiający",
      },
    ],
  },
};
export const MissingGeometry: Story = {
  args: { regions: regions.map((item) => ({ ...item, box: undefined })) },
};
export const Empty: Story = { args: { regions: [] } };
