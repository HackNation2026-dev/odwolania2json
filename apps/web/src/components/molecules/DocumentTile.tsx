import type { ReactNode, ComponentProps } from "react";
import { Icon, StatusBadge } from "@/components/atoms";
import { ProgressBar } from "./ProgressBar";
export type DocumentTileProps = {
  href: string;
  fileName: string;
  className?: string;
  status: ComponentProps<typeof StatusBadge>["status"];
  pages: number;
  date?: string;
  codes?: string[];
  progress?: number;
  thumbnail?: ReactNode;
};
export function DocumentTile({
  href,
  fileName,
  className,
  status,
  pages,
  date,
  codes = [],
  progress,
  thumbnail,
}: DocumentTileProps) {
  return (
    <article className="min-w-0 overflow-hidden rounded-lg border border-border bg-surface">
      <div
        aria-hidden="true"
        className="flex h-44 items-center justify-center bg-[var(--pdf-canvas)]"
      >
        {thumbnail ?? <Icon name="file" size={24} />}
      </div>
      <div className="space-y-2 p-3">
        <h2 className="break-all text-sm font-semibold">
          <a
            href={href}
            className="inline-flex min-h-11 items-center underline"
          >
            {fileName}
          </a>
        </h2>
        <p className="text-xs text-muted">{className ?? "Klasa nieustalona"}</p>
        <StatusBadge status={status} />
        <p className="text-xs text-muted">
          {pages} str.{date && ` · ${date}`}
        </p>
        {codes.length > 0 && (
          <p className="break-words text-xs text-muted">{codes.join(" · ")}</p>
        )}
        {progress !== undefined && (
          <ProgressBar label="Analiza" value={progress} />
        )}
      </div>
    </article>
  );
}
