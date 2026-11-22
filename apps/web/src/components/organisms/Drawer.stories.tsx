import { Drawer } from "./Drawer";
import { Input } from "@/components/atoms";
import { Button } from "@/components/atoms";
import { Banner } from "@/components/molecules/Banner";
const meta = { title: "Organisms/Drawer" };
export default meta;
export const Default = {
  render: () => (
    <Drawer
      open
      onClose={() => {}}
      title="Potwierdzenie"
      description="Sprawdź dane przed zapisem."
      actions={<Button>Zapisz</Button>}
    >
      <Input aria-label="Nazwa dokumentu" />
    </Drawer>
  ),
};
export const Error = {
  render: () => (
    <Drawer
      open
      onClose={() => {}}
      title="Potwierdzenie"
      description="Sprawdź dane przed zapisem."
      actions={<Button>Zapisz</Button>}
    >
      <Input aria-label="Nazwa dokumentu" />
      <Banner tone="error">Nie udało się zapisać.</Banner>
    </Drawer>
  ),
};
export const Closed = {
  render: () => (
    <Drawer open={false} onClose={() => {}} title="Potwierdzenie">
      Treść
    </Drawer>
  ),
};
