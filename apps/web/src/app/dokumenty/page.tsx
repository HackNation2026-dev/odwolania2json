import { Suspense } from "react";
import { DocumentsList } from "@/features/dokumenty-lista/DocumentsList";

export const metadata = { title: "Dodane dokumenty · Odwołania2JSON" };

export default function DocumentsPage() {
  return (
    <Suspense fallback={<p role="status">Ładowanie dokumentów…</p>}>
      <DocumentsList />
    </Suspense>
  );
}
