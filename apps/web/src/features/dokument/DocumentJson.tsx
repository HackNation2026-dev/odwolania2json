"use client";
import { JsonViewer } from "@/components/organisms/JsonViewer";
export function DocumentJson({
  json,
  blocked,
}: {
  json: string | null;
  blocked: boolean;
}) {
  return <JsonViewer json={json} blocked={blocked} />;
}
