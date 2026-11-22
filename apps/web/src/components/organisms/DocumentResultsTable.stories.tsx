import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { seedDocuments } from "@/lib/api/mock/data";
import { DocumentResultsTable } from "./DocumentResultsTable";
export default {
  title: "Organisms/DocumentResultsTable",
  component: DocumentResultsTable,
  args: {
    documents: [],
    onRetry: () => {},
    retryPending: false,
    retryError: false,
  },
} satisfies Meta<typeof DocumentResultsTable>;
export const Empty: StoryObj<typeof DocumentResultsTable> = {};
export const RetryFailed: StoryObj<typeof DocumentResultsTable> = {
  args: { retryError: true },
};

export const Results: StoryObj<typeof DocumentResultsTable> = { args: { documents: seedDocuments().slice(0, 8) } };
