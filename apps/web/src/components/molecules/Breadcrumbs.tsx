import { Icon } from "@/components/atoms";
export type Breadcrumb = { label: string; href?: string };
export function Breadcrumbs({ items }: { items: Breadcrumb[] }) {
  return (
    <nav aria-label="Ścieżka nawigacji">
      <ol className="flex flex-wrap items-center gap-2 text-sm text-muted">
        {items.map((item, i) => (
          <li
            key={`${item.label}-${i}`}
            className="flex min-w-0 items-center gap-2"
          >
            {i > 0 && <Icon name="chevron-right" />}
            {item.href && i < items.length - 1 ? (
              <a
                href={item.href}
                className="inline-flex min-h-11 items-center underline"
              >
                {item.label}
              </a>
            ) : (
              <span aria-current={i === items.length - 1 ? "page" : undefined}>
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
