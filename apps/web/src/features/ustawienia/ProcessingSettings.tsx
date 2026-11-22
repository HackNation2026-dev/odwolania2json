"use client";
import { Card } from "@/components/atoms/Card";
import { KeyValueList } from "@/components/molecules/KeyValueList";
import { LoadingState } from "@/components/molecules/LoadingState";
import { ErrorState } from "@/components/molecules/ErrorState";
import { EmptyState } from "@/components/molecules/EmptyState";
import { useSystemInfo } from "@/lib/api/hooks";

export function ProcessingSettings() {
  const info = useSystemInfo();
  return (
    <Card as="section" padding="lg" className="space-y-4 rounded-md">
      <h2 className="text-xl font-semibold">
        Przetwarzanie{" "}
        <span className="text-sm font-normal text-muted">tylko odczyt</span>
      </h2>
      {info.isPending ? (
        <LoadingState label="Wczytywanie modelu…" />
      ) : info.isError ? (
        <ErrorState
          description="Nie udało się wczytać modelu."
          onRetry={() => void info.refetch()}
        />
      ) : !info.data.models.length ? (
        <EmptyState title="Brak skonfigurowanych modeli." />
      ) : (
        info.data.models.map((model) => (
          <KeyValueList
            key={model.id}
            items={[
              { key: "model", label: "Model językowy", value: model.name },
              { key: "license", label: "Licencja", value: model.license },
              {
                key: "provider",
                label: "Dostawca API i region",
                value: `${model.provider ?? "Nie podano"} · ${model.region ?? "Nie potwierdzono"}`,
              },
            ]}
          />
        ))
      )}
    </Card>
  );
}
