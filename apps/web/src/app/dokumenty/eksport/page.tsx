import { BatchExportView } from "@/features/dokumenty-lista/BatchExportView";
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ partia?: string }>;
}) {
  const { partia } = await searchParams;
  return <BatchExportView batchId={partia ?? "B-01"} />;
}
