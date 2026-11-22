import { AppShellPreferences } from "./AppShellPreferences";
const meta = {
  title: "Organisms/AppShellPreferences",
  component: AppShellPreferences,
};
export default meta;
export const Default = {
  render: () => (
    <>
      <AppShellPreferences />
      <p>Preferencje dostępności i gęstości zapisane na tym urządzeniu.</p>
    </>
  ),
};
