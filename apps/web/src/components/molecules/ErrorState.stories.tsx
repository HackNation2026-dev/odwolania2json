import { ErrorState } from "./ErrorState";

const meta = { title: "Molecules/ErrorState" };
export default meta;
export const Default = {
  render: () => (
    <ErrorState description="Usługa jest niedostępna." onRetry={() => {}} />
  ),
};
export const WithoutRetry = {
  render: () => (
    <ErrorState
      title="Brak uprawnień"
      description="Poproś administratora o dostęp."
    />
  ),
};
