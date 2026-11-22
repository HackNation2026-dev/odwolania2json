import { Dialog } from "./Dialog";
import { Input } from "@/components/atoms";
import { Button } from "@/components/atoms";
import { Banner } from "@/components/molecules/Banner";
const meta = { title: "Organisms/Dialog" };
export default meta;
export const Default = {
  render: () => (
    <Dialog
      open
      onClose={() => {}}
      title="Potwierdzenie"
      description="Sprawdź dane przed zapisem."
      actions={<Button>Zapisz</Button>}
    >
      <Input aria-label="Nazwa dokumentu" />
    </Dialog>
  ),
};
export const Error = {
  render: () => (
    <Dialog
      open
      onClose={() => {}}
      title="Potwierdzenie"
      description="Sprawdź dane przed zapisem."
      actions={<Button>Zapisz</Button>}
    >
      <Input aria-label="Nazwa dokumentu" />
      <Banner tone="error">Nie udało się zapisać. Popraw dane.</Banner>
    </Dialog>
  ),
};
export const Closed = {
  render: () => (
    <Dialog open={false} onClose={() => {}} title="Potwierdzenie">
      Treść
    </Dialog>
  ),
};
