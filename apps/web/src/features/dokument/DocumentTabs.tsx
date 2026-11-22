import Link from "next/link";
import s from "./dokument.module.css";

export function DocumentTabs({
  id,
  activeTab,
}: {
  id: string;
  activeTab: string;
}) {
  return (
    <>
      <nav aria-label="Widoki dokumentu" className={s.tabs}>
        <Link
          className={s.mobileDoc}
          href={`/dokumenty/${id}?tab=dokument`}
          aria-current={activeTab === "dokument" ? "page" : undefined}
        >
          Dokument
        </Link>
        <Link
          href={`/dokumenty/${id}?tab=przeglad`}
          aria-current={activeTab === "przeglad" ? "page" : undefined}
        >
          <span className={s.desktopLabel}>Przegląd</span>
          <span className={s.tabletLabel}>Formularz</span>
          <span className={s.phoneLabel}>Dane</span>
        </Link>
        <Link
          href={`/dokumenty/${id}?tab=json`}
          aria-current={activeTab === "json" ? "page" : undefined}
        >
          JSON
        </Link>
        {[
          ["dowody", "Dowody"],
          ["eksport", "Eksport"],
        ].map(([key, label]) => (
          <Link
            className={s.secondaryTab}
            key={key}
            href={`/dokumenty/${id}?tab=${key}`}
            aria-current={activeTab === key ? "page" : undefined}
          >
            {label}
          </Link>
        ))}
      </nav>
      <details className={s.phoneMore}>
        <summary>Więcej widoków</summary>
        <nav
          aria-label="Pozostałe widoki dokumentu"
          className="flex flex-wrap gap-3 px-3"
        >
          <Link
            className="inline-flex min-h-11 items-center underline"
            href={`/dokumenty/${id}?tab=dowody`}
          >
            Dowody
          </Link>
          <Link
            className="inline-flex min-h-11 items-center underline"
            href={`/dokumenty/${id}?tab=eksport`}
          >
            Eksport · wariant A
          </Link>
        </nav>
      </details>
    </>
  );
}
