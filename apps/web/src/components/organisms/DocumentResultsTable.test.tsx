import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { DocumentResultsTable } from "./DocumentResultsTable";
it("announces a failed retry without hiding document results", () => {
  render(
    <DocumentResultsTable
      documents={[]}
      onRetry={() => {}}
      retryPending={false}
      retryError
    />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Nie udało się ponowić analizy",
  );
});

import { seedDocuments } from "@/lib/api/mock/data";
it("retries only the failed document from the responsive results", () => {
  const retry = vi.fn();
  render(<DocumentResultsTable documents={seedDocuments().filter(d => d.id === "doc-6")} onRetry={retry} retryPending={false} retryError={false} />);
  fireEvent.click(screen.getAllByRole("button", { name: "Ponów" })[0]!);
  expect(retry).toHaveBeenCalledWith("doc-6");
});
