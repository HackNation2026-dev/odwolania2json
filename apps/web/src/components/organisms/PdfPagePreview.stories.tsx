import { PdfPagePreview } from "./PdfPagePreview";

const meta = { title: "Organisms/PdfPagePreview" };
export default meta;
export const Default = {
  render: () => (
    <PdfPagePreview
      pages={2}
      page={1}
      onPageChange={() => {}}
      pageText={["Wnoszę odwołanie.", "Uzasadnienie."]}
      evidence={[
        {
          id: "e1",
          page: 1,
          quote: "Wnoszę odwołanie",
          source: "ocr",
          confidence: 0.8,
          box: { x: 0.1, y: 0.4, w: 0.8, h: 0.1 },
        },
      ]}
    />
  ),
};
export const Empty = {
  render: () => (
    <PdfPagePreview pages={0} page={1} onPageChange={() => {}} pageText={[]} />
  ),
};
export const MissingText = {
  render: () => (
    <PdfPagePreview pages={1} page={1} onPageChange={() => {}} pageText={[]} />
  ),
};
