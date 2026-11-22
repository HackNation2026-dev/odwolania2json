import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { DocumentResultTile } from "./DocumentResultTile";
export default {
  title: "Molecules/DocumentResultTile",
  component: DocumentResultTile,
  args: {
    document: {
      id: "demo",
      fileName: "odwolanie.pdf",
      status: "full",
      className: "Odwołanie do KIO",
      pages: 3,
      uploadedAt: "2026-11-21T10:00:00Z",
    },
    codes: [],
  },
} satisfies Meta<typeof DocumentResultTile>;
export const Default: StoryObj<typeof DocumentResultTile> = {};
export const Running: StoryObj<typeof DocumentResultTile> = {
  args: {
    document: {
      id: "demo",
      fileName: "odwolanie.pdf",
      status: "running",
      className: null,
      pages: 3,
      uploadedAt: "2026-11-21T10:00:00Z",
      progress: 40,
    },
  },
};
