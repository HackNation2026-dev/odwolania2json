import { TwoPane } from "./TwoPane";

const meta = { title: "Templates/TwoPane" };
export default meta;
export const Default = {
  render: () => (
    <TwoPane left={<p>Treść dokumentu</p>} right={<p>Dane dokumentu</p>} />
  ),
};
export const WideLeft = {
  render: () => (
    <TwoPane
      ratio="60/40"
      mobileTabs={["PDF", "JSON"]}
      left={<p>Treść PDF</p>}
      right={<p>Treść JSON</p>}
    />
  ),
};
