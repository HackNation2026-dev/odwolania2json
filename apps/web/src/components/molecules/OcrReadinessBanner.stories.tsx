import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { OcrReadinessBanner } from "./OcrReadinessBanner";
export default {
  title: "Molecules/OcrReadinessBanner",
  component: OcrReadinessBanner,
  args: {
    mode: "shim",
    name: "Zamiennik demonstracyjny",
    version: null,
    detail:
      "Oznaczenie zamiennika zostaje przy dowodzie i w pobranych dowodach.",
  },
} satisfies Meta<typeof OcrReadinessBanner>;
export const Shim: StoryObj<typeof OcrReadinessBanner> = {};
export const Unavailable: StoryObj<typeof OcrReadinessBanner> = {
  args: { mode: "unavailable" },
};
