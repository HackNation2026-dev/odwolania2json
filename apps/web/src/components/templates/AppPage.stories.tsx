import { AppPage } from "./AppPage";

const meta = { title: "Templates/AppPage" };
export default meta;
export const Default = {
  render: () => (
    <AppPage header={<h1>Dokumenty</h1>}>
      <p>Treść strony.</p>
    </AppPage>
  ),
};
