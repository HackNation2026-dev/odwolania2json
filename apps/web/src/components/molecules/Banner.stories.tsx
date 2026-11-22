import { Banner } from "./Banner";
import { Button } from "@/components/atoms";
const meta = { title: "Molecules/Banner" };
export default meta;
export const Default = {
  render: () => (
    <Banner tone="info" title="Informacja">
      Dokument został dodany.
    </Banner>
  ),
};
export const Success = {
  render: () => (
    <Banner
      tone="success"
      title="Zapisano"
      actions={<Button variant="secondary">Szczegóły</Button>}
    >
      Treść komunikatu.
    </Banner>
  ),
};
export const Warning = {
  render: () => (
    <Banner
      tone="warning"
      title="Sprawdź dokument"
      actions={<Button variant="secondary">Szczegóły</Button>}
    >
      Treść komunikatu.
    </Banner>
  ),
};
export const Error = {
  render: () => (
    <Banner
      tone="error"
      title="Błąd zapisu"
      actions={<Button variant="secondary">Szczegóły</Button>}
    >
      Treść komunikatu.
    </Banner>
  ),
};
export const Neutral = {
  render: () => (
    <Banner
      tone="neutral"
      title="Tryb demonstracyjny"
      actions={<Button variant="secondary">Szczegóły</Button>}
    >
      Treść komunikatu.
    </Banner>
  ),
};
