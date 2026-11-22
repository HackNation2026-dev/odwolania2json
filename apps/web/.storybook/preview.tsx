import type { Preview } from "@storybook/nextjs-vite";
import { useLayoutEffect } from "react";
import "../src/styles/globals.css";

export function ThemeFrame({
  theme,
  children,
}: {
  theme: string;
  children: React.ReactNode;
}) {
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.lang = "pl";
  }, [theme]);
  return <div className="min-h-24 bg-bg p-4 text-fg">{children}</div>;
}
const preview: Preview = {
  globalTypes: {
    theme: {
      description: "Motyw",
      toolbar: {
        title: "Motyw",
        icon: "circlehollow",
        dynamicTitle: true,
        items: [
          { value: "light", title: "Jasny" },
          { value: "dark", title: "Ciemny" },
        ],
      },
    },
  },
  initialGlobals: { theme: "light" },
  decorators: [
    (Story, context) => (
      <ThemeFrame theme={context.globals.theme ?? "light"}>
        <Story />
      </ThemeFrame>
    ),
  ],
  parameters: {
    nextjs: { appDirectory: true },
    a11y: { test: "error" },
    viewport: {
      options: Object.fromEntries(
        [320, 360, 768, 1024, 1440].map((width) => [
          String(width),
          {
            name: `${width} px`,
            styles: { width: `${width}px`, height: "900px" },
            type: width < 768 ? "mobile" : width < 1024 ? "tablet" : "desktop",
          },
        ]),
      ),
    },
  },
};
export default preview;
