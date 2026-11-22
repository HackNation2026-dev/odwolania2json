import { DropZone } from "./DropZone";

const meta = { title: "Molecules/DropZone" };
export default meta;
export const Default = { render: () => <DropZone onFiles={() => {}} /> };
export const Disabled = {
  render: () => <DropZone onFiles={() => {}} disabled />,
};
