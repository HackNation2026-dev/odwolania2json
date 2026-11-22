import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { PdfViewer } from "./PdfViewer";
import geometry from "../../../public/demo-pdf/odwolanie.json";
const meta = {
  title: "Organisms/PdfViewer",
  component: PdfViewer,
  args: { file: "/demo-pdf/odwolanie.pdf" },
} satisfies Meta<typeof PdfViewer>;
export default meta;
type Story = StoryObj<typeof meta>;
export const OneDocument: Story = {
  args: { file: "/demo-pdf/pelnomocnictwo.pdf" },
};
export const MultiplePages: Story = { args: { page: 2 } };
export const Highlights: Story = { args: { highlights: geometry } };
export const ActiveEvidence: Story = {
  args: { highlights: geometry.map((h, i) => ({ ...h, active: i === 3 })) },
};
export const LoadingError: Story = { args: { file: "/demo-pdf/missing.pdf" } };
export const ScanWithoutText: Story = {
  args: { file: "/demo-pdf/skan-odwolanie.pdf" },
};
export const Dark: Story = {
  ...ActiveEvidence,
  decorators: [
    (Story) => (
      <div data-theme="dark">
        <Story />
      </div>
    ),
  ],
};
