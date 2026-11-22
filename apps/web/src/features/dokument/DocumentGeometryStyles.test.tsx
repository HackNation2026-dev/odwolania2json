import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";
import { seedDocuments } from "@/lib/api/mock/data";
import { DocumentGeometryStyles } from "./DocumentGeometryStyles";
afterEach(cleanup);
describe("document geometry styling", () => {
  it("keeps identifiers and line patterns alongside token based group colors", () => {
    const { container } = render(
      <DocumentGeometryStyles doc={seedDocuments()[0]!} />,
    );
    const rules = container.querySelector("style")!.textContent!;
    expect(rules).toContain("var(--evidence-border)");
    expect(rules).toContain("G2 · ");
    expect(rules).toContain("border-style:dashed");
    expect(rules).not.toMatch(/#[0-9a-f]{3,8}/i);
  });
  it("skips unsafe selectors from remote evidence identifiers", () => {
    const doc = structuredClone(seedDocuments()[0]!);
    doc.evidence[0]!.id = 'unsafe"]{}';
    doc.evidence[0]!.box = { x: 0.1, y: 0.1, w: 0.2, h: 0.1 };
    const { container } = render(<DocumentGeometryStyles doc={doc} />);
    expect(container.querySelector("style")!.textContent).not.toContain(
      "unsafe",
    );
  });
});
