"use client";
import { Button } from "@/components/atoms/Button";
import { Banner, LoadingState } from "@/components/molecules";
import { OcrReadinessBanner } from "@/components/molecules/OcrReadinessBanner";
import { useSystemInfo } from "@/lib/api/hooks";
export function SystemReadiness() {
  const info = useSystemInfo();
  if (info.isPending) return <LoadingState label="Sprawdzanie gotowości OCR" />;
  if (info.isError)
    return (
      <Banner
        tone="error"
        actions={
          <Button variant="secondary" onClick={() => void info.refetch()}>
            Sprawdź ponownie
          </Button>
        }
      >
        Nie udało się pobrać gotowości OCR.
      </Banner>
    );
  return <OcrReadinessBanner {...info.data.ocr} />;
}
