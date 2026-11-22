import { AppShell } from "./AppShell";

const meta = { title: "Organisms/AppShell" };
export default meta;
export const Default = {
  render: () => (
    <AppShell>
      <h1>Dokumenty</h1>
      <p>Treść strony.</p>
    </AppShell>
  ),
};
