import { EvidenceQuote } from "./EvidenceQuote";

const meta = { title: "Molecules/EvidenceQuote" };
export default meta;
export const Default = {
  render: () => (
    <EvidenceQuote
      quote="Wnoszę odwołanie"
      page={1}
      source="text"
      confidence={0.98}
      onSelect={() => {}}
    />
  ),
};
export const Ocr = {
  render: () => (
    <EvidenceQuote
      quote="Wnoszę odwołanie"
      page={1}
      source="ocr"
      confidence={0.7}
    />
  ),
};
