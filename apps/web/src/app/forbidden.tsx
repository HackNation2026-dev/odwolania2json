import Link from "next/link";
import { TextPage } from "@/components/templates/TextPage";

export default function Forbidden() {
  return (
    <div className="py-20 text-center">
      <p aria-hidden className="mb-5 text-6xl font-semibold text-muted">
        403
      </p>
      <TextPage
        title="Brak dostępu"
        intro="Nie masz dostępu do tej strony. Poproś administratora o nadanie roli."
      >
        <Link
          href="/dokumenty"
          className="inline-flex min-h-11 items-center rounded-md bg-primary px-4 text-on-primary"
        >
          Wróć do spraw
        </Link>
      </TextPage>
    </div>
  );
}
