import { CodeBlock } from "./CodeBlock";

const meta = { title: "Molecules/CodeBlock" };
export default meta;
export const Default = {
  render: () => (
    <CodeBlock code={'{"przelew_bankowy": {"kwota": null}}'} copyLabel="Kopiuj JSON" />
  ),
};
export const NoWrap = {
  render: () => (
    <CodeBlock code={"Bardzo długa linia danych ".repeat(20)} wrap={false} />
  ),
};
export const Blocked = { render: () => <CodeBlock code="{}" copyDisabled /> };
export const Empty = { render: () => <CodeBlock code="" /> };
