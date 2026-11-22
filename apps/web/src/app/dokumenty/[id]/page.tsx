import { DocumentView } from "@/features/dokument/DocumentView";
export default async function DocumentPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ tab?: string }> }) {
  const { id } = await params;
  const { tab } = await searchParams;
  return <DocumentView key={id} id={id} tab={tab} />;
}
