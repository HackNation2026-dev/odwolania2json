import { PageHeader } from "./PageHeader";
import { Button } from "@/components/atoms";
const meta = { title: "Organisms/PageHeader" };
export default meta;
export const Default = {
  render: () => (
    <PageHeader
      breadcrumbs={[{ label: "Pulpit", href: "/" }, { label: "Dokumenty" }]}
      title="Dokumenty"
      subtitle="Przegląd wszystkich analiz"
      actions={<Button>Nowa analiza</Button>}
    />
  ),
};
