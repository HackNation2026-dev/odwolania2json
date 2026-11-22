import Link from "next/link";
import { Card } from "@/components/atoms/Card";
import { Badge } from "@/components/atoms/Badge";
import { TextPage } from "@/components/templates/TextPage";

export function AccessibilityView() {
  return (
    <TextPage
      title="Dostępność"
      intro="Projektujemy zgodnie z WCAG 2.1 AA. Stan zgodności zostanie opisany po audycie działającej aplikacji."
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Badge tone="neutral">Cel: WCAG 2.1 AA</Badge>
          <Badge tone="neutral">Nie przeprowadzono audytu</Badge>
        </div>
        <Card as="section" className="space-y-2">
          <h2 className="font-semibold">Stan sprawdzenia</h2>
          <p className="text-sm text-muted">Data i zakres testu</p>
          <p>Nie przeprowadzono audytu.</p>
        </Card>
        <Card as="section" className="space-y-2">
          <h2 className="font-semibold">Znane ograniczenia</h2>
          <ul className="list-inside list-disc space-y-2">
            <li>
              Obraz PDF może nie być dostępny dla czytnika ekranu. Użyj „Tekst
              strony”.
            </li>
            <li>OCR może zawierać błędy.</li>
          </ul>
        </Card>
        <Card as="section" className="space-y-2">
          <h2 className="font-semibold">Zgłoś problem</h2>
          <p className="text-sm text-muted">
            Kontakt zespołu pochodzi z konfiguracji.
          </p>
          <p>Kontakt nie został skonfigurowany.</p>
        </Card>
        <Link
          href="/dodaj"
          className="flex min-h-11 items-center justify-center rounded-md border border-control px-4"
        >
          Wróć do analizy
        </Link>
      </div>
    </TextPage>
  );
}
