import { Badge, Button, Card } from "@/components/atoms";
import { Banner } from "@/components/molecules/Banner";
import { Dialog } from "@/components/organisms/Dialog";
import type { ClassSetVersion } from "@/lib/api/schemas";

type Props = {
  open: boolean;
  pending: boolean;
  error: boolean;
  activated: boolean;
  versions: ClassSetVersion[];
  onClose: () => void;
  onActivate: () => void;
};

export function ClassActivation({
  open,
  pending,
  error,
  activated,
  versions,
  onClose,
  onActivate,
}: Props) {
  const draft = versions.find((version) => version.version === "v2");
  return (
    <>
      {activated && (
        <section className="space-y-4">
          <Banner tone="success" title="Zestaw v2 aktywny" />
          <Card className="space-y-3">
            <h2 className="font-semibold">Klasy w zestawie v2 (3)</h2>
            <ul className="space-y-2">
              {draft?.classes.map((cls) => (
                <li
                  key={cls.id}
                  className="flex flex-wrap justify-between gap-2 rounded-md bg-subtle p-3"
                >
                  <span>{cls.id}</span>
                  <span>
                    wersja {cls.version} · {cls.fields} pól
                  </span>
                </li>
              ))}
            </ul>
          </Card>
          <Banner tone="info">
            Aktywacja nie przelicza zapisanych wyników. Trwające zadania
            zachowują zestaw v1, nowe używają v2.
          </Banner>
        </section>
      )}
      <Dialog
        open={open}
        onClose={() => {
          if (!pending) onClose();
        }}
        title={pending ? "Aktywowanie…" : "Aktywuj zestaw v2?"}
        description="Nowe analizy użyją tego zestawu. Trwające zadania i zapisane wyniki zachowają v1."
        actions={
          <>
            <Button
              touch
              variant="secondary"
              disabled={pending}
              onClick={onClose}
            >
              Anuluj
            </Button>
            <Button touch disabled={pending} onClick={onActivate}>
              {pending ? "Aktywowanie…" : error ? "Ponów" : "Aktywuj"}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {error && (
            <Banner
              tone="error"
              title="Nie aktywowano. Nadal aktywny v1. Ponów"
            />
          )}
          <h3 className="font-semibold">Lista zmian</h3>
          <ul className="list-inside list-disc text-sm">
            {draft?.changes.map((change) => (
              <li key={change}>{change}</li>
            ))}
          </ul>
          <p>Liczba klas w zestawie: {draft?.classes.length ?? 0}</p>
          <div className="flex flex-wrap gap-2">
            <Badge tone="full">✓ Walidacja: poprawna</Badge>
            <Badge tone="full">✓ Test mocka: zgodny</Badge>
          </div>
          {pending && (
            <p role="status" aria-live="polite">
              Zestaw v2 jest aktywowany. Nie zamykaj okna. Do potwierdzenia
              przez serwer aktywna pozostaje wersja v1.
            </p>
          )}
        </div>
      </Dialog>
    </>
  );
}
