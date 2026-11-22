import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";
vi.mock("next/dynamic", () => ({ default: () => Client }));
vi.mock("react-web-pdf-editor", () => ({
  PdfEditor: (props: Record<string, unknown>) => {
    const toolbar = props.toolbar as (api: object) => React.ReactNode;
    return (
      <div>
        {toolbar({
          page: 1,
          numPages: 3,
          scale: 1,
          minScale: 0.25,
          maxScale: 3,
          search: { query: "", matchCount: 0, setQuery: vi.fn() },
          nextPage: next,
          prevPage: vi.fn(),
          zoomIn: vi.fn(),
          zoomOut: vi.fn(),
        })}
        <div
          className="rpe-page"
          data-page-number="1"
          style={{ position: "relative", width: 600, height: 800 }}
        />
        <output>{String(props.workerSrc)}</output>
      </div>
    );
  },
}));
const next = vi.fn();
import Client from "./pdf/PdfViewerClient";
import { PdfViewer } from "./PdfViewer";
import { editorPages } from "./pdf/editorDom";
import type React from "react";
beforeAll(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
    },
  );
  Element.prototype.scrollIntoView = vi.fn();
});
describe("PdfViewer", () => {
  it("uses a local worker and exposes read-only navigation", () => {
    render(<PdfViewer file="/test.pdf" />);
    expect(screen.getByText("/pdf/pdf.worker.min.mjs")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Następna strona" }));
    expect(next).toHaveBeenCalledOnce();
    expect(
      screen.queryByRole("button", { name: /export|draw|signature/i }),
    ).toBeNull();
  });
  it("positions and labels evidence inside the versioned page DOM", async () => {
    const click = vi.fn();
    const { container } = render(
      <PdfViewer
        file="/test.pdf"
        highlights={[
          {
            id: "a",
            page: 1,
            label: "Fragment",
            active: true,
            box: { x: 0.1, y: 0.2, w: 0.3, h: 0.04 },
          },
        ]}
        onHighlightClick={click}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Dowód 1: Fragment" }),
      ).toBeInTheDocument(),
    );
    const proof = screen.getByRole("button", { name: "Dowód 1: Fragment" });
    expect(proof).toHaveStyle({
      left: "10%",
      top: "20%",
      width: "30%",
      height: "4%",
    });
    expect(editorPages(container)[0]).toContainElement(proof);
    fireEvent.click(proof);
    expect(click).toHaveBeenCalledWith("a");
  });
});
