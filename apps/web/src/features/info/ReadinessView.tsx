"use client";

import { TextPage } from "@/components/templates/TextPage";
import { useReadiness } from "@/lib/api/hooks";
import { SystemInfoContent } from "./SystemInfoCard";

export function ReadinessView() {
  const info = useReadiness();
  return (
    <TextPage
      title="Gotowość i modele"
      intro="Stan usług używanych przez analizę oraz dane o modelach, licencjach i lokalizacji."
    >
      <SystemInfoContent info={info} />
    </TextPage>
  );
}
