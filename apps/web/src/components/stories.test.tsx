/// <reference types="vite/client" />
import { cleanup, render, screen } from "@testing-library/react";
import { composeStories, type Meta, type StoryFn } from "@storybook/react";
import { axe } from "jest-axe";
import { describe, expect, it, vi } from "vitest";
import type { PdfEditorProps, ToolbarApi } from "react-web-pdf-editor";

// jsdom nie renderuje PDF/canvas; prawdziwy edytor sprawdza e2e/pdf-viewer.spec.ts.
// Pozostają rzeczywisty pasek PdfViewer, adapter DOM, portale ramek i sprawdzenie axe.
vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
vi.mock("react-web-pdf-editor", () => ({
  PdfEditor: (props: PdfEditorProps) => {
    const noop = () => {};
    const api: ToolbarApi = {
      name: "PDF", setName: noop, canUndo: false, canRedo: false, undo: noop, redo: noop,
      shortcuts: { undo: "", redo: "", undoKeys: "", redoKeys: "" }, activeTool: "select", setTool: noop,
      exportPdf: noop, exporting: false, exportError: null,
      page: props.page ?? 1, numPages: 3, scale: props.scale ?? 1, minScale: .25, maxScale: 3, disabled: false,
      prevPage: noop, nextPage: noop, zoomIn: noop, zoomOut: noop, setScale: noop, setPage: noop,
      search: { query: "", matchCount: 0, currentIndex: 0, clear: noop, setQuery: noop, prev: noop, next: noop },
    };
    return <div>{props.toolbar?.(api)}{String(props.file).includes("missing") ? <p role="alert">Nie udało się wczytać PDF.</p> : [1, 2, 3].map(page => <div key={page} className="rpe-page" data-page-number={page} role="group" aria-label={`Strona PDF ${page}`} style={{ position: "relative", width: 595, height: 842 }}><canvas aria-hidden="true" /></div>)}</div>;
  },
}));

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
          if (path.endsWith("/PdfViewer.stories.tsx")) {
            await screen.findByRole("group", { name: "Nawigacja PDF" });
          }
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
