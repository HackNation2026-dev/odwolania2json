import { CenteredCard } from "./CenteredCard";
import { Input } from "@/components/atoms";
import { Button } from "@/components/atoms";
const meta = { title: "Templates/CenteredCard" };
export default meta;
export const Default = {
  render: () => (
    <CenteredCard title="Klucz API">
      <p>Skonfiguruj dostęp do modelu.</p>
      <Input aria-label="Klucz API" type="password" autoComplete="off" />
      <Button>Zapisz klucz</Button>
    </CenteredCard>
  ),
};
