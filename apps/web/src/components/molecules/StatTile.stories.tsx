import { StatTile } from "./StatTile";

const meta = { title: "Molecules/StatTile" };
export default meta;
export const Default = {
  render: () => (
    <StatTile label="Dokumenty" value={42} hint="W bieżącym projekcie" />
  ),
};
export const Empty = { render: () => <StatTile label="Dokumenty" value={0} /> };
