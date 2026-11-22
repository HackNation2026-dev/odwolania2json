import { ProgressBar } from "./ProgressBar";

const meta = { title: "Molecules/ProgressBar" };
export default meta;
export const Default = {
  render: () => <ProgressBar label="Analiza" value={45} />,
};
export const Pending = {
  render: () => <ProgressBar label="Analiza" value={0} />,
};
export const Complete = {
  render: () => <ProgressBar label="Analiza" value={100} />,
};
