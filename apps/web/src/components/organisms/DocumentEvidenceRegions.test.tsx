import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  DocumentEvidenceRegions,
  regionsOverlap,
  type EvidenceRegion,
} from "./DocumentEvidenceRegions";
afterEach(cleanup);
const first: EvidenceRegion = {
  id: "e1",
  page: 1,
  fieldKey: "nazwa",
  groupId: "G2",
  groupLabel: "Odwołujący",
  box: { x: 0.1, y: 0.2, w: 0.4, h: 0.03 },
};
describe("document evidence regions", () => {
  it("cycles multiple areas across pages and keeps identifiers in the legend", async () => {
    const onSelect = vi.fn();
    render(
      <DocumentEvidenceRegions
        regions={[first, { ...first, id: "e2", page: 2 }]}
        selected="e1"
        onSelect={onSelect}
      />,
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Następny obszar" }),
    );
    expect(onSelect).toHaveBeenCalledWith("e2");
    await userEvent.click(
      screen.getByText("Legenda obszarów i powiązania pól"),
    );
    expect(
      screen.getByRole("button", { name: /G2 · 2 · str. 2 · e2/ }),
    ).toBeVisible();
  });
  it("warns about collisions without merging bounding boxes", () => {
    render(
      <DocumentEvidenceRegions
        regions={[first, { ...first, id: "other", groupId: "G3" }]}
        selected="e1"
        onSelect={vi.fn()}
      />,
    );
    expect(
      screen.getByText("Grupy nakładają się. Pokazano oznaczenia pól."),
    ).toBeVisible();
  });
  it("does not report intersections on different pages or without geometry", () => {
    expect(regionsOverlap(first, { ...first, page: 2 })).toBe(false);
    expect(regionsOverlap(first, { ...first, box: undefined })).toBe(false);
  });
});
