import { EmptyState } from "./EmptyState";
import { Button } from "@/components/atoms";
const meta = { title: "Molecules/EmptyState" };
export default meta;
export const Default = {
  render: () => (
    <EmptyState
      title="Brak dokumentów"
      description="Dodaj pierwszy plik PDF."
      action={<Button>Dodaj dokument</Button>}
    />
  ),
};
