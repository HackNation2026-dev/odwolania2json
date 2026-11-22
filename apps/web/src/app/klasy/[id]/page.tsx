import { ClassDetailView } from "@/features/klasy/ClassDetailView";

export default async function ClassPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ClassDetailView key={id} id={id} />;
}
