import { Stepper } from "./Stepper";

const meta = { title: "Molecules/Stepper" };
export default meta;
export const Default = {
  render: () => (
    <Stepper
      steps={[
        { id: "1", label: "Połączenie", status: "ok" },
        { id: "2", label: "Model", status: "running" },
        { id: "3", label: "OCR", status: "pending" },
        {
          id: "4",
          label: "Eksport",
          status: "error",
          description: "Brak odpowiedzi",
        },
      ]}
    />
  ),
};
