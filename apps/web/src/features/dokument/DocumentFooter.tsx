"use client";
import Link from "next/link";
import { Button } from "@/components/atoms/Button";
import type { useExportDecision } from "@/lib/api/hooks";
import s from "./dokument.module.css";
export function DocumentFooter({
  id,
  decision,
  activeTab,
  downloading,
  failed,
  downloadJson,
  downloadEvidence,
  message,
}: {
  id: string;
  decision: ReturnType<typeof useExportDecision>;
  activeTab: string;
  downloading: boolean;
  failed: boolean;
  downloadJson: () => void;
  downloadEvidence: () => void;
  message: string;
}) {
  return (
    <footer className={s.footer}>
      {activeTab !== "eksport" && (
        <div className={s.exportSummary}>
          {decision.data ? (
            <>
              <h2>
                {decision.data.allowed
                  ? "✓ Eksport dozwolony"
                  : "! Eksport zablokowany"}
              </h2>
              <Link href={`/dokumenty/${id}?tab=eksport`}>
                Wariant A ·{" "}
                {decision.data.allowed ? "szczegóły" : "zobacz powody"}
              </Link>
            </>
          ) : decision.isError ? (
            <p role="alert">
              Nie udało się sprawdzić eksportu.{" "}
              <Button
                variant="ghost"
                className="min-h-11"
                onClick={() => decision.refetch()}
              >
                Sprawdź ponownie
              </Button>
            </p>
          ) : (
            <p role="status">Sprawdzanie warunków eksportu…</p>
          )}
        </div>
      )}
      <div className={s.footerActions}>
        <Button
          className="min-h-11"
          disabled={!decision.data?.allowed || downloading}
          onClick={downloadJson}
        >
          Pobierz JSON
        </Button>
        <Button
          variant="secondary"
          className="min-h-11"
          onClick={downloadEvidence}
        >
          Pobierz dowody
        </Button>
        <span className="text-xs text-muted">Dowody zapisano osobno.</span>
      </div>
      {message && (
        <p role={failed ? "alert" : "status"} className="text-sm">
          {message}
        </p>
      )}
    </footer>
  );
}
