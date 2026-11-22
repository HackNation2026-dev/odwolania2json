import { Disclosure } from "./Disclosure";

const meta = { title: "Molecules/Disclosure" };
export default meta;
export const Default = {
  render: () => (
    <Disclosure title="Szczegóły">Dodatkowe informacje.</Disclosure>
  ),
};
export const Open = {
  render: () => (
    <Disclosure title="Szczegóły" open>
      Dodatkowe informacje.
    </Disclosure>
  ),
};
