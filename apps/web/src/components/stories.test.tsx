/// <reference types="vite/client" />
import { cleanup, render } from "@testing-library/react";
import { composeStories, type Meta, type StoryFn } from "@storybook/react";
import { axe } from "jest-axe";
import { describe, expect, it } from "vitest";

type StoryFile = { default: Meta; [name: string]: StoryFn | Meta };
const modules = import.meta.glob<StoryFile>(
  [
    "./atoms/**/*.stories.tsx",
    "./molecules/**/*.stories.tsx",
    "./organisms/**/*.stories.tsx",
    "./templates/**/*.stories.tsx",
  ],
  { eager: true },
);
for (const [path, file] of Object.entries(modules)) {
  describe(path, () => {
    const stories = composeStories(file);
    it("exports at least one story", () => {
      expect(Object.keys(stories).length).toBeGreaterThan(0);
    });
    for (const [name, Story] of Object.entries(stories)) {
      it.each(["light", "dark"])(
        `${name} has no serious or critical accessibility violations (%s)`,
        async (theme) => {
          document.documentElement.dataset.theme = theme;
          document.documentElement.lang = "pl";
          render(<Story />);
          const results = await axe(document.body, {
            rules: { "color-contrast": { enabled: false } },
          });
          expect(
            results.violations.filter(
              (v) => v.impact === "serious" || v.impact === "critical",
            ),
          ).toEqual([]);
          cleanup();
          delete document.documentElement.dataset.theme;
        },
      );
    }
  });
}
