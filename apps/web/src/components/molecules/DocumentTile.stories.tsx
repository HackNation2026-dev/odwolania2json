import { DocumentTile } from "./DocumentTile";

const meta = { title: "Molecules/DocumentTile" };
export default meta;
export const Default = {
  render: () => (
    <DocumentTile
      href="/dokumenty/1"
      fileName="Odwołanie.pdf"
      status="full"
      className="Odwołanie"
      pages={3}
      date="21.11.2026"
    />
  ),
};
export const Partial = {
  render: () => (
    <DocumentTile
      href="/dokumenty/1"
      fileName="Odwołanie.pdf"
      status="partial"
      pages={3}
      codes={["BRAK_DANYCH"]}
    />
  ),
};
export const Error = {
  render: () => (
    <DocumentTile
      href="/dokumenty/1"
      fileName="Odwołanie.pdf"
      status="error"
      pages={3}
      codes={["BRAK_DANYCH"]}
    />
  ),
};
export const Running = {
  render: () => (
    <DocumentTile
      href="/dokumenty/1"
      fileName="Odwołanie.pdf"
      status="running"
      pages={3}
      codes={["BRAK_DANYCH"]}
      progress={45}
    />
  ),
};
export const Ambiguous = {
  render: () => (
    <DocumentTile
      href="/dokumenty/1"
      fileName="Odwołanie.pdf"
      status="ambiguous"
      pages={3}
      codes={["BRAK_DANYCH"]}
    />
  ),
};
export const Multi = {
  render: () => (
    <DocumentTile
      href="/dokumenty/1"
      fileName="Odwołanie.pdf"
      status="multi"
      pages={3}
      codes={["BRAK_DANYCH"]}
    />
  ),
};
export const Foreign = {
  render: () => (
    <DocumentTile
      href="/dokumenty/1"
      fileName="Odwołanie.pdf"
      status="foreign"
      pages={3}
      codes={["BRAK_DANYCH"]}
    />
  ),
};
