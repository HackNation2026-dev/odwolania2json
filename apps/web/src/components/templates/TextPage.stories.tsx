import { TextPage } from "./TextPage";

const meta = { title: "Templates/TextPage" };
export default meta;
export const Default = {
  render: () => (
    <TextPage title="Jak to działa" intro="Analiza dokumentów PDF">
      <section>
        <h2>Dodaj dokument</h2>
        <p>Wybierz plik PDF do analizy.</p>
      </section>
    </TextPage>
  ),
};
