"use client";

import { useRef, useState } from "react";
import { Button, Card } from "@/components/atoms";
import {
  Banner,
  CodeBlock,
  EmptyState,
  ErrorState,
  LoadingState,
  Tab,
  TabList,
  TabPanel,
  Tabs,
} from "@/components/molecules";
import { PageHeader } from "@/components/organisms/PageHeader";
import { AppPage } from "@/components/templates/AppPage";
import { TwoPane } from "@/components/templates/TwoPane";
import {
  useActivateClassSet,
  useClassDetail,
  useClassVersions,
  useClassYaml,
  useTestClassDraft,
} from "@/lib/api/hooks";
import { ClassActivation } from "./ClassActivation";
import { ClassFormPreview } from "./ClassFormPreview";
import { ConfigurationError } from "./ConfigurationGuard";
import { ClassDraftEditor } from "./ClassDraftEditor";
import { ConfigurationFieldList } from "@/components/molecules/ConfigurationFieldList";

export function ClassDetailView({
  id,
  initialTab = "fields",
}: {
  id: string;
  initialTab?: string;
}) {
  const detail = useClassDetail(id);
  const yaml = useClassYaml(id);
  const versions = useClassVersions();
  const test = useTestClassDraft();
  const activation = useActivateClassSet();
  const [tab, setTab] = useState(initialTab);
  const [draft, setDraft] = useState<string | null>(null);
  const [dialog, setDialog] = useState(false);
  const lock = useRef(false);
  const code = draft ?? yaml.data?.draft ?? "";
  const testedCurrent = test.isSuccess && test.variables?.yaml === code;
  const canActivate = testedCurrent && test.data.valid && !activation.isPending;

  async function activate() {
    if (lock.current || !canActivate) return;
    lock.current = true;
    try {
      await activation.mutateAsync("v2");
      setDialog(false);
    } catch {
      // Dialog zachowuje błąd i pozwala ponowić tę samą operację.
    } finally {
      lock.current = false;
    }
  }

  if (detail.isPending || yaml.isPending || versions.isPending)
    return <LoadingState label="Wczytywanie klasy…" />;
  if (detail.isError || yaml.isError || versions.isError) {
    return (
      <ErrorState
        title="Nie udało się wczytać klasy"
        onRetry={() => {
          void detail.refetch();
          void yaml.refetch();
          void versions.refetch();
        }}
      />
    );
  }
  if (!versions.data.some((version) => version.active))
    return <ConfigurationError />;
  if (!detail.data)
    return (
      <EmptyState
        title="Nie znaleziono klasy"
        description="Wróć do listy klas i wybierz aktywną konfigurację."
      />
    );
  const cls = detail.data;
  const hasDraft = yaml.data.draft !== null && !activation.isSuccess;
  const preview = <ClassFormPreview definition={cls} />;
  const testPanel = (
    <Card className="space-y-4">
      <h2 className="text-lg font-semibold">Test na pliku</h2>
      <p className="text-sm text-muted">
        Demonstracja E2 · syntetyczny przelew-demo.pdf. Test mocka bez analizy
        PDF.
      </p>
      {(!testedCurrent || !test.data?.valid) && (
        <Banner
          tone="warning"
          title="Wynik poprzedniego testu jest nieaktualny"
        >
          Poprzedni wynik · wersja 1 · tylko odczyt. Kwota: 200.00;
          data_operacji: 2026-10-12. Zapisany wynik dotyczy wersji 1.
        </Banner>
      )}
      {test.isError && (
        <Banner tone="error" title="Nie udało się uruchomić testu. Ponów." />
      )}
      {testedCurrent &&
        test.data.issues.map((issue) => (
          <Banner key={issue} tone="error" title={issue} />
        ))}
      {testedCurrent && test.data.valid && (
        <Banner tone="success" title="Walidacja: poprawna">
          {test.data.summary}
        </Banner>
      )}
      <div className="flex flex-wrap gap-2">
        <Button
          disabled={!hasDraft || test.isPending || activation.isPending}
          onClick={() => test.mutate({ id, yaml: code })}
        >
          {test.isPending ? "Testowanie…" : "Testuj wersję roboczą"}
        </Button>
        <Button
          variant="secondary"
          disabled={!hasDraft || !canActivate}
          onClick={() => setDialog(true)}
        >
          Aktywuj zestaw
        </Button>
      </div>
      {test.isPending && <p role="status">Testowanie konfiguracji…</p>}
      <Banner tone="info">
        Nowa reguła (np. inny słownik) wymaga funkcji w rejestrze silnika.
        Edycja klas w GUI jest demonstracją.
      </Banner>
    </Card>
  );

  return (
    <AppPage
      header={
        <PageHeader
          title={cls.name}
          breadcrumbs={[
            { label: "Klasy dokumentów", href: "/klasy" },
            { label: cls.name },
          ]}
          subtitle={`${cls.id} · zestaw ${versions.data.find((version) => version.active)?.version} · konfiguracja demonstracyjna`}
        />
      }
    >
      <div className="space-y-4 [&_button]:min-h-11">
        <ClassActivation
          open={dialog}
          pending={activation.isPending}
          error={activation.isError}
          activated={activation.isSuccess}
          versions={versions.data}
          onClose={() => setDialog(false)}
          onActivate={() => void activate()}
        />
        <Tabs value={tab} onValueChange={setTab}>
          <TabList aria-label="Szczegóły klasy">
            <Tab value="fields">Pola</Tab>
            <Tab value="yaml">YAML</Tab>
            <Tab value="preview">Podgląd formularza</Tab>
            <Tab value="test">Test</Tab>
          </TabList>
          <TabPanel value="fields">
            <Card className="space-y-3">
              <h2 className="text-lg font-semibold">Pola i reguły kontraktu</h2>
              <ConfigurationFieldList
                fields={[...cls.containers, ...cls.fields]}
              />
            </Card>
          </TabPanel>
          <TabPanel value="yaml">
            <TwoPane
              ratio="60/40"
              mobileTabs={["Kod YAML", "Formularz"]}
              left={
                <Card className="space-y-4">
                  <h2 className="font-semibold">{id}.yaml · odczyt</h2>
                  <a
                    className="inline-flex min-h-11 items-center underline"
                    href={`data:text/yaml;charset=utf-8,${encodeURIComponent(yaml.data.active)}`}
                    download={`${id}.yaml`}
                  >
                    Pobierz {id}.yaml
                  </a>
                  <CodeBlock
                    code={yaml.data.active}
                    copyLabel="Kopiuj"
                    label={`${id}.yaml`}
                  />
                </Card>
              }
              right={preview}
            />
          </TabPanel>
          <TabPanel value="preview">{preview}</TabPanel>
          <TabPanel value="test">
            {hasDraft ? (
              <TwoPane
                ratio="60/40"
                mobileTabs={["Wersja robocza", "Wynik testu"]}
                left={
                  <ClassDraftEditor
                    id={id}
                    code={code}
                    busy={activation.isPending || test.isPending}
                    valid={Boolean(canActivate)}
                    onChange={setDraft}
                    onSave={() => setDialog(true)}
                  />
                }
                right={testPanel}
              />
            ) : (
              <EmptyState
                title="Brak wersji roboczej"
                description={
                  activation.isSuccess
                    ? "Wersja 2 została aktywowana. Aktywny YAML i formularz są dostępne w zakładkach."
                    : "Demonstracja zmiany → test → aktywacja jest dostępna dla klasy przelew."
                }
              />
            )}
          </TabPanel>
        </Tabs>
      </div>
    </AppPage>
  );
}
