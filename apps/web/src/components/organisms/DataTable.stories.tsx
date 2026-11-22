import { DataTable } from "./DataTable";

const meta = { title: "Organisms/DataTable" };
export default meta;
export const Default = {
  render: () => (
    <DataTable
      columns={[
        {
          key: "name",
          label: "Nazwa",
          render: (row: { id: string; name: string }) => row.name,
          sortValue: (row: { id: string; name: string }) => row.name,
        },
      ]}
      rows={[
        { id: "1", name: "Odwołanie.pdf" },
        { id: "2", name: "Decyzja.pdf" },
      ]}
      rowKey={(row) => row.id}
      cardTitle={(row) => row.name}
      caption="Dokumenty"
    />
  ),
};
export const Empty = {
  render: () => (
    <DataTable
      columns={[
        {
          key: "name",
          label: "Nazwa",
          render: (row: { id: string; name: string }) => row.name,
        },
      ]}
      rows={[]}
      rowKey={(row) => row.id}
      cardTitle={(row) => row.name}
      caption="Dokumenty"
    />
  ),
};
export const Loading = {
  render: () => (
    <DataTable
      columns={[
        {
          key: "name",
          label: "Nazwa",
          render: (row: { id: string; name: string }) => row.name,
          sortValue: (row: { id: string; name: string }) => row.name,
        },
      ]}
      rows={[
        { id: "1", name: "Odwołanie.pdf" },
        { id: "2", name: "Decyzja.pdf" },
      ]}
      rowKey={(row) => row.id}
      cardTitle={(row) => row.name}
      caption="Dokumenty"
      loading
    />
  ),
};
export const Error = {
  render: () => (
    <DataTable
      columns={[
        {
          key: "name",
          label: "Nazwa",
          render: (row: { id: string; name: string }) => row.name,
          sortValue: (row: { id: string; name: string }) => row.name,
        },
      ]}
      rows={[
        { id: "1", name: "Odwołanie.pdf" },
        { id: "2", name: "Decyzja.pdf" },
      ]}
      rowKey={(row) => row.id}
      cardTitle={(row) => row.name}
      caption="Dokumenty"
      error="Usługa niedostępna"
      onRetry={() => {}}
    />
  ),
};
