"use client";

import { Banner } from "@/components/molecules/Banner";
import { useClassVersions } from "@/lib/api/hooks";

export const configurationError =
  "Błąd konfiguracji. Brak poprawnego zestawu klas. Analiza zablokowana.";

export function useClassConfiguration() {
  const query = useClassVersions();
  return {
    ...query,
    blocked:
      query.isPending ||
      query.isError ||
      !query.data?.some((version) => version.active),
    message: configurationError,
  };
}

export function ConfigurationError() {
  return (
    <Banner tone="error" title={configurationError}>
      <p>
        Brak poprzedniego kompletnego zestawu. Sprawdź konfigurację YAML poza
        GUI.
      </p>
      <p>
        Błąd konfiguracji jest błędem technicznym. Wynik zastępczy nie jest
        tworzony.
      </p>
    </Banner>
  );
}
