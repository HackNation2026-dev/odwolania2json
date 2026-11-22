"use client";
import { useState } from "react";
import { Button, Select } from "@/components/atoms";
import {
  Banner,
  EmptyState,
  ErrorState,
  KeyValueList,
  LoadingState,
  Tab,
  TabList,
  TabPanel,
  Tabs,
} from "@/components/molecules";
import { Drawer } from "@/components/organisms";
import { useDiagnosis } from "@/lib/api/hooks";
import type { DiagnosisPart } from "@/lib/api/processing";
import s from "./dokument.module.css";

function DiagnosisDetails({ part }: { part: DiagnosisPart }) {
  const sources = {
    pdf: "tekst cyfrowy",
    ocr: "OCR",
    mixed: "tekst PDF i OCR",
    none: "brak odczytu",
    unknown: "nierozpoznane",
  };
  return (
    <div className="space-y-3">
      <KeyValueList
        items={[
          {
            key: "source",
            label: "Źródło tekstu",
            value: sources[part.text_source],
          },
          {
            key: "type",
            label: "Typ strony",
            value: "Nie przekazano typu strony",
          },
          { key: "quality", label: "Jakość odczytu", value: "Nie oceniono" },
          {
            key: "rotation",
            label: "Orientacja",
            value:
              part.rotation_degrees === null
                ? "Nie oceniono"
                : `${part.rotation_degrees}°`,
          },
          {
            key: "coverage",
            label: "Pokrycie",
            value:
              part.coverage === null
                ? "Nie oceniono"
                : `${Math.round(part.coverage * 100)}%`,
          },
          {
            key: "confidence",
            label: "Pewność diagnozy",
            value:
              part.confidence === null
                ? "Nie oceniono"
                : `${Math.round(part.confidence * 100)}%`,
          },
          {
            key: "ocr",
            label: "Decyzja OCR",
            value:
              part.requires_ocr === null
                ? "Nie ustalono"
                : part.requires_ocr
                  ? "OCR wymagany"
                  : "OCR niewymagany",
          },
          { key: "method", label: "Metoda", value: part.method },
        ]}
      />
      <h3 className="font-semibold">Sygnały decyzji</h3>
      {part.signals.length ? (
        <ul className="list-disc pl-5">
          {part.signals.map((signal) => (
            <li key={signal.code}>
              {signal.description} · <code>{signal.code}</code>:{" "}
              {String(signal.value)}
            </li>
          ))}
        </ul>
      ) : (
        <p>Silnik nie przekazał uzasadnienia.</p>
      )}
      <h3 className="font-semibold">Kody odstępstw</h3>
      <p>{part.codes.join(", ") || "Brak kodów odstępstw."}</p>
    </div>
  );
}

export function DocumentDiagnosis({
  id,
  className,
}: {
  id: string;
  className: string | null;
}) {
  const query = useDiagnosis(id);
  const [message, setMessage] = useState("");
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [region, setRegion] = useState("");
  const pageData = query.data?.pages.find((item) => item.number === page);
  const regionData = pageData?.regions?.find((item) => item.id === region);
  return (
    <>
      <Button variant="ghost" onClick={() => setOpen(true)}>
        Diagnoza dokumentu, stron i regionów
      </Button>
      <Drawer
        open={open}
        onClose={() => setOpen(false)}
        title="Diagnoza"
        actions={
          <>
            <Button
              variant="secondary"
              disabled={!query.data}
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(
                    JSON.stringify(query.data, null, 2),
                  );
                  setMessage("Skopiowano szczegóły.");
                } catch {
                  setMessage("Nie udało się skopiować szczegółów.");
                }
              }}
            >
              Kopiuj szczegóły
            </Button>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Zamknij diagnozę
            </Button>
          </>
        }
        description="Pewność diagnozy jest oddzielna od pewności klasy, wartości i dowodu."
      >
        <div className={s.diagnosis}>
          <p className="mb-3 text-sm">
            Klasa biznesowa: {className ?? "Nieustalona"}
          </p>
          {query.isPending ? (
            <LoadingState label="Wczytywanie diagnozy…" />
          ) : query.isError ? (
            <ErrorState
              title="Nie udało się odczytać diagnozy"
              onRetry={() => query.refetch()}
            />
          ) : (
            <Tabs defaultValue="dokument">
              <TabList aria-label="Poziom diagnozy">
                <Tab value="dokument">Dokument</Tab>
                <Tab value="strona">Strona</Tab>
                <Tab value="region">Region</Tab>
              </TabList>
              <TabPanel value="dokument">
                <DiagnosisDetails part={query.data} />
              </TabPanel>
              <TabPanel value="strona">
                <label className="block">
                  Strona
                  <Select
                    value={page}
                    onChange={(event) => {
                      setPage(Number(event.target.value));
                      setRegion("");
                    }}
                  >
                    {query.data.pages.map((item) => (
                      <option key={item.number} value={item.number}>
                        {item.number}
                      </option>
                    ))}
                  </Select>
                </label>
                {pageData ? (
                  <DiagnosisDetails part={pageData} />
                ) : (
                  <EmptyState title="Brak diagnozy stron." />
                )}
              </TabPanel>
              <TabPanel value="region">
                <label className="block">
                  Strona regionu
                  <Select
                    value={page}
                    onChange={(event) => {
                      setPage(Number(event.target.value));
                      setRegion("");
                    }}
                  >
                    {query.data.pages.map((item) => (
                      <option key={item.number} value={item.number}>
                        {item.number}
                      </option>
                    ))}
                  </Select>
                </label>
                <label className="block">
                  Region
                  <Select
                    value={region}
                    onChange={(event) => setRegion(event.target.value)}
                  >
                    <option value="">Wybierz region</option>
                    {pageData?.regions?.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.id}
                      </option>
                    ))}
                  </Select>
                </label>
                {regionData ? (
                  <DiagnosisDetails part={regionData} />
                ) : (
                  <EmptyState title="Brak diagnozy dla tego regionu" />
                )}
              </TabPanel>
            </Tabs>
          )}
          <Banner tone="neutral">
            Brak skalibrowanej miary oznaczamy „Nie oceniono”.
          </Banner>
        </div>
      </Drawer>
    </>
  );
}
