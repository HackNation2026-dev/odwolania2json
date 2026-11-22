"use client";
import { Button } from "@/components/atoms";
export function LoadMore({
  onLoad,
  loading = false,
  hasMore = true,
  shown,
  total,
}: {
  onLoad: () => void;
  loading?: boolean;
  hasMore?: boolean;
  shown: number;
  total: number;
}) {
  return (
    <div className="space-y-2 py-4 text-center">
      <p role="status" className="text-sm text-muted">
        Pokazano {shown} z {total}
      </p>
      {hasMore && (
        <Button variant="secondary" loading={loading} onClick={onLoad}>
          Pokaż więcej
        </Button>
      )}
    </div>
  );
}
