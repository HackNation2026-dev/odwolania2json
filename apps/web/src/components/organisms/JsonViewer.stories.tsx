import { JsonViewer } from "./JsonViewer";

const meta = { title: "Organisms/JsonViewer" };
export default meta;
export const Default = {
  render: () => <JsonViewer json={'{"przelew_bankowy": {"kwota": null}}'} />,
};
export const Blocked = {
  render: () => <JsonViewer json={'{"przelew_bankowy": {"kwota": null}}'} blocked />,
};
export const Empty = { render: () => <JsonViewer json={null} /> };
export const Foreign = { render: () => <JsonViewer json="{}" /> };
