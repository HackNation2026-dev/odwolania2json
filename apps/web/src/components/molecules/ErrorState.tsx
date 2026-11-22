"use client";
import { Button } from "@/components/atoms";
import { Banner } from "./Banner";
export type ErrorStateProps = {
  title?: string;
  description?: string;
  onRetry?: () => void;
};
export function ErrorState({
  title = "Nie udało się wczytać danych",
  description,
  onRetry,
}: ErrorStateProps) {
  return (
    <Banner
      tone="error"
      title={title}
      actions={
        onRetry && (
          <Button variant="secondary" onClick={onRetry}>
            Spróbuj ponownie
          </Button>
        )
      }
    >
      {description && <p>{description}</p>}
    </Banner>
  );
}
