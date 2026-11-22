import { Banner } from "./Banner";
export type OcrReadinessBannerProps = {
  mode: "target" | "shim" | "unavailable";
  name: string;
  version: string | null;
  detail: string;
};
export function OcrReadinessBanner({
  mode,
  name,
  version,
  detail,
}: OcrReadinessBannerProps) {
  if (mode === "target") return null;
  return (
    <Banner
      tone={mode === "unavailable" ? "error" : "warning"}
      title={
        mode === "unavailable"
          ? "OCR niedostępny"
          : `OCR tymczasowy (shim): ${name}${version ? `, ${version}` : ""}`
      }
    >
      <p className="text-sm">
        {mode === "unavailable"
          ? "Strony wymagające OCR pozostaną nieprzetworzone. Dokument nie zostanie uznany za obcy z powodu braku OCR."
          : "Skany i dokumenty mieszane przetwarza zamiennik. Docelowy własny model OCR nie jest podłączony."}
      </p>
      <p className="mt-2 text-sm">{detail}</p>
    </Banner>
  );
}
